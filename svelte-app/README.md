# Weryfikacja Wieku — Svelte App

Interaktywne demo anonimowej weryfikacji wieku oparte na rzeczywistej kryptografii (RSA Blind Signatures) i komunikacji z backendem FastAPI.

## Wymagania

- **Node.js 18+**
- **npm** (dołączony do Node.js)
- **Uruchomiony [backend](../backend/README.md)** (wymagany do działania kryptografii i wydawania kodów)

## Instalacja

```bash
cd svelte-app
npm install
```

## Uruchomienie (tryb deweloperski)

```bash
npm run dev
```

Aplikacja będzie dostępna pod adresem: **http://localhost:5173** (lub innym wskazanym przez Vite).  
**Ważne:** Vite jest skonfigurowany z proxy (`/api` → `localhost:8000`), aby umożliwić bezproblemową komunikację z backendem bez problemów z CORS.

## Struktura projektu

- `src/lib/bigint-rsa.js`: Kliencka implementacja ślepych podpisów RSA przy użyciu BigInt.  
- `src/lib/crypto.js`: Warstwa API komunikująca się z backendem i koordynująca kroki kryptograficzne.  
- `src/lib/stores.js`: Przechowuje ostatnio wygenerowany kod dla wygody dema.  
- `src/components/Phone.svelte`: Interfejs mObywatela wykonujący operacje kryptograficzne (zaślepianie/odślepianie).  
- `src/components/Site.svelte`: Interfejs strony 18+ weryfikującej kod przez API.

## Jak działa demo (wersja API)

1. **Zaślepienie (Klient)**: Przeglądarka pobiera klucz publiczny RSA Gov A i generuje losowy token. Następnie zaślepia go lokalnie (Gov A nigdy nie zobaczy oryginalnych danych).
2. **Podpisanie (Gov A)**: Serwer Gov A weryfikuje PESEL i ślepo podpisuje zaślepiony token.
3. **Odślepienie (Klient)**: Przeglądarka odślepia podpis Gov A, uzyskując ważny dowód pełnoletności na oryginalnym tokenie.
4. **Wydanie Kodu (Gov B)**: Przeglądarka przesyła anonimowy token z podpisem do Gov B. Serwer Gov B wydaje 6-cyfrowy kod z czasem życia 5 minut.
5. **Weryfikacja (Strona)**: Kod jest wpisywany na zewnętrznej stronie, która odpytuje Gov B o jego ważność.

## Gwarancje prywatności

System zapewnia matematyczne odizolowanie tożsamości od faktu weryfikacji wieku na konkretnej stronie. Ślepy podpis RSA gwarantuje, że podmiot weryfikujący tożsamość (Gov A) nigdy nie dowiedzie się, jaki kod otrzymał użytkownik.
