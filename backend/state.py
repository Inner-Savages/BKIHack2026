"""
Globalny stan serwera — instancje kluczy kryptograficznych i dzienniki.

Klucze RSA (Gov A) i parametry OPRF (Gov B) generowane są raz przy starcie.
W produkcji: persystowane w HSM lub szyfrowanym storage.
"""
import sys

from .crypto_core import NieswiadomaFunkcjaPRF, ParaKluczyRSA

print("[Backend] Generuję klucze RSA dla Gov A (512 bit)...", file=sys.stderr)
gov_a_rsa = ParaKluczyRSA(bity=512)
print(f"[Backend] Klucze RSA gotowe. n={hex(gov_a_rsa.n)[:24]}...", file=sys.stderr)

print("[Backend] Inicjalizuję parametry OPRF dla Gov B (256 bit)...", file=sys.stderr)
gov_b_oprf = NieswiadomaFunkcjaPRF(bity=256)
print(f"[Backend] OPRF gotowe. p={hex(gov_b_oprf.p)[:24]}...", file=sys.stderr)

# Aktywne kody: {kod: {odcisk_tokenu, wygasa, uzyty}}
active_codes: dict = {}

# Dzienniki audytu
audit_log_a: list = []
audit_log_b: list = []
