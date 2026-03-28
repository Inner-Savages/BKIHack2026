"""
Prymitywy kryptograficzne — wyciągnięte z age_verification_poc.py.
Używane przez routery FastAPI (gov_a, gov_b).
"""
import hashlib
import secrets


class ParaKluczyRSA:
    """Uproszczone RSA do demonstracji ślepych podpisów.

    W produkcji: użyj RSA-PSS z biblioteką typu `cryptography`.
    Tu: ręczna implementacja dla przejrzystości matematyki.
    UWAGA: 512 bitów to ZA MAŁO na produkcję (min. 2048).
    """

    def __init__(self, bity: int = 512):
        self.p = self._generuj_liczbe_pierwsza(bity // 2)
        self.q = self._generuj_liczbe_pierwsza(bity // 2)
        self.n = self.p * self.q
        self.phi = (self.p - 1) * (self.q - 1)
        self.e = 65537
        self.d = pow(self.e, -1, self.phi)

    def _generuj_liczbe_pierwsza(self, bity: int) -> int:
        while True:
            n = secrets.randbits(bity) | (1 << bity - 1) | 1
            if self._czy_prawdopodobnie_pierwsza(n):
                return n

    def _czy_prawdopodobnie_pierwsza(self, n: int, rundy: int = 20) -> bool:
        if n < 2:
            return False
        if n % 2 == 0:
            return n == 2
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

    Matematyka:
      1. Użytkownik: zaslepiona = m * r^e mod n
      2. Serwer:     slepy_podpis = zaslepiona^d mod n
      3. Użytkownik: podpis = slepy_podpis * r^-1 mod n
      4. Weryfikacja: podpis^e mod n == m
    """

    @staticmethod
    def podpisz_slepo(zaslepiona_wiadomosc: int, d: int, n: int) -> int:
        """Serwer podpisuje zaślepioną wiadomość. Nie widzi co podpisuje."""
        return pow(zaslepiona_wiadomosc, d, n)

    @staticmethod
    def zweryfikuj(hash_wiadomosci: int, podpis: int, e: int, n: int) -> bool:
        """Standardowa weryfikacja RSA."""
        return pow(podpis, e, n) == hash_wiadomosci


class NieswiadomaFunkcjaPRF:
    """Nieświadoma Funkcja Pseudolosowa (OPRF).

    F(k, x) = H(x)^k mod p

    Serwer nigdy nie widzi H(x) ani F(k, x):
      1. Klient: zaslepione = H(x)^r mod p
      2. Serwer: wynik = zaslepione^k mod p = H(x)^(r*k) mod p
      3. Klient: odslepy = wynik^(1/r) mod p = H(x)^k mod p
    """

    def __init__(self, bity: int = 256):
        self.q = self._znajdz_pierwsza(bity - 1)
        self.p = 2 * self.q + 1
        while not self._czy_pierwsza(self.p):
            self.q = self._znajdz_pierwsza(bity - 1)
            self.p = 2 * self.q + 1
        self.g = self._znajdz_generator()
        self.klucz_serwera = secrets.randbelow(self.q - 1) + 1

    def _znajdz_pierwsza(self, bity: int) -> int:
        while True:
            n = secrets.randbits(bity) | (1 << bity - 1) | 1
            if self._czy_pierwsza(n):
                return n

    def _czy_pierwsza(self, n: int, rundy: int = 20) -> bool:
        if n < 2:
            return False
        if n % 2 == 0:
            return n == 2
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

    def _znajdz_generator(self) -> int:
        while True:
            h = secrets.randbelow(self.p - 2) + 2
            g = pow(h, 2, self.p)
            if g != 1:
                return g

    def serwer_oblicz(self, zaslepione: int) -> int:
        """Serwer przetwarza zaślepione dane swoim kluczem. Nie widzi treści."""
        return pow(zaslepione, self.klucz_serwera, self.p)
