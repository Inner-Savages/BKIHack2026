"""
Router Rządu A — mObywatel (weryfikator wieku).

Endpointy:
  GET  /gov-a/public-key  — klucz publiczny RSA do zaślepiania tokenów przez klienta
  POST /gov-a/sign        — weryfikuje PESEL i ślepo podpisuje zaślepiony token
"""
import hashlib
import time
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from .crypto_core import ParaKluczyRSA, SlepyRSA
from .state import gov_a_rsa, audit_log_a


router = APIRouter(prefix="/gov-a", tags=["Gov A — mObywatel"])


# ── Modele ──────────────────────────────────────────────────────────

class SignRequest(BaseModel):
    pesel: str
    blinded_token_hex: str     # zaslepiony token jako hex string


class PublicKeyResponse(BaseModel):
    e: str                     # e jako hex
    n: str                     # n jako hex


class SignResponse(BaseModel):
    blind_signature_hex: str   # ślepy podpis jako hex


# ── Endpointy ────────────────────────────────────────────────────────

@router.get("/public-key", response_model=PublicKeyResponse)
def get_public_key():
    """Zwraca klucz publiczny RSA Rządu A.

    Klient używa go do zaślepienia tokenu przed wysłaniem do podpisu:
      zaslepiony = hash(token) × r^e mod n
    """
    return PublicKeyResponse(
        e=hex(gov_a_rsa.e),
        n=hex(gov_a_rsa.n),
    )


@router.post("/sign", response_model=SignResponse)
def blind_sign(req: SignRequest):
    """Weryfikuje wiek z PESEL i ślepo podpisuje zaślepiony token.

    Rząd A:
      - WIDZI:    PESEL + zaślepiony token (losowy szum)
      - NIE WIDZI: oryginalnego tokenu (niemożliwe matematycznie)
    """
    # 1. Weryfikacja wieku z PESEL
    pesel = req.pesel.strip()
    if len(pesel) != 11 or not pesel.isdigit():
        raise HTTPException(status_code=422, detail="Nieprawidłowy format PESEL")

    rok = int(pesel[:2])
    miesiac = int(pesel[2:4])
    if miesiac > 20:
        rok += 2000
        miesiac -= 20
    else:
        rok += 1900

    wiek = 2026 - rok
    if wiek < 18:
        raise HTTPException(status_code=403, detail="Osoba niepełnoletnia")

    # 2. Parsowanie zaślepionego tokenu
    try:
        blinded = int(req.blinded_token_hex, 16)
    except ValueError:
        raise HTTPException(status_code=422, detail="Nieprawidłowy format blinded_token_hex")

    if blinded <= 0 or blinded >= gov_a_rsa.n:
        raise HTTPException(status_code=422, detail="Zaślepiony token poza zakresem")

    # 3. Ślepy podpis — Rząd A NIE WIE co podpisuje
    blind_sig = SlepyRSA.podpisz_slepo(blinded, gov_a_rsa.d, gov_a_rsa.n)

    # 4. Dziennik audytu — logujemy KTO prosił, ale NIE oryginalny token
    audit_log_a.append({
        "czas": time.time(),
        "hash_pesel": hashlib.sha256(pesel.encode()).hexdigest()[:16],
        "akcja": "slepy_podpis",
        "widziany_zaslepiony": req.blinded_token_hex[:20] + "...",
        # ↑ Losowy szum — nie da się z niego odtworzyć tokenu
    })

    return SignResponse(blind_signature_hex=hex(blind_sig))
