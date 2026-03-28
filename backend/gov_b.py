"""
Router Rządu B — NASK (wydawca kodów).

Endpointy:
  GET  /gov-b/oprf-params   — publiczne parametry OPRF
  POST /gov-b/oprf-eval     — serwer oblicza OPRF na zaślepionych danych
  POST /gov-b/issue-code    — weryfikuje podpis Gov A i wystawia kod 6-cyfrowy
  POST /gov-b/verify-code   — weryfikuje kod (dla Strony 18+) i spala
"""
import hashlib
import secrets
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .crypto_core import SlepyRSA
from .state import gov_b_oprf, active_codes, audit_log_b


router = APIRouter(prefix="/gov-b", tags=["Gov B — NASK"])

CODE_TTL_SECONDS = 300  # 5 minut


# ── Modele ──────────────────────────────────────────────────────────

class OprfParamsResponse(BaseModel):
    p: str   # modulus jako hex
    g: str   # generator jako hex


class OprfEvalRequest(BaseModel):
    blinded_hex: str   # zaślepiony element grupy (H(x)^r mod p)


class OprfEvalResponse(BaseModel):
    result_hex: str    # zaślepiony wynik (H(x)^(r*k) mod p)


class IssueCodeRequest(BaseModel):
    token_hash_hex: str    # hash oryginalnego tokenu klienta
    signature_hex: str     # odślepiony podpis Gov A
    gov_a_e_hex: str       # klucz publiczny Gov A (e)
    gov_a_n_hex: str       # klucz publiczny Gov A (n)
    blinded_oprf_hex: str  # zaślepiony wkład do OPRF


class IssueCodeResponse(BaseModel):
    code: str
    expires_in: int   # sekundy


class VerifyCodeRequest(BaseModel):
    code: str


class VerifyCodeResponse(BaseModel):
    valid: bool
    reason: str | None = None


# ── Endpointy ────────────────────────────────────────────────────────

@router.get("/oprf-params", response_model=OprfParamsResponse)
def get_oprf_params():
    """Publiczne parametry grupy dla OPRF — klient używa ich do zaślepiania."""
    return OprfParamsResponse(
        p=hex(gov_b_oprf.p),
        g=hex(gov_b_oprf.g),
    )


@router.post("/oprf-eval", response_model=OprfEvalResponse)
def oprf_eval(req: OprfEvalRequest):
    """Serwer przetwarza zaślepione dane swoim kluczem k.

    Rząd B NIE WIE co przetwarza — widzi losowy element grupy.
    Klient musi potem samodzielnie odślepić wynik.
    """
    try:
        blinded = int(req.blinded_hex, 16)
    except ValueError:
        raise HTTPException(status_code=422, detail="Nieprawidłowy format blinded_hex")

    result = gov_b_oprf.serwer_oblicz(blinded)
    return OprfEvalResponse(result_hex=hex(result))


@router.post("/issue-code", response_model=IssueCodeResponse)
def issue_code(req: IssueCodeRequest):
    """Weryfikuje podpis Gov A i wystawia 6-cyfrowy jednorazowy kod.

    Rząd B:
      - WIDZI:    anonimowy token + podpis Gov A + zaślepione dane OPRF
      - NIE WIDZI: tożsamości użytkownika (ślepy podpis uniemożliwia powiązanie)
    """
    # 1. Parsowanie
    try:
        token_hash = int(req.token_hash_hex, 16)
        signature = int(req.signature_hex, 16)
        e = int(req.gov_a_e_hex, 16)
        n = int(req.gov_a_n_hex, 16)
    except ValueError:
        raise HTTPException(status_code=422, detail="Nieprawidłowy format hex")

    # 2. Weryfikacja podpisu Gov A
    # W produkcji: n byłby pinned (nie przyjmowany od klienta)
    if not SlepyRSA.zweryfikuj(token_hash, signature, e, n):
        raise HTTPException(
            status_code=403,
            detail="Nieważny podpis weryfikacji wieku"
        )

    # 3. Walidacja OPRF (parsowanie — serwer przetworzy zaślepione dane)
    try:
        blinded_oprf = int(req.blinded_oprf_hex, 16)
    except ValueError:
        raise HTTPException(status_code=422, detail="Nieprawidłowy format blinded_oprf_hex")

    # Weryfikujemy że blinded_oprf jest poprawnym elementem grupy
    if blinded_oprf <= 1 or blinded_oprf >= gov_b_oprf.p:
        raise HTTPException(status_code=422, detail="OPRF: element poza grupą")

    # 4. Generowanie kodu
    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = time.time() + CODE_TTL_SECONDS

    # Zapisujemy kod z odciskiem tokenu (NIE z tożsamością)
    active_codes[code] = {
        "odcisk_tokenu": hashlib.sha256(req.token_hash_hex.encode()).hexdigest()[:16],
        "wygasa": expires_at,
        "uzyty": False,
    }

    # Dziennik: wiemy ŻE wydano kod, NIE WIEMY KOMU
    audit_log_b.append({
        "czas": time.time(),
        "akcja": "wydano_kod",
        "hash_kodu": hashlib.sha256(code.encode()).hexdigest()[:16],
        "tozsamosc": "NIEZNANA — ślepy podpis uniemożliwia identyfikację",
    })

    return IssueCodeResponse(code=code, expires_in=CODE_TTL_SECONDS)


@router.post("/verify-code", response_model=VerifyCodeResponse)
def verify_code(req: VerifyCodeRequest):
    """Weryfikuje kod dla Strony 18+. Kod jest jednorazowy — po użyciu spalony.

    Strona 18+:
      - WIDZI:    odpowiedź TAK/NIE
      - NIE WIDZI: tożsamości, PESELu, tokenu, czegokolwiek
    """
    code = req.code.strip()

    if code not in active_codes:
        return VerifyCodeResponse(valid=False, reason="Kod nie istnieje")

    entry = active_codes[code]

    if entry["uzyty"]:
        return VerifyCodeResponse(valid=False, reason="Kod już wykorzystany")

    if time.time() > entry["wygasa"]:
        del active_codes[code]
        return VerifyCodeResponse(valid=False, reason="Kod wygasł")

    # Palenie kodu po jednorazowym użyciu
    entry["uzyty"] = True

    return VerifyCodeResponse(valid=True)
