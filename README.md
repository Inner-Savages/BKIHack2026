# Anonimowa Weryfikacja Wieku

System pozwala udowodnić stronie internetowej, że masz 18+ lat, **bez ujawniania kim jesteś**.

## Jak to działa?

Trzy podmioty, z których **żaden nie wie wszystkiego**:

| Kto | Co wie | Czego nie wie |
|-----|--------|---------------|
| **mObywatel** (Rząd A) | Kim jesteś i ile masz lat | Jakiego kodu użyjesz ani gdzie |
| **NASK** (Rząd B) | Że ktoś anonimowy ma 18+ | Kim jest ta osoba |
| **Strona 18+** | Że wpisany kod jest ważny | Kim jest użytkownik |

## Przepływ krok po kroku

```mermaid
sequenceDiagram
    participant U as 👤 Użytkownik
    participant A as 🏛️ mObywatel<br/>(Rząd A)
    participant B as 🏛️ NASK<br/>(Rząd B)
    participant S as 🌐 Strona 18+

    Note over U: Chcę wejść na stronę 18+<br/>ale nie chcę podawać<br/>kim jestem

    rect rgb(232, 245, 233)
        Note over U,A: KROK 1 — Potwierdzenie wieku
        U->>U: Generuję losowy "bilet"<br/>i chowam go w kopercie<br/>(zaślepiam kryptograficznie)
        U->>A: Oto mój PESEL + zaklejona koperta
        A->>A: Sprawdzam PESEL → 18+? ✓<br/>Podpisuję kopertę<br/>NIE WIEM co jest w środku
        A->>U: Podpisana koperta 🔏
        U->>U: Otwieram kopertę →<br/>mam bilet z podpisem rządu!<br/>Rząd A nigdy go nie widział
    end

    rect rgb(227, 242, 253)
        Note over U,B: KROK 2 — Pobranie kodu
        U->>B: Oto bilet z podpisem Rządu A<br/>(bez PESELu, bez imienia!)
        B->>B: Podpis Rządu A ważny? ✓<br/>Ktoś anonimowy ma 18+<br/>Generuję kod: 931129
        B->>U: Twój jednorazowy kod: 931129<br/>Ważny 5 minut ⏱️
    end

    rect rgb(255, 243, 224)
        Note over U,S: KROK 3 — Wejście na stronę
        U->>S: Wpisuję kod: 931129
        S->>B: Czy kod 931129 jest ważny?
        B->>S: TAK ✓ (kod spalony)
        S->>U: Dostęp przyznany! 🔓<br/>Nie wiem kim jesteś
    end

    rect rgb(252, 228, 236)
        Note over U,S: Próba ponownego użycia
        U->>S: Wpisuję kod: 931129 (ponownie)
        S->>B: Czy kod 931129 jest ważny?
        B->>S: NIE ✗ — już użyty
        S->>U: Odmowa dostępu 🔒
    end
```

## Dlaczego to jest bezpieczne?

```mermaid
graph LR
    subgraph "🏛️ mObywatel wie"
        A1[Kim jesteś]
        A2[Ile masz lat]
    end

    subgraph "🏛️ NASK wie"
        B1[Że ktoś ma 18+]
        B2[Jaki kod wydał]
    end

    subgraph "🌐 Strona wie"
        S1[Że kod był ważny]
    end

    A1 -.-x|nie da się połączyć| B1
    B2 -.-x|nie da się połączyć| A1
    S1 -.-x|nie da się połączyć| A1

    style A1 fill:#c8e6c9
    style A2 fill:#c8e6c9
    style B1 fill:#bbdefb
    style B2 fill:#bbdefb
    style S1 fill:#ffe0b2
```

**Nawet gdyby oba urzędy połączyły swoje dane** — matematycznie nie da się powiązać osoby z kodem, ponieważ "koperta" (blind signature) sprawia, że podpisany bilet wygląda zupełnie inaczej niż to, co widział mObywatel.

## Warstwy ochrony prywatności

System nie polega na jednym mechanizmie — stosuje **cztery niezależne warstwy**, z których każda samodzielnie chroni użytkownika. Żeby deanonimizować kogokolwiek, trzeba by złamać **wszystkie naraz**.

```mermaid
graph TB
    subgraph "🔒 Warstwa 1: Separacja prawna"
        P1[Dwa oddzielne resorty rządowe]
        P2[Ustawowy zakaz wymiany danych]
        P3[Odpowiedzialność karna za zmowę]
    end

    subgraph "🔐 Warstwa 2: Ślepe podpisy RSA"
        K1[Rząd A podpisuje kopertę<br/>nie widząc zawartości]
        K2[Rząd B widzi podpis<br/>ale nie wie czyj]
        K3[Zaślepiony token ≠ odślepiony token]
    end

    subgraph "🧮 Warstwa 3: OPRF"
        O1[Serwer przetwarza dane<br/>których nigdy nie widział]
        O2[Nawet logi są bezużyteczne —<br/>dane przeszły zaślepione]
        O3[Matematycznie niemożliwa<br/>deanonimizacja]
    end

    subgraph "🖥️ Warstwa 4: Enklawy sprzętowe TEE"
        T1[Intel SGX / ARM TrustZone / AMD SEV]
        T2[Kod open-source + remote attestation]
        T3[Nawet administrator serwera<br/>nie widzi co dzieje się w środku]
    end

    P1 ~~~ K1
    K1 ~~~ O1
    O1 ~~~ T1

    style P1 fill:#e8f5e9
    style P2 fill:#e8f5e9
    style P3 fill:#e8f5e9
    style K1 fill:#e3f2fd
    style K2 fill:#e3f2fd
    style K3 fill:#e3f2fd
    style O1 fill:#fff3e0
    style O2 fill:#fff3e0
    style O3 fill:#fff3e0
    style T1 fill:#fce4ec
    style T2 fill:#fce4ec
    style T3 fill:#fce4ec
```

### Warstwa 1: Separacja architektoniczna + prawna

Dwa oddzielne systemy rządowe, prowadzone przez **różne resorty** (np. Ministerstwo Cyfryzacji i NASK), z **ustawowym zakazem wymiany danych** — tak jak dziś tajemnica skarbowa i tajemnica lekarska istnieją w ramach tego samego państwa, ale łamanie bariery między nimi jest przestępstwem.

- **Podmiot A** (np. MC) weryfikuje wiek
- **Podmiot B** (np. NASK) wydaje kody
- Komunikują się **wyłącznie przez ślepy podpis** — A podpisuje nie widząc co, B widzi podpis ale nie wie czyj

> Ograniczenie: wymaga zaufania instytucjonalnego. Zmowa jest nielegalna, ale technicznie możliwa — dlatego potrzebujemy kolejnych warstw.

### Warstwa 2: Ślepe podpisy RSA

Nawet gdyby oba resorty **chciały** połączyć dane, zaślepiony token który widział Rząd A wygląda zupełnie inaczej niż odślepiony token który widzi Rząd B. Matematycznie nie da się ich ze sobą powiązać bez znajomości losowego czynnika zaślepiającego, który zna **wyłącznie użytkownik**.

### Warstwa 3: Nieświadoma Funkcja Pseudolosowa (OPRF)

To jest najsilniejsza warstwa. Oba systemy mogą stać **na tych samych serwerach rządowych**, a i tak matematycznie nie da się powiązać użytkownika z kodem.

Jak to działa:
1. Serwer B ma swój sekretny klucz `k`
2. Użytkownik wysyła **zaślepioną** wartość
3. Serwer przetwarza ją kluczem `k` — ale **nie widzi ani wejścia, ani wyjścia**
4. Użytkownik odślepia wynik i dostaje deterministyczny token

Serwer B wykonał obliczenie na danych, **których nigdy nie widział**. Nawet gdyby ktoś z B chciał deanonimizować — nie ma czego logować, bo dane przeszły w formie kryptograficznie zaślepionej.

### Warstwa 4: Enklawy sprzętowe (TEE)

Podmiot B może dodatkowo działać w **enklawie sprzętowej** (Intel SGX / ARM TrustZone / AMD SEV):

- Kod jest **open-source** i publicznie audytowalny
- Uruchamia się w sprzętowej enklawie z **remote attestation** — każdy może zweryfikować, że działa dokładnie ten kod i nic innego
- **Nawet administrator serwera, nawet minister, nawet ABW z fizycznym dostępem do maszyny** nie mogą podejrzeć co się dzieje w środku

### Rekomendacja: wszystkie warstwy razem

To jest podejście "pasek i szelki":

| Warstwa | Co gwarantuje | Rodzaj gwarancji |
|---------|---------------|------------------|
| **Separacja prawna** | Wymiana danych = przestępstwo | Prawna |
| **Ślepe podpisy** | Nie da się powiązać tokenów | Matematyczna |
| **OPRF** | Serwer nie widzi przetwarzanych danych | Matematyczna |
| **TEE** | Kod robi dokładnie to co deklaruje | Sprzętowa |
| **Open-source** | Brak ukrytych backdoorów | Społeczna (audyt) |

**Nawet jeśli jedno zabezpieczenie zawiedzie, pozostałe trzymają.** Żeby deanonimizować użytkownika, trzeba by **jednocześnie**: złamać matematykę OPRF, zhackować enklawę sprzętową, obejść audyt open-source i złamać prawo. To jest praktycznie niemożliwe.

## Analogia z życia codziennego

> Wyobraź sobie, że wkładasz kartkę do **nieprzezroczystej koperty z kalką**. Urzędnik sprawdza Twój dowód, podpisuje kopertę (podpis przechodzi przez kalkę na kartkę). Otwierasz kopertę — masz kartkę z podpisem urzędnika, ale **urzędnik nigdy nie widział co było na kartce**. Pokazujesz kartkę w innym okienku, dostajesz kod. Drugie okienko wie, że podpis jest prawdziwy, ale **nie wie kto stał w pierwszym okienku**.

## Uruchomienie demo

```bash
python3 age_verification_poc.py
```

Wymagania: Python 3.8+ (bez zewnętrznych bibliotek).
