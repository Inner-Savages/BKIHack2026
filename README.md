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

## Analogia z życia codziennego

> Wyobraź sobie, że wkładasz kartkę do **nieprzezroczystej koperty z kalką**. Urzędnik sprawdza Twój dowód, podpisuje kopertę (podpis przechodzi przez kalkę na kartkę). Otwierasz kopertę — masz kartkę z podpisem urzędnika, ale **urzędnik nigdy nie widział co było na kartce**. Pokazujesz kartkę w innym okienku, dostajesz kod. Drugie okienko wie, że podpis jest prawdziwy, ale **nie wie kto stał w pierwszym okienku**.

## Uruchomienie demo

```bash
python3 age_verification_poc.py
```

Wymagania: Python 3.8+ (bez zewnętrznych bibliotek).
