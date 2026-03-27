"""
══════════════════════════════════════════════════════════════════════
  DOWÓD KONCEPCJI: Anonimowa Weryfikacja Wieku
  Ślepe Podpisy RSA + Nieświadoma Funkcja Pseudolosowa + Krótki Kod
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
  • Korelacja czasowa: neutralizowana przez grupowe pobieranie tokenów z wyprzedzeniem
"""
import hashlib
import secrets
import time
import json
from dataclasses import dataclass, field


# ════════════════════════════════════════════════════════════════════
# CZĘŚĆ 1: Prymitywy kryptograficzne
# ════════════════════════════════════════════════════════════════════

class ParaKluczyRSA:
    """Uproszczone RSA do demonstracji ślepych podpisów.

    W produkcji: użyj RSA-PSS z biblioteką typu `cryptography`.
    Tu: ręczna implementacja dla przejrzystości matematyki.
    """

    def __init__(self, bity=512):
        # UWAGA: 512 bitów to ZA MAŁO na produkcję (min. 2048)
        # Tu używamy małych kluczy dla szybkości demo
        self.p = self._generuj_liczbe_pierwsza(bity // 2)
        self.q = self._generuj_liczbe_pierwsza(bity // 2)
        self.n = self.p * self.q
        self.phi = (self.p - 1) * (self.q - 1)
        self.e = 65537
        self.d = pow(self.e, -1, self.phi)

    def _generuj_liczbe_pierwsza(self, bity):
        """Generuje prawdopodobną liczbę pierwszą (Miller-Rabin wystarczy na demo)."""
        while True:
            n = secrets.randbits(bity) | (1 << bity - 1) | 1
            if self._czy_prawdopodobnie_pierwsza(n):
                return n

    def _czy_prawdopodobnie_pierwsza(self, n, rundy=20):
        if n < 2: return False
        if n % 2 == 0: return n == 2
        d, r = n - 1, 0
        while d % 2 == 0:
            d //= 2
            r += 1
        for _ in range(rundy):
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


class SlepyRSA:
    """Ślepy Podpis RSA (schemat Chauma, 1983).

    Idea: użytkownik "zaślepia" wiadomość losowym czynnikiem,
    serwer podpisuje zaślepioną wiadomość, użytkownik "odślepia"
    podpis. Wynik: ważny podpis RSA, ale serwer NIGDY nie widział
    oryginalnej wiadomości.

    Matematyka:
      1. Użytkownik: zaslepiona = m * r^e mod n     (zaślepienie)
      2. Serwer:     slepy_podpis = zaslepiona^d mod n  (podpis ślepego)
      3. Użytkownik: podpis = slepy_podpis / r mod n    (odślepienie)
      4. Weryfikacja: podpis^e mod n == m             (standardowe RSA)

    Serwer widział tylko `zaslepiona` — losowy szum, z którego
    NIE DA SIĘ odzyskać `m` bez znajomości `r`.
    """

    @staticmethod
    def zaslep(hash_wiadomosci: int, klucz_publiczny_e: int, klucz_publiczny_n: int) -> tuple:
        """Użytkownik zaślepia wiadomość przed wysłaniem do podpisu.

        Zwraca: (zaslepiona_wiadomosc, czynnik_zaslepiajacy_r)
        """
        while True:
            r = secrets.randbelow(klucz_publiczny_n - 2) + 2
            # r musi być odwracalne mod n
            try:
                r_odw = pow(r, -1, klucz_publiczny_n)
                break
            except ValueError:
                continue

        # zaslepiona = m * r^e mod n
        r_do_e = pow(r, klucz_publiczny_e, klucz_publiczny_n)
        zaslepiona = (hash_wiadomosci * r_do_e) % klucz_publiczny_n

        return zaslepiona, r

    @staticmethod
    def podpisz_slepo(zaslepiona_wiadomosc: int, klucz_prywatny_d: int, n: int) -> int:
        """Serwer (Rząd A) podpisuje zaślepioną wiadomość.

        Serwer NIE WIE co podpisuje — widzi losowy szum.
        """
        return pow(zaslepiona_wiadomosc, klucz_prywatny_d, n)

    @staticmethod
    def odslep(slepy_podpis: int, r: int, n: int) -> int:
        """Użytkownik odślepia podpis.

        Wynik: ważny podpis RSA na oryginalnej wiadomości,
        którego serwer nigdy nie widział.
        """
        r_odw = pow(r, -1, n)
        return (slepy_podpis * r_odw) % n

    @staticmethod
    def zweryfikuj(hash_wiadomosci: int, podpis: int, klucz_publiczny_e: int, n: int) -> bool:
        """Standardowa weryfikacja RSA — działa na odślepionym podpisie!"""
        return pow(podpis, klucz_publiczny_e, n) == hash_wiadomosci


class NieswiadomaFunkcjaPRF:
    """Nieświadoma Funkcja Pseudolosowa (OPRF).

    Serwer (Rząd B) przetwarza dane użytkownika swoim kluczem,
    ale NIGDY NIE WIDZI ani danych wejściowych, ani wyniku.

    Bazujemy na multiplikatywnym zaślepieniu w grupie Z*_p:

      F(k, x) = H(x)^k mod p

    Ale serwer nigdy nie widzi H(x) ani F(k, x):
      1. Klient: h = H(x), losuje r, wysyła zaslepione = h^r mod p
      2. Serwer: zwraca wynik = zaslepione^k mod p = h^(r*k) mod p
      3. Klient: odślepia = wynik^(1/r) mod p = h^k mod p = F(k,x)

    Serwer widział tylko h^r — losowy element grupy.
    """

    def __init__(self, bity=512):
        # Generujemy bezpieczną grupę (p = 2q + 1, bezpieczna liczba pierwsza)
        # W produkcji: użyj standardowej krzywej EC (P-256, ristretto255)
        self.q = self._znajdz_pierwsza(bity - 1)
        self.p = 2 * self.q + 1
        while not self._czy_pierwsza(self.p):
            self.q = self._znajdz_pierwsza(bity - 1)
            self.p = 2 * self.q + 1

        # Generator podgrupy rzędu q
        self.g = self._znajdz_generator()

        # Sekretny klucz serwera
        self.klucz_serwera = secrets.randbelow(self.q - 1) + 1

    def _znajdz_pierwsza(self, bity):
        while True:
            n = secrets.randbits(bity) | (1 << bity - 1) | 1
            if self._czy_pierwsza(n):
                return n

    def _czy_pierwsza(self, n, rundy=20):
        if n < 2: return False
        if n % 2 == 0: return n == 2
        d, r = n - 1, 0
        while d % 2 == 0:
            d //= 2
            r += 1
        for _ in range(rundy):
            a = secrets.randbelow(n - 3) + 2
            x = pow(a, d, n)
            if x == 1 or x == n - 1: continue
            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1: break
            else:
                return False
        return True

    def _znajdz_generator(self):
        """Znajduje generator podgrupy rzędu q w Z*_p."""
        while True:
            h = secrets.randbelow(self.p - 2) + 2
            g = pow(h, 2, self.p)  # g = h^2 mod p, rząd q (bo p = 2q+1)
            if g != 1:
                return g

    def hashuj_do_grupy(self, dane: bytes) -> int:
        """Mapuje arbitralne dane na element grupy."""
        h = int.from_bytes(hashlib.sha512(dane).digest(), 'big')
        return pow(self.g, h % self.q, self.p)

    # --- Strona klienta ---

    def klient_zaslep(self, dane_wejsciowe: bytes) -> tuple:
        """Klient zaślepia swoje dane przed wysłaniem do serwera.

        Zwraca: (zaslepiony_element, czynnik_zaslepiajacy, oryginalny_hash)
        """
        h = self.hashuj_do_grupy(dane_wejsciowe)
        r = secrets.randbelow(self.q - 1) + 1  # losowy czynnik zaślepiający

        # zaslepione = h^r mod p — serwer nie może odzyskać h
        zaslepione = pow(h, r, self.p)

        return zaslepione, r, h

    # --- Strona serwera ---

    def serwer_oblicz(self, zaslepione: int) -> int:
        """Serwer (Rząd B) przetwarza zaślepione dane swoim kluczem.

        Serwer NIE WIE co przetwarza — widzi losowy element grupy.
        Zwraca: zaslepione^k mod p
        """
        return pow(zaslepione, self.klucz_serwera, self.p)

    # --- Strona klienta ---

    def klient_odslep(self, obliczone: int, r: int) -> int:
        """Klient odślepia wynik serwera.

        obliczone = h^(r*k) mod p
        wynik = obliczone^(1/r) mod p = h^k mod p = F(k, wejście)

        To jest finalna wartość PRF, której serwer NIGDY nie widział.
        """
        r_odw = pow(r, -1, self.q)
        return pow(obliczone, r_odw, self.p)

    # --- Weryfikacja (do testów) ---

    def oblicz_bezposrednio(self, dane_wejsciowe: bytes) -> int:
        """Bezpośrednie obliczenie F(k, x) — tylko do testów!
        W prawdziwym systemie nikt nie ma dostępu do obu stron naraz.
        """
        h = self.hashuj_do_grupy(dane_wejsciowe)
        return pow(h, self.klucz_serwera, self.p)


# ════════════════════════════════════════════════════════════════════
# CZĘŚĆ 2: Symulacja podmiotów systemu
# ════════════════════════════════════════════════════════════════════

@dataclass
class RzadA_WeryfikatorWieku:
    """RZĄD A — Weryfikator wieku (np. mObywatel).

    WIDZI: tożsamość użytkownika (PESEL, imię, wiek)
    NIE WIDZI: tokenu który podpisuje (ślepy podpis)
    NIE WIE: na jakiej stronie użytkownik użyje kodu
    """
    nazwa: str = "mObywatel (Rząd A)"
    rsa: ParaKluczyRSA = None

    # Dziennik audytu — w produkcji: przechowywanie prawne z czasowym kasowaniem
    dziennik: list = field(default_factory=list)

    def __post_init__(self):
        print(f"[{self.nazwa}] Generuję klucze RSA do ślepych podpisów...")
        self.rsa = ParaKluczyRSA(bity=512)
        print(f"[{self.nazwa}] Klucze gotowe. Klucz publiczny udostępniony.")

    def zweryfikuj_wiek_i_podpisz_slepo(self, pesel: str, zaslepiony_token: int) -> dict:
        """Użytkownik prosi o podpis po weryfikacji wieku.

        Rząd A:
          1. Sprawdza PESEL → czy osoba ma 18+
          2. Podpisuje ZAŚLEPIONY token (nie widzi co podpisuje)
          3. Loguje: "użytkownik X poprosił o weryfikację" (ale NIE token)
        """
        # Symulacja weryfikacji wieku z PESEL
        rok = int(pesel[:2])
        miesiac = int(pesel[2:4])
        if miesiac > 20:
            rok += 2000
            miesiac -= 20
        else:
            rok += 1900

        wiek = 2026 - rok  # uproszczenie
        pelnoletni = wiek >= 18

        print(f"\n[{self.nazwa}] Weryfikacja wieku:")
        print(f"  PESEL: {pesel[:6]}****{pesel[-1]}")
        print(f"  Wiek: {wiek} lat")
        print(f"  Pełnoletni: {'TAK ✓' if pelnoletni else 'NIE ✗'}")

        if not pelnoletni:
            return {"sukces": False, "powod": "Osoba niepełnoletnia"}

        # Podpisujemy ZAŚLEPIONY token — nie wiemy co to jest!
        slepy_podpis = SlepyRSA.podpisz_slepo(
            zaslepiony_token, self.rsa.d, self.rsa.n
        )

        # Dziennik: wiemy KTO poprosił, ale NIE wiemy o CO (token zaślepiony)
        self.dziennik.append({
            "czas": time.time(),
            "hash_pesel": hashlib.sha256(pesel.encode()).hexdigest()[:16],
            "akcja": "slepy_podpis",
            "widziany_zaslepiony_token": hex(zaslepiony_token)[:20] + "...",
            # ↑ Ten hash to LOSOWY SZUM — nie da się z niego odzyskać tokenu
        })

        print(f"  Podpisano zaślepiony token (nie wiem co podpisałem!)")
        print(f"  Widzę tylko losowy szum: {hex(zaslepiony_token)[:24]}...")

        return {
            "sukces": True,
            "slepy_podpis": slepy_podpis,
            "klucz_publiczny_e": self.rsa.e,
            "klucz_publiczny_n": self.rsa.n,
        }


@dataclass
class RzadB_WydawcaKodow:
    """RZĄD B — Wydawca kodów (np. NASK).

    WIDZI: anonimowy token z ważnym podpisem Rządu A
    NIE WIDZI: tożsamości użytkownika (matematycznie niemożliwe)
    NIE WIE: kto stoi za danym tokenem

    Nieświadoma Funkcja PRF zapewnia, że nawet dane przechodzące
    przez serwer są kryptograficznie zaślepione — serwer przetwarza
    dane których nie widzi.
    """
    nazwa: str = "NASK (Rząd B)"
    oprf: NieswiadomaFunkcjaPRF = None

    # Baza aktywnych kodów: {kod: {odcisk_tokenu, wygasa}}
    aktywne_kody: dict = field(default_factory=dict)

    # Dziennik audytu
    dziennik: list = field(default_factory=list)

    def __post_init__(self):
        print(f"[{self.nazwa}] Inicjalizuję parametry Nieświadomej Funkcji PRF...")
        self.oprf = NieswiadomaFunkcjaPRF(bity=256)
        print(f"[{self.nazwa}] Funkcja PRF gotowa. Parametry publiczne udostępnione.")

    def przetworz_oprf_i_wydaj_kod(
        self,
        zaslepione_dane_oprf: int,
        hash_tokenu: int,
        podpis_tokenu: int,
        klucz_rzadu_a_e: int,
        klucz_rzadu_a_n: int,
    ) -> dict:
        """Przetwarza żądanie wydania kodu.

        1. Weryfikuje podpis Rządu A (czy wiek był sprawdzony)
        2. Przetwarza PRF na zaślepionych danych (nie widzi treści)
        3. Generuje 6-cyfrowy kod z czasem życia 5 minut
        """
        print(f"\n[{self.nazwa}] Otrzymano żądanie wydania kodu:")

        # Krok 1: Weryfikacja podpisu Rządu A
        podpis_wazny = SlepyRSA.zweryfikuj(
            hash_tokenu, podpis_tokenu, klucz_rzadu_a_e, klucz_rzadu_a_n
        )

        print(f"  Podpis Rządu A: {'WAŻNY ✓' if podpis_wazny else 'NIEWAŻNY ✗'}")

        if not podpis_wazny:
            return {"sukces": False, "powod": "Nieważny podpis weryfikacji wieku"}

        # Krok 2: PRF — przetwarzam zaślepione dane
        # NIE WIEM co to za dane! Widzę tylko losowy element grupy.
        wynik_oprf = self.oprf.serwer_oblicz(zaslepione_dane_oprf)

        print(f"  PRF: przetworzono zaślepione dane")
        print(f"  Widzę na wejściu: {hex(zaslepione_dane_oprf)[:24]}... (losowy szum)")
        print(f"  Zwracam wynik:    {hex(wynik_oprf)[:24]}... (też losowy szum)")

        # Krok 3: Generuję 6-cyfrowy kod
        kod = f"{secrets.randbelow(900000) + 100000}"
        wygasa = time.time() + 300  # 5 minut czasu życia

        # Zapisuję kod z hashem tokenu (NIE z tożsamością!)
        # Hash tokenu pozwala na jednorazowe użycie
        self.aktywne_kody[kod] = {
            "odcisk_tokenu": hashlib.sha256(
                str(hash_tokenu).encode()
            ).hexdigest()[:16],
            "wygasa": wygasa,
            "uzyty": False,
        }

        print(f"  Wygenerowano kod: {kod} (czas życia: 5 min)")

        # Dziennik: wiemy ŻE wydano kod, ale NIE wiemy KOMU
        self.dziennik.append({
            "czas": time.time(),
            "akcja": "wydano_kod",
            "hash_kodu": hashlib.sha256(kod.encode()).hexdigest()[:16],
            "tozsamosc": "NIEZNANA — ślepy podpis uniemożliwia identyfikację",
        })

        return {
            "sukces": True,
            "kod": kod,
            "wynik_oprf": wynik_oprf,
            "wygasa_za_sekund": 300,
        }

    def zweryfikuj_kod(self, kod: str) -> dict:
        """Strona 18+ odpytuje: czy ten kod jest ważny?

        Odpowiedź: TAK/NIE. Kod jest jednorazowy — po weryfikacji spalony.
        """
        print(f"\n[{self.nazwa}] Weryfikacja kodu od strony 18+:")
        print(f"  Kod: {kod}")

        if kod not in self.aktywne_kody:
            print(f"  Wynik: NIEZNANY KOD ✗")
            return {"wazny": False, "powod": "Kod nie istnieje"}

        wpis = self.aktywne_kody[kod]

        if wpis["uzyty"]:
            print(f"  Wynik: KOD JUŻ UŻYTY ✗")
            return {"wazny": False, "powod": "Kod już wykorzystany"}

        if time.time() > wpis["wygasa"]:
            print(f"  Wynik: KOD WYGASŁ ✗")
            del self.aktywne_kody[kod]
            return {"wazny": False, "powod": "Kod wygasł"}

        # Kod ważny — spalamy go (jednorazowy)
        wpis["uzyty"] = True
        print(f"  Wynik: KOD WAŻNY ✓ (spalony po użyciu)")

        return {"wazny": True, "wiek_zweryfikowany": True}


@dataclass
class Uzytkownik:
    """UŻYTKOWNIK — łączy oba systemy, ale zachowuje anonimowość.

    Jako jedyny widzi pełny obraz, ale żaden z serwerów nie może
    zrekonstruować tego co widzi użytkownik.
    """
    pesel: str
    imie: str

    def popros_o_slepy_podpis(self, rzad_a: RzadA_WeryfikatorWieku) -> dict:
        """Krok 1: Proszę Rząd A o ślepy podpis (weryfikacja wieku)."""

        print(f"\n{'='*60}")
        print(f"UŻYTKOWNIK: {self.imie}")
        print(f"{'='*60}")
        print(f"\n[Użytkownik] Generuję losowy token i zaślepiam go...")

        # Generuję losowy token — to będzie mój anonimowy bilet
        self.token = secrets.randbelow(rzad_a.rsa.n - 2) + 2
        self.hash_tokenu = int.from_bytes(
            hashlib.sha256(str(self.token).encode()).digest(), 'big'
        ) % rzad_a.rsa.n

        # Zaślepiam token — Rząd A nie zobaczy oryginału
        self.zaslepiony_token, self.czynnik_r = SlepyRSA.zaslep(
            self.hash_tokenu, rzad_a.rsa.e, rzad_a.rsa.n
        )

        print(f"  Mój token (sekretny):        {hex(self.token)[:24]}...")
        print(f"  Zaślepiony (to widzi Rząd A): {hex(self.zaslepiony_token)[:24]}...")
        print(f"  → Rząd A NIE MOŻE odzyskać mojego tokenu z tego co widzi")

        # Wysyłam PESEL + zaślepiony token do Rządu A
        wynik = rzad_a.zweryfikuj_wiek_i_podpisz_slepo(self.pesel, self.zaslepiony_token)

        if wynik["sukces"]:
            # Odślepiam podpis — teraz mam ważny podpis na moim tokenie!
            self.podpis_tokenu = SlepyRSA.odslep(
                wynik["slepy_podpis"], self.czynnik_r, wynik["klucz_publiczny_n"]
            )

            # Weryfikuję że podpis jest poprawny
            podpis_ok = SlepyRSA.zweryfikuj(
                self.hash_tokenu, self.podpis_tokenu,
                wynik["klucz_publiczny_e"], wynik["klucz_publiczny_n"]
            )

            print(f"\n[Użytkownik] Odślepiłem podpis.")
            print(f"  Podpis ważny: {'TAK ✓' if podpis_ok else 'NIE ✗'}")
            print(f"  Rząd A podpisał coś, czego nigdy nie widział!")

            self.klucz_rzadu_a_e = wynik["klucz_publiczny_e"]
            self.klucz_rzadu_a_n = wynik["klucz_publiczny_n"]

        return wynik

    def pobierz_anonimowy_kod(self, rzad_b: RzadB_WydawcaKodow) -> dict:
        """Krok 2: Przedstawiam anonimowy token Rządowi B, dostaję kod."""

        print(f"\n[Użytkownik] Wysyłam anonimowy token do Rządu B...")
        print(f"  Rząd B nie wie kim jestem — ma tylko token z podpisem Rządu A")

        # Zaślepiam dane wejściowe dla PRF
        dane_prf = f"weryfikacja_wieku_{self.token}_{time.time()}".encode()
        zaslepione_prf, self.czynnik_prf_r, self.hash_prf = rzad_b.oprf.klient_zaslep(dane_prf)

        # Wysyłam do Rządu B:
        #   - zaślepione dane PRF (Rząd B nie widzi treści)
        #   - token z podpisem Rządu A (Rząd B weryfikuje wiek, nie zna tożsamości)
        wynik = rzad_b.przetworz_oprf_i_wydaj_kod(
            zaslepione_dane_oprf=zaslepione_prf,
            hash_tokenu=self.hash_tokenu,
            podpis_tokenu=self.podpis_tokenu,
            klucz_rzadu_a_e=self.klucz_rzadu_a_e,
            klucz_rzadu_a_n=self.klucz_rzadu_a_n,
        )

        if wynik["sukces"]:
            # Odślepiam wynik PRF (opcjonalnie — do dodatkowej weryfikacji)
            wynik_prf = rzad_b.oprf.klient_odslep(
                wynik["wynik_oprf"], self.czynnik_prf_r
            )

            self.kod = wynik["kod"]
            print(f"\n[Użytkownik] Otrzymałem kod: ★ {self.kod} ★")
            print(f"  Mogę go teraz przepisać na dowolnej stronie 18+")

        return wynik


class Strona18Plus:
    """STRONA 18+ — weryfikuje kod, nie zna tożsamości.

    WIDZI: 6-cyfrowy kod
    NIE WIDZI: tożsamości, PESELu, nic
    DOWIADUJE SIĘ: "wiek zweryfikowany" / "kod nieważny"
    """

    def __init__(self, nazwa="example-adult-site.pl"):
        self.nazwa = nazwa

    def zweryfikuj_uzytkownika(self, kod: str, rzad_b: RzadB_WydawcaKodow) -> bool:
        """Użytkownik wpisał kod — weryfikujemy go u Rządu B."""

        print(f"\n{'='*60}")
        print(f"STRONA 18+: {self.nazwa}")
        print(f"{'='*60}")
        print(f"\n[{self.nazwa}] Użytkownik wpisał kod: {kod}")
        print(f"  Odpytuję Rząd B o ważność...")

        wynik = rzad_b.zweryfikuj_kod(kod)

        if wynik["wazny"]:
            print(f"\n[{self.nazwa}] ✓ Wiek zweryfikowany! Przyznano dostęp.")
            print(f"  Nie wiem kim jest użytkownik — i nie muszę wiedzieć.")
        else:
            print(f"\n[{self.nazwa}] ✗ Kod odrzucony: {wynik['powod']}")

        return wynik["wazny"]


# ════════════════════════════════════════════════════════════════════
# CZĘŚĆ 3: Pełna symulacja
# ════════════════════════════════════════════════════════════════════

def wypisz_naglowek(tekst):
    szerokosc = 64
    print(f"\n{'█'*szerokosc}")
    print(f"█{tekst:^{szerokosc-2}}█")
    print(f"{'█'*szerokosc}")


def wypisz_analize_prywatnosci(rzad_a, rzad_b):
    """Analiza: co każdy podmiot wie po zakończeniu procesu."""

    wypisz_naglowek("ANALIZA PRYWATNOŚCI")

    print(f"""
┌─────────────────────────────────────────────────────────┐
│                    RZĄD A (mObywatel)                   │
├─────────────────────────────────────────────────────────┤
│ WIE:                                                    │
│  • Użytkownik o danym PESEL poprosił o weryfikację      │
│  • Użytkownik jest pełnoletni                           │
│                                                         │
│ NIE WIE (kryptograficznie):                             │
│  • Jaki token podpisał (ślepy podpis)                   │
│  • Jaki kod otrzymał użytkownik                         │
│  • Na jakiej stronie użytkownik użył kodu               │
│                                                         │
│ Dziennik Rządu A:""")
    for wpis in rzad_a.dziennik:
        print(f"│  {json.dumps(wpis, indent=2, default=str, ensure_ascii=False)[:55]}")
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
│  • Kim jest użytkownik (ślepy podpis → brak powiązania) │
│  • Jaki był oryginalny token (PRF → zaślepione dane)    │
│  • Jakie dane przetworzyła PRF (nieświadome obliczenie) │
│                                                         │
│ Dziennik Rządu B:""")
    for wpis in rzad_b.dziennik:
        print(f"│  {json.dumps(wpis, indent=2, default=str, ensure_ascii=False)[:55]}")
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
│ (to jest sedno ślepego podpisu!)                        │
│                                                         │
│ Nawet mając OBA dzienniki, NIE DA SIĘ powiązać wpisów   │
│ z Rządu A z wpisami z Rządu B.                          │
│                                                         │
│ Jedyny atak: korelacja czasowa przy małym ruchu.         │
│ Obrona: grupowe pobieranie tokenów z wyprzedzeniem      │
│ (użytkownik pobiera tokeny na zapas, losowo, w tle).    │
└─────────────────────────────────────────────────────────┘""")


def uruchom_demo():
    """Uruchamia pełną symulację systemu."""

    wypisz_naglowek("INICJALIZACJA SYSTEMU")

    # Inicjalizacja podmiotów rządowych
    rzad_a = RzadA_WeryfikatorWieku()
    rzad_b = RzadB_WydawcaKodow()

    # Strona 18+
    strona = Strona18Plus("example-adult.pl")

    # Użytkownik (PESEL z 1995 roku → 31 lat → pełnoletni)
    uzytkownik = Uzytkownik(pesel="95030112345", imie="Jan Kowalski")

    # ── KROK 1: Weryfikacja wieku + ślepy podpis ──
    wypisz_naglowek("KROK 1: WERYFIKACJA WIEKU (Rząd A)")
    wynik_a = uzytkownik.popros_o_slepy_podpis(rzad_a)

    if not wynik_a["sukces"]:
        print("Weryfikacja nieudana — koniec.")
        return

    # ── KROK 2: Anonimowy token → krótki kod ──
    wypisz_naglowek("KROK 2: WYDANIE KODU (Rząd B)")
    wynik_b = uzytkownik.pobierz_anonimowy_kod(rzad_b)

    if not wynik_b["sukces"]:
        print("Wydanie kodu nieudane — koniec.")
        return

    # ── KROK 3: Użycie kodu na stronie 18+ ──
    wypisz_naglowek("KROK 3: WERYFIKACJA NA STRONIE 18+")
    strona.zweryfikuj_uzytkownika(uzytkownik.kod, rzad_b)

    # ── KROK 4: Próba ponownego użycia (powinna się nie udać) ──
    wypisz_naglowek("KROK 4: PRÓBA PONOWNEGO UŻYCIA KODU (atak)")
    strona.zweryfikuj_uzytkownika(uzytkownik.kod, rzad_b)

    # ── Analiza prywatności ──
    wypisz_analize_prywatnosci(rzad_a, rzad_b)

    # ── Test: osoba niepełnoletnia ──
    wypisz_naglowek("TEST: OSOBA NIEPEŁNOLETNIA")
    niepelnoletni = Uzytkownik(pesel="10250154321", imie="Mały Jaś")  # 2010 → 16 lat
    wynik_niepelnoletni = niepelnoletni.popros_o_slepy_podpis(rzad_a)
    print(f"\n→ System poprawnie odrzucił niepełnoletniego: {wynik_niepelnoletni}")


if __name__ == "__main__":
    uruchom_demo()
