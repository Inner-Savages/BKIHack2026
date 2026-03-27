# Weryfikacja Wieku — Svelte App

Interaktywne demo anonimowej weryfikacji wieku oparte na ślepych podpisach RSA i Nieświadomej Funkcji Pseudolosowej (OPRF).

## Wymagania

- [Node.js](https://nodejs.org/) w wersji **18+**
- npm (dołączony do Node.js)

## Instalacja

```bash
cd svelte-app
npm install
```

## Uruchomienie (tryb deweloperski)

```bash
npm run dev
```

Aplikacja będzie dostępna pod adresem **http://localhost:5173**

## Budowanie wersji produkcyjnej

```bash
npm run build
```

Skompilowane pliki trafią do katalogu `dist/`.

## Podgląd wersji produkcyjnej

```bash
npm run preview
```

---

## Struktura projektu

```
svelte-app/
├── index.html
├── package.json
├── vite.config.js
└── src/
    ├── main.js                      # punkt wejścia
    ├── App.svelte                   # główny layout + globalne style
    ├── lib/
    │   ├── stores.js                # współdzielony stan (activeCodes)
    │   └── crypto.js                # pomocniki: generateCode, formatCode, kroki krypto
    └── components/
        ├── Phone.svelte             # symulator aplikacji mObywatel (3 ekrany)
        └── Site.svelte              # symulator strony 18+
```

## Jak działa demo

1. **Ekran 1 — mObywatel** — wyświetla kartę tożsamości Jana Kowalskiego. Kliknij „Generuj anonimowy token".
2. **Ekran 2 — Przetwarzanie** — animacja 7 kroków kryptograficznych:
   - zaślepienie tokenu (ślepy podpis RSA)
   - weryfikacja PESEL u Rządu A (mObywatel)
   - odślepienie podpisu
   - anonimowe żądanie do Rządu B (NASK)
   - przetworzenie OPRF
   - wygenerowanie 6-cyfrowego kodu
3. **Ekran 3 — Kod aktywny** — jednorazowy kod ważny przez **5 minut** z odliczaniem.
4. **Strona 18+** — wpisz kod z telefonu. Otrzymasz odpowiedź TAK/NIE bez żadnych danych osobowych.

## Gwarancje prywatności (symulowane)

| Podmiot   | Wie                              | Nie wie                              |
|-----------|----------------------------------|--------------------------------------|
| Rząd A    | tożsamość użytkownika            | treść tokenu, kod, strona docelowa   |
| Rząd B    | że ktoś ma 18+                   | kto to jest (matematycznie niemożliwe) |
| Strona    | kod → TAK/NIE                    | tożsamość, PESEL, źródło             |
