"""
══════════════════════════════════════════════════════════════════════
  PROOF OF CONCEPT: Anonimowa Weryfikacja Wieku
  Blind RSA Signatures + Oblivious PRF + Krótki Kod
══════════════════════════════════════════════════════════════════════
Architektura trójstronna (wszystko rządowe, ale kryptograficznie rozdzielone):
  ┌─────────────┐     ślepy podpis      ┌─────────────┐
  │  RZĄD A     │◄────────────────────►  │  UŻYTKOWNIK │
  │ (mObywatel) │  "wiem KTO ale nie    │             │
  │ weryfikuje  │   wiem CO podpisałem" │  przepisuje │
  │ wiek        │                        │  kod na     │
  └─────────────┘                        │  stronie    │
                                         └──────┬──────┘
  ┌─────────────┐    anonimowy token            │ kod 6-cyfrowy
  │  RZĄD B     │◄─────────────────────────────►│
  │ (NASK/COI)  │  "wiem ŻE jest ważny         │
  │ wydaje kody │   ale nie wiem CZYJ"          ▼
  └──────┬──────┘                        ┌─────────────┐
         │  "tak/nie"                    │ STRONA 18+  │
         └──────────────────────────────►│ zna kod,    │
                                         │ nie zna     │
                                         │ tożsamości  │
                                         └─────────────┘
Gwarancje prywatności:
  • Rząd A:  zna tożsamość, NIE zna kodu ani strony docelowej
  • Rząd B:  zna kod, NIE zna tożsamości (matematycznie niemożliwe)
  • Strona:  zna kod, NIE zna tożsamości ani źródła
  • Korelacja czasowa: neutralizowana przez batch prefetch tokenów
"""
import hashlib
import secrets
import time
import json
from dataclasses import dataclass, field


# ════════════════════════════════════════════════════════════════════
# CZĘŚĆ 1: Prymitywy kryptograficzne
# ════════════════════════════════════════════════════════════════════

class RSAKeyPair:
    """Uproszczone RSA do demonstracji blind signatures.

    W produkcji: użyj RSA-PSS z biblioteką typu `cryptography`.
    Tu: ręczna implementacja dla przejrzystości matematyki.
    """

    def __init__(self, bits=512):
        # UWAGA: 512 bitów to ZA MAŁO na produkcję (min. 2048)
        # Tu używamy małych kluczy dla szybkości demo
        self.p = self._generate_prime(bits // 2)
        self.q = self._generate_prime(bits // 2)
        self.n = self.p * self.q
        self.phi = (self.p - 1) * (self.q - 1)
        self.e = 65537
        self.d = pow(self.e, -1, self.phi)

    def _generate_prime(self, bits):
        """Generuje prawdopodobny prime (Miller-Rabin wystarczy na demo)."""
        while True:
            n = secrets.randbits(bits) | (1 << bits - 1) | 1
            if self._is_probable_prime(n):
                return n

    def _is_probable_prime(self, n, rounds=20):
        if n < 2: return False
        if n % 2 == 0: return n == 2
        d, r = n - 1, 0
        while d % 2 == 0:
            d //= 2
            r += 1
        for _ in range(rounds):
            a = secrets.randbelow(n - 3) + 2
            x = pow(a, d, n)
            if x == 1 or x == n - 1:
                continue
            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        return True


class BlindRSA:
    """Blind RSA Signature (schemat Chauma, 1983).

    Idea: użytkownik "zaślepia" wiadomość losowym czynnikiem,
    serwer podpisuje zaślepioną wiadomość, użytkownik "odślepia"
    podpis. Wynik: ważny podpis RSA, ale serwer NIGDY nie widział
    oryginalnej wiadomości.

    Matematyka:
      1. Użytkownik: blinded = m * r^e mod n     (zaślepienie)
      2. Serwer:     blind_sig = blinded^d mod n  (podpis ślepego)
      3. Użytkownik: sig = blind_sig / r mod n    (odślepienie)
      4. Weryfikacja: sig^e mod n == m             (standardowe RSA)

    Serwer widział tylko `blinded` — losowy szum, z którego
    NIE DA SIĘ odzyskać `m` bez znajomości `r`.
    """

    @staticmethod
    def blind(message_hash: int, pubkey_e: int, pubkey_n: int) -> tuple:
        """Użytkownik zaślepia wiadomość przed wysłaniem do podpisu.

        Returns: (blinded_message, blinding_factor_r)
        """
        while True:
            r = secrets.randbelow(pubkey_n - 2) + 2
            # r musi być odwracalne mod n
            try:
                r_inv = pow(r, -1, pubkey_n)
                break
            except ValueError:
                continue

        # blinded = m * r^e mod n
        r_to_e = pow(r, pubkey_e, pubkey_n)
        blinded = (message_hash * r_to_e) % pubkey_n

        return blinded, r

    @staticmethod
    def sign_blind(blinded_message: int, privkey_d: int, n: int) -> int:
        """Serwer (Rząd A) podpisuje zaślepioną wiadomość.

        Serwer NIE WIE co podpisuje — widzi losowy szum.
        """
        return pow(blinded_message, privkey_d, n)

    @staticmethod
    def unblind(blind_signature: int, r: int, n: int) -> int:
        """Użytkownik odślepia podpis.

        Wynik: ważny podpis RSA na oryginalnej wiadomości,
        którego serwer nigdy nie widział.
        """
        r_inv = pow(r, -1, n)
        return (blind_signature * r_inv) % n

    @staticmethod
    def verify(message_hash: int, signature: int, pubkey_e: int, n: int) -> bool:
        """Standardowa weryfikacja RSA — działa na odślepionym podpisie!"""
        return pow(signature, pubkey_e, n) == message_hash


class OPRF:
    """Oblivious Pseudorandom Function (OPRF).

    Serwer (Rząd B) przetwarza dane użytkownika swoim kluczem,
    ale NIGDY NIE WIDZI ani danych wejściowych, ani wyniku.

    Bazujemy na multiplikatywnym zaślepieniu w grupie Z*_p:

      F(k, x) = H(x)^k mod p

    Ale serwer nigdy nie widzi H(x) ani F(k, x):
      1. Klient: h = H(x), losuje r, wysyła blinded = h^r mod p
      2. Serwer: zwraca evaluated = blinded^k mod p = h^(r*k) mod p
      3. Klient: odślepia = evaluated^(1/r) mod p = h^k mod p = F(k,x)

    Serwer widział tylko h^r — losowy element grupy.
    """

    def __init__(self, bits=512):
        # Generujemy bezpieczną grupę (p = 2q + 1, safe prime)
        # W produkcji: użyj standardowej krzywej EC (P-256, ristretto255)
        self.q = self._find_prime(bits - 1)
        self.p = 2 * self.q + 1
        while not self._is_prime(self.p):
            self.q = self._find_prime(bits - 1)
            self.p = 2 * self.q + 1

        # Generator podgrupy rzędu q
        self.g = self._find_generator()

        # Sekretny klucz serwera
        self.server_key = secrets.randbelow(self.q - 1) + 1

    def _find_prime(self, bits):
        while True:
            n = secrets.randbits(bits) | (1 << bits - 1) | 1
            if self._is_prime(n):
                return n

    def _is_prime(self, n, rounds=20):
        if n < 2: return False
        if n % 2 == 0: return n == 2
        d, r = n - 1, 0
        while d % 2 == 0:
            d //= 2
            r += 1
        for _ in range(rounds):
            a = secrets.randbelow(n - 3) + 2
            x = pow(a, d, n)
            if x == 1 or x == n - 1: continue
            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1: break
            else:
                return False
        return True

    def _find_generator(self):
        """Znajduje generator podgrupy rzędu q w Z*_p."""
        while True:
            h = secrets.randbelow(self.p - 2) + 2
            g = pow(h, 2, self.p)  # g = h^2 mod p, rząd q (bo p = 2q+1)
            if g != 1:
                return g

    def hash_to_group(self, data: bytes) -> int:
        """Mapuje arbitrarne dane na element grupy."""
        h = int.from_bytes(hashlib.sha512(data).digest(), 'big')
        return pow(self.g, h % self.q, self.p)

    # --- Strona klienta ---

    def client_blind(self, input_data: bytes) -> tuple:
        """Klient zaślepia swoje dane przed wysłaniem do serwera.

        Returns: (blinded_element, blinding_factor, original_hash)
        """
        h = self.hash_to_group(input_data)
        r = secrets.randbelow(self.q - 1) + 1  # losowy czynnik zaślepiający

        # blinded = h^r mod p — serwer nie może odzyskać h
        blinded = pow(h, r, self.p)

        return blinded, r, h

    # --- Strona serwera ---

    def server_evaluate(self, blinded: int) -> int:
        """Serwer (Rząd B) przetwarza zaślepione dane swoim kluczem.

        Serwer NIE WIE co przetwarza — widzi losowy element grupy.
        Zwraca: blinded^k mod p
        """
        return pow(blinded, self.server_key, self.p)

    # --- Strona klienta ---

    def client_unblind(self, evaluated: int, r: int) -> int:
        """Klient odślepia wynik serwera.

        evaluated = h^(r*k) mod p
        result = evaluated^(1/r) mod p = h^k mod p = F(k, input)

        To jest finalna wartość PRF, której serwer NIGDY nie widział.
        """
        r_inv = pow(r, -1, self.q)
        return pow(evaluated, r_inv, self.p)

    # --- Weryfikacja (do testów) ---

    def compute_directly(self, input_data: bytes) -> int:
        """Bezpośrednie obliczenie F(k, x) — tylko do testów!
        W prawdziwym systemie nikt nie ma dostępu do obu stron naraz.
        """
        h = self.hash_to_group(input_data)
        return pow(h, self.server_key, self.p)


# ════════════════════════════════════════════════════════════════════
# CZĘŚĆ 2: Symulacja podmiotów systemu
# ════════════════════════════════════════════════════════════════════

@dataclass
class GovA_AgeVerifier:
    """RZĄD A — Weryfikator wieku (np. mObywatel).

    WIDZI: tożsamość użytkownika (PESEL, imię, wiek)
    NIE WIDZI: tokenu który podpisuje (blind signature)
    NIE WIE: na jakiej stronie użytkownik użyje kodu
    """
    name: str = "mObywatel (Rząd A)"
    rsa: RSAKeyPair = None

    # Audit log — w produkcji: legal retention z czasowym kasowaniem
    log: list = field(default_factory=list)

    def __post_init__(self):
        print(f"[{self.name}] Generuję klucze RSA do ślepych podpisów...")
        self.rsa = RSAKeyPair(bits=512)
        print(f"[{self.name}] Klucze gotowe. Klucz publiczny udostępniony.")

    def verify_age_and_blind_sign(self, pesel: str, blinded_token: int) -> dict:
        """Użytkownik prosi o podpis po weryfikacji wieku.

        Rząd A:
          1. Sprawdza PESEL → czy osoba ma 18+
          2. Podpisuje ZAŚLEPIONY token (nie widzi co podpisuje)
          3. Loguje: "użytkownik X poprosił o weryfikację" (ale NIE token)
        """
        # Symulacja weryfikacji wieku z PESEL
        year = int(pesel[:2])
        month = int(pesel[2:4])
        if month > 20:
            year += 2000
            month -= 20
        else:
            year += 1900

        age = 2026 - year  # uproszczenie
        is_adult = age >= 18

        print(f"\n[{self.name}] Weryfikacja wieku:")
        print(f"  PESEL: {pesel[:6]}****{pesel[-1]}")
        print(f"  Wiek: {age} lat")
        print(f"  Pełnoletni: {'TAK ✓' if is_adult else 'NIE ✗'}")

        if not is_adult:
            return {"success": False, "reason": "Osoba niepełnoletnia"}

        # Podpisujemy ZAŚLEPIONY token — nie wiemy co to jest!
        blind_signature = BlindRSA.sign_blind(
            blinded_token, self.rsa.d, self.rsa.n
        )

        # Log: wiemy KTO poprosił, ale NIE wiemy o CO (token zaślepiony)
        self.log.append({
            "time": time.time(),
            "pesel_hash": hashlib.sha256(pesel.encode()).hexdigest()[:16],
            "action": "blind_sign",
            "blinded_token_seen": hex(blinded_token)[:20] + "...",
            # ↑ Ten hash to LOSOWY SZUM — nie da się z niego odzyskać tokenu
        })

        print(f"  Podpisano zaślepiony token (nie wiem co podpisałem!)")
        print(f"  Widzę tylko losowy szum: {hex(blinded_token)[:24]}...")

        return {
            "success": True,
            "blind_signature": blind_signature,
            "pubkey_e": self.rsa.e,
            "pubkey_n": self.rsa.n,
        }


@dataclass
class GovB_CodeIssuer:
    """RZĄD B — Wydawca kodów (np. NASK).

    WIDZI: anonimowy token z ważnym podpisem Rządu A
    NIE WIDZI: tożsamości użytkownika (matematycznie niemożliwe)
    NIE WIE: kto stoi za danym tokenem

    OPRF zapewnia, że nawet dane przechodzące przez serwer
    są kryptograficznie zaślepione — serwer przetwarza dane
    których nie widzi.
    """
    name: str = "NASK (Rząd B)"
    oprf: OPRF = None

    # Baza aktywnych kodów: {kod: {token_hash, expires}}
    active_codes: dict = field(default_factory=dict)

    # Audit log
    log: list = field(default_factory=list)

    def __post_init__(self):
        print(f"[{self.name}] Inicjalizuję parametry OPRF...")
        self.oprf = OPRF(bits=256)
        print(f"[{self.name}] OPRF gotowy. Parametry publiczne udostępnione.")

    def process_oprf_and_issue_code(
        self,
        blinded_oprf_input: int,
        token_hash: int,
        token_signature: int,
        gov_a_pubkey_e: int,
        gov_a_pubkey_n: int,
    ) -> dict:
        """Przetwarza żądanie wydania kodu.

        1. Weryfikuje podpis Rządu A (czy wiek był sprawdzony)
        2. Przetwarza OPRF na zaślepionych danych (nie widzi treści)
        3. Generuje 6-cyfrowy kod z TTL 5 minut
        """
        print(f"\n[{self.name}] Otrzymano żądanie wydania kodu:")

        # Krok 1: Weryfikacja podpisu Rządu A
        sig_valid = BlindRSA.verify(
            token_hash, token_signature, gov_a_pubkey_e, gov_a_pubkey_n
        )

        print(f"  Podpis Rządu A: {'WAŻNY ✓' if sig_valid else 'NIEWAŻNY ✗'}")

        if not sig_valid:
            return {"success": False, "reason": "Nieważny podpis weryfikacji wieku"}

        # Krok 2: OPRF — przetwarzam zaślepione dane
        # NIE WIEM co to za dane! Widzę tylko losowy element grupy.
        oprf_evaluated = self.oprf.server_evaluate(blinded_oprf_input)

        print(f"  OPRF: przetworzono zaślepione dane")
        print(f"  Widzę na wejściu: {hex(blinded_oprf_input)[:24]}... (losowy szum)")
        print(f"  Zwracam wynik:    {hex(oprf_evaluated)[:24]}... (też losowy szum)")

        # Krok 3: Generuję 6-cyfrowy kod
        code = f"{secrets.randbelow(900000) + 100000}"
        expires = time.time() + 300  # 5 minut TTL

        # Zapisuję kod z hashem tokenu (NIE z tożsamością!)
        # Hash tokenu pozwala na jednorazowe użycie
        self.active_codes[code] = {
            "token_fingerprint": hashlib.sha256(
                str(token_hash).encode()
            ).hexdigest()[:16],
            "expires": expires,
            "used": False,
        }

        print(f"  Wygenerowano kod: {code} (TTL: 5 min)")

        # Log: wiemy ŻE wydano kod, ale NIE wiemy KOMU
        self.log.append({
            "time": time.time(),
            "action": "code_issued",
            "code_hash": hashlib.sha256(code.encode()).hexdigest()[:16],
            "identity": "NIEZNANA — blind signature uniemożliwia identyfikację",
        })

        return {
            "success": True,
            "code": code,
            "oprf_evaluated": oprf_evaluated,
            "expires_in_seconds": 300,
        }

    def verify_code(self, code: str) -> dict:
        """Strona 18+ odpytuje: czy ten kod jest ważny?

        Odpowiedź: TAK/NIE. Kod jest jednorazowy — po weryfikacji spalony.
        """
        print(f"\n[{self.name}] Weryfikacja kodu od strony 18+:")
        print(f"  Kod: {code}")

        if code not in self.active_codes:
            print(f"  Wynik: NIEZNANY KOD ✗")
            return {"valid": False, "reason": "Kod nie istnieje"}

        entry = self.active_codes[code]

        if entry["used"]:
            print(f"  Wynik: KOD JUŻ UŻYTY ✗")
            return {"valid": False, "reason": "Kod już wykorzystany"}

        if time.time() > entry["expires"]:
            print(f"  Wynik: KOD WYGASŁ ✗")
            del self.active_codes[code]
            return {"valid": False, "reason": "Kod wygasł"}

        # Kod ważny — spalamy go (jednorazowy)
        entry["used"] = True
        print(f"  Wynik: KOD WAŻNY ✓ (spalony po użyciu)")

        return {"valid": True, "age_verified": True}


@dataclass
class User:
    """UŻYTKOWNIK — łączy oba systemy, ale zachowuje anonimowość.

    Jako jedyny widzi pełny obraz, ale żaden z serwerów nie może
    zrekonstruować tego co widzi użytkownik.
    """
    pesel: str
    name: str

    def request_blind_signature(self, gov_a: GovA_AgeVerifier) -> dict:
        """Krok 1: Prosię Rząd A o ślepy podpis (weryfikacja wieku)."""

        print(f"\n{'='*60}")
        print(f"UŻYTKOWNIK: {self.name}")
        print(f"{'='*60}")
        print(f"\n[Użytkownik] Generuję losowy token i zaślepiam go...")

        # Generuję losowy token — to będzie mój anonimowy bilet
        self.token = secrets.randbelow(gov_a.rsa.n - 2) + 2
        self.token_hash = int.from_bytes(
            hashlib.sha256(str(self.token).encode()).digest(), 'big'
        ) % gov_a.rsa.n

        # Zaślepiam token — Rząd A nie zobaczy oryginału
        self.blinded_token, self.blind_r = BlindRSA.blind(
            self.token_hash, gov_a.rsa.e, gov_a.rsa.n
        )

        print(f"  Mój token (sekretny):        {hex(self.token)[:24]}...")
        print(f"  Zaślepiony (to widzi Rząd A): {hex(self.blinded_token)[:24]}...")
        print(f"  → Rząd A NIE MOŻE odzyskać mojego tokenu z tego co widzi")

        # Wysyłam PESEL + zaślepiony token do Rządu A
        result = gov_a.verify_age_and_blind_sign(self.pesel, self.blinded_token)

        if result["success"]:
            # Odślepiam podpis — teraz mam ważny podpis na moim tokenie!
            self.token_signature = BlindRSA.unblind(
                result["blind_signature"], self.blind_r, result["pubkey_n"]
            )

            # Weryfikuję że podpis jest poprawny
            sig_ok = BlindRSA.verify(
                self.token_hash, self.token_signature,
                result["pubkey_e"], result["pubkey_n"]
            )

            print(f"\n[Użytkownik] Odślepiłem podpis.")
            print(f"  Podpis ważny: {'TAK ✓' if sig_ok else 'NIE ✗'}")
            print(f"  Rząd A podpisał coś, czego nigdy nie widział!")

            self.gov_a_pubkey_e = result["pubkey_e"]
            self.gov_a_pubkey_n = result["pubkey_n"]

        return result

    def get_anonymous_code(self, gov_b: GovB_CodeIssuer) -> dict:
        """Krok 2: Przedstawiam anonimowy token Rządowi B, dostaję kod."""

        print(f"\n[Użytkownik] Wysyłam anonimowy token do Rządu B...")
        print(f"  Rząd B nie wie kim jestem — ma tylko token z podpisem Rządu A")

        # Zaślepiam dane wejściowe dla OPRF
        oprf_input = f"age_verification_{self.token}_{time.time()}".encode()
        blinded_oprf, self.oprf_r, self.oprf_h = gov_b.oprf.client_blind(oprf_input)

        # Wysyłam do Rządu B:
        #   - zaślepione dane OPRF (Rząd B nie widzi treści)
        #   - token z podpisem Rządu A (Rząd B weryfikuje wiek, nie zna tożsamości)
        result = gov_b.process_oprf_and_issue_code(
            blinded_oprf_input=blinded_oprf,
            token_hash=self.token_hash,
            token_signature=self.token_signature,
            gov_a_pubkey_e=self.gov_a_pubkey_e,
            gov_a_pubkey_n=self.gov_a_pubkey_n,
        )

        if result["success"]:
            # Odślepiam wynik OPRF (opcjonalnie — do dodatkowej weryfikacji)
            oprf_result = gov_b.oprf.client_unblind(
                result["oprf_evaluated"], self.oprf_r
            )

            self.code = result["code"]
            print(f"\n[Użytkownik] Otrzymałem kod: ★ {self.code} ★")
            print(f"  Mogę go teraz przepisać na dowolnej stronie 18+")

        return result


class AdultSite:
    """STRONA 18+ — weryfikuje kod, nie zna tożsamości.

    WIDZI: 6-cyfrowy kod
    NIE WIDZI: tożsamości, PESELu, nic
    DOWIADUJE SIĘ: "wiek zweryfikowany" / "kod nieważny"
    """

    def __init__(self, name="example-adult-site.pl"):
        self.name = name

    def verify_user(self, code: str, gov_b: GovB_CodeIssuer) -> bool:
        """Użytkownik wpisał kod — weryfikujemy go u Rządu B."""

        print(f"\n{'='*60}")
        print(f"STRONA 18+: {self.name}")
        print(f"{'='*60}")
        print(f"\n[{self.name}] Użytkownik wpisał kod: {code}")
        print(f"  Odpytuję Rząd B o ważność...")

        result = gov_b.verify_code(code)

        if result["valid"]:
            print(f"\n[{self.name}] ✓ Wiek zweryfikowany! Przyznano dostęp.")
            print(f"  Nie wiem kim jest użytkownik — i nie muszę wiedzieć.")
        else:
            print(f"\n[{self.name}] ✗ Kod odrzucony: {result['reason']}")

        return result["valid"]


# ════════════════════════════════════════════════════════════════════
# CZĘŚĆ 3: Pełna symulacja
# ════════════════════════════════════════════════════════════════════

def print_header(text):
    width = 64
    print(f"\n{'█'*width}")
    print(f"█{text:^{width-2}}█")
    print(f"{'█'*width}")


def print_privacy_analysis(gov_a, gov_b):
    """Analiza: co każdy podmiot wie po zakończeniu procesu."""

    print_header("ANALIZA PRYWATNOŚCI")

    print(f"""
┌─────────────────────────────────────────────────────────┐
│                    RZĄD A (mObywatel)                   │
├─────────────────────────────────────────────────────────┤
│ WIE:                                                    │
│  • Użytkownik o danym PESEL poprosił o weryfikację      │
│  • Użytkownik jest pełnoletni                           │
│                                                         │
│ NIE WIE (kryptograficznie):                             │
│  • Jaki token podpisał (blind signature)                │
│  • Jaki kod otrzymał użytkownik                         │
│  • Na jakiej stronie użytkownik użył kodu               │
│                                                         │
│ Logi Rządu A:""")
    for entry in gov_a.log:
        print(f"│  {json.dumps(entry, indent=2, default=str)[:55]}")
    print(f"""│                                                         │
│ → Zaślepiony token to LOSOWY SZUM — nic z niego        │
│   nie wynika, nawet przy zmowie z Rządem B              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    RZĄD B (NASK)                        │
├─────────────────────────────────────────────────────────┤
│ WIE:                                                    │
│  • Ktoś (anonimowy) z ważną weryfikacją wieku           │
│    poprosił o kod                                       │
│  • Kod został/nie został użyty                          │
│                                                         │
│ NIE WIE (kryptograficznie):                             │
│  • Kim jest użytkownik (blind sig → brak powiązania)    │
│  • Jaki był oryginalny token (OPRF → zaślepione dane)   │
│  • Jakie dane przetworzyło OPRF (oblivious evaluation)  │
│                                                         │
│ Logi Rządu B:""")
    for entry in gov_b.log:
        print(f"│  {json.dumps(entry, indent=2, default=str)[:55]}")
    print(f"""│                                                         │
│ → Nawet gdyby Rząd B CHCIAŁ zidentyfikować użytkownika │
│   — nie ma matematycznej możliwości                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                 ZMOWA RZĄDU A + B?                       │
├─────────────────────────────────────────────────────────┤
│ Rząd A ma: PESEL + zaślepiony_token (losowy szum)       │
│ Rząd B ma: odślepiony_token + kod (bez tożsamości)      │
│                                                         │
│ Zaślepiony token ≠ odślepiony token                     │
│ (to jest sedno blind signature!)                        │
│                                                         │
│ Nawet mając OBA logi, NIE DA SIĘ powiązać wpisów        │
│ z Rządu A z wpisami z Rządu B.                          │
│                                                         │
│ Jedyny atak: korelacja czasowa przy małym ruchu.         │
│ Obrona: batch prefetch tokenów (użytkownik pobiera      │
│ tokeny na zapas, losowo, w tle).                        │
└─────────────────────────────────────────────────────────┘""")


def run_demo():
    """Uruchamia pełną symulację systemu."""

    print_header("INICJALIZACJA SYSTEMU")

    # Inicjalizacja podmiotów rządowych
    gov_a = GovA_AgeVerifier()
    gov_b = GovB_CodeIssuer()

    # Strona 18+
    site = AdultSite("example-adult.pl")

    # Użytkownik (PESEL z 1995 roku → 31 lat → pełnoletni)
    user = User(pesel="95030112345", name="Jan Kowalski")

    # ── KROK 1: Weryfikacja wieku + ślepy podpis ──
    print_header("KROK 1: WERYFIKACJA WIEKU (Rząd A)")
    result_a = user.request_blind_signature(gov_a)

    if not result_a["success"]:
        print("Weryfikacja nieudana — koniec.")
        return

    # ── KROK 2: Anonimowy token → krótki kod ──
    print_header("KROK 2: WYDANIE KODU (Rząd B)")
    result_b = user.get_anonymous_code(gov_b)

    if not result_b["success"]:
        print("Wydanie kodu nieudane — koniec.")
        return

    # ── KROK 3: Użycie kodu na stronie 18+ ──
    print_header("KROK 3: WERYFIKACJA NA STRONIE 18+")
    site.verify_user(user.code, gov_b)

    # ── KROK 4: Próba ponownego użycia (powinna się nie udać) ──
    print_header("KROK 4: PRÓBA REUŻYCIA KODU (atak)")
    site.verify_user(user.code, gov_b)

    # ── Analiza prywatności ──
    print_privacy_analysis(gov_a, gov_b)

    # ── Test: osoba niepełnoletnia ──
    print_header("TEST: OSOBA NIEPEŁNOLETNIA")
    minor = User(pesel="10250154321", name="Mały Jaś")  # 2010 → 16 lat
    result_minor = minor.request_blind_signature(gov_a)
    print(f"\n→ System poprawnie odrzucił niepełnoletniego: {result_minor}")


if __name__ == "__main__":
    run_demo()
