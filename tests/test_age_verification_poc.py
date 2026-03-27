import hashlib
import secrets
import unittest
from unittest.mock import patch

from age_verification_poc import (
    ParaKluczyRSA,
    RzadA_WeryfikatorWieku,
    RzadB_WydawcaKodow,
    Uzytkownik,
)


class AgeVerificationPOCTests(unittest.TestCase):
    def test_happy_path_and_single_use_code(self):
        gov_a = RzadA_WeryfikatorWieku()
        gov_b = RzadB_WydawcaKodow()
        user = Uzytkownik(pesel="95030112345", imie="Jan Kowalski")

        result_a = user.popros_o_slepy_podpis(gov_a)
        self.assertTrue(result_a["sukces"])

        result_b = user.pobierz_anonimowy_kod(gov_b)
        self.assertTrue(result_b["sukces"])
        self.assertRegex(result_b["kod"], r"^\d{6}$")

        first_check = gov_b.zweryfikuj_kod(result_b["kod"])
        self.assertTrue(first_check["wazny"])

        second_check = gov_b.zweryfikuj_kod(result_b["kod"])
        self.assertFalse(second_check["wazny"])
        self.assertEqual(second_check["powod"], "Kod już wykorzystany")

    def test_minor_is_rejected_by_gov_a(self):
        gov_a = RzadA_WeryfikatorWieku()
        minor = Uzytkownik(pesel="10250154321", imie="Maly Jas")

        result = minor.popros_o_slepy_podpis(gov_a)

        self.assertFalse(result["sukces"])
        self.assertEqual(result["powod"], "Osoba niepełnoletnia")

    def test_tampered_signature_is_rejected_by_gov_b(self):
        gov_a = RzadA_WeryfikatorWieku()
        gov_b = RzadB_WydawcaKodow()
        user = Uzytkownik(pesel="95030112345", imie="Jan Kowalski")

        result_a = user.popros_o_slepy_podpis(gov_a)
        self.assertTrue(result_a["sukces"])

        blinded_oprf, _, _ = gov_b.oprf.klient_zaslep(b"unit-test")

        result = gov_b.przetworz_oprf_i_wydaj_kod(
            zaslepione_dane_oprf=blinded_oprf,
            hash_tokenu=user.hash_tokenu,
            podpis_tokenu=(user.podpis_tokenu + 1) % gov_a.rsa.n,
            klucz_rzadu_a_e=gov_a.rsa.e,
            klucz_rzadu_a_n=gov_a.rsa.n,
        )

        self.assertFalse(result["sukces"])
        self.assertEqual(result["powod"], "Nieważny podpis weryfikacji wieku")

    def test_code_expires_after_ttl(self):
        gov_a = RzadA_WeryfikatorWieku()
        gov_b = RzadB_WydawcaKodow()
        user = Uzytkownik(pesel="95030112345", imie="Jan Kowalski")

        self.assertTrue(user.popros_o_slepy_podpis(gov_a)["sukces"])
        issued = user.pobierz_anonimowy_kod(gov_b)
        self.assertTrue(issued["sukces"])

        code = issued["kod"]
        expires_at = gov_b.aktywne_kody[code]["wygasa"]

        with patch("age_verification_poc.time.time", return_value=expires_at + 1):
            check = gov_b.zweryfikuj_kod(code)

        self.assertFalse(check["wazny"])
        self.assertEqual(check["powod"], "Kod wygasł")
        self.assertNotIn(code, gov_b.aktywne_kody)

    def test_public_key_spoofing_bypass_current_behavior(self):
        # This test documents an existing weakness: Gov B accepts the pubkey
        # provided by the client instead of a pinned Gov A key.
        gov_b = RzadB_WydawcaKodow()

        attacker_keypair = ParaKluczyRSA(bity=512)
        attacker_token = secrets.randbelow(attacker_keypair.n - 2) + 2
        attacker_token_hash = int.from_bytes(
            hashlib.sha256(str(attacker_token).encode()).digest(), "big"
        ) % attacker_keypair.n
        attacker_signature = pow(
            attacker_token_hash, attacker_keypair.d, attacker_keypair.n
        )

        blinded_oprf, _, _ = gov_b.oprf.klient_zaslep(b"attacker-flow")
        result = gov_b.przetworz_oprf_i_wydaj_kod(
            zaslepione_dane_oprf=blinded_oprf,
            hash_tokenu=attacker_token_hash,
            podpis_tokenu=attacker_signature,
            klucz_rzadu_a_e=attacker_keypair.e,
            klucz_rzadu_a_n=attacker_keypair.n,
        )

        self.assertTrue(result["sukces"])


if __name__ == "__main__":
    unittest.main()

