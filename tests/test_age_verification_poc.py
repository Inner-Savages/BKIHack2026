import hashlib
import secrets
import unittest
from unittest.mock import patch

from age_verification_poc import GovA_AgeVerifier, GovB_CodeIssuer, RSAKeyPair, User


class AgeVerificationPOCTests(unittest.TestCase):
    def test_happy_path_and_single_use_code(self):
        gov_a = GovA_AgeVerifier()
        gov_b = GovB_CodeIssuer()
        user = User(pesel="95030112345", name="Jan Kowalski")

        result_a = user.request_blind_signature(gov_a)
        self.assertTrue(result_a["success"])

        result_b = user.get_anonymous_code(gov_b)
        self.assertTrue(result_b["success"])
        self.assertRegex(result_b["code"], r"^\d{6}$")

        first_check = gov_b.verify_code(result_b["code"])
        self.assertTrue(first_check["valid"])

        second_check = gov_b.verify_code(result_b["code"])
        self.assertFalse(second_check["valid"])
        self.assertEqual(second_check["reason"], "Kod już wykorzystany")

    def test_minor_is_rejected_by_gov_a(self):
        gov_a = GovA_AgeVerifier()
        minor = User(pesel="10250154321", name="Maly Jas")

        result = minor.request_blind_signature(gov_a)

        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "Osoba niepełnoletnia")

    def test_tampered_signature_is_rejected_by_gov_b(self):
        gov_a = GovA_AgeVerifier()
        gov_b = GovB_CodeIssuer()
        user = User(pesel="95030112345", name="Jan Kowalski")

        result_a = user.request_blind_signature(gov_a)
        self.assertTrue(result_a["success"])

        blinded_oprf, _, _ = gov_b.oprf.client_blind(b"unit-test")

        result = gov_b.process_oprf_and_issue_code(
            blinded_oprf_input=blinded_oprf,
            token_hash=user.token_hash,
            token_signature=(user.token_signature + 1) % gov_a.rsa.n,
            gov_a_pubkey_e=gov_a.rsa.e,
            gov_a_pubkey_n=gov_a.rsa.n,
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "Nieważny podpis weryfikacji wieku")

    def test_code_expires_after_ttl(self):
        gov_a = GovA_AgeVerifier()
        gov_b = GovB_CodeIssuer()
        user = User(pesel="95030112345", name="Jan Kowalski")

        self.assertTrue(user.request_blind_signature(gov_a)["success"])
        issued = user.get_anonymous_code(gov_b)
        self.assertTrue(issued["success"])

        code = issued["code"]
        expires_at = gov_b.active_codes[code]["expires"]

        with patch("age_verification_poc.time.time", return_value=expires_at + 1):
            check = gov_b.verify_code(code)

        self.assertFalse(check["valid"])
        self.assertEqual(check["reason"], "Kod wygasł")
        self.assertNotIn(code, gov_b.active_codes)

    def test_public_key_spoofing_bypass_current_behavior(self):
        # This test documents an existing weakness: Gov B accepts the pubkey
        # provided by the client instead of a pinned Gov A key.
        gov_b = GovB_CodeIssuer()

        attacker_keypair = RSAKeyPair(bits=512)
        attacker_token = secrets.randbelow(attacker_keypair.n - 2) + 2
        attacker_token_hash = int.from_bytes(
            hashlib.sha256(str(attacker_token).encode()).digest(), "big"
        ) % attacker_keypair.n
        attacker_signature = pow(
            attacker_token_hash, attacker_keypair.d, attacker_keypair.n
        )

        blinded_oprf, _, _ = gov_b.oprf.client_blind(b"attacker-flow")
        result = gov_b.process_oprf_and_issue_code(
            blinded_oprf_input=blinded_oprf,
            token_hash=attacker_token_hash,
            token_signature=attacker_signature,
            gov_a_pubkey_e=attacker_keypair.e,
            gov_a_pubkey_n=attacker_keypair.n,
        )

        self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()

