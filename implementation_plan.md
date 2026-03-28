# Rozbudowa PoC: Backend API + Frontend integracja

## Opis

Obecny demo działa w całości w przeglądarce — przez wspólny store Svelte symuluje komunikację między "telefonem" (mObywatel) a "stroną 18+". Celem jest zastąpienie tej symulacji prawdziwym backendem FastAPI, który eksponuje kryptografię z `age_verification_poc.py` przez REST API, a frontend komunikuje się z nim przy użyciu prawdziwych wywołań HTTP.

Kluczowe wyzwanie: **zaślepienie/odślepienie tokenu musi dziać się po stronie klienta** (inaczej backend widziałby zarówno tożsamość, jak i token — łamiąc model prywatności). Dlatego w frontendzie implementujemy arytmetykę BigInt RSA w JavaScript.

## User Review Required

> [!IMPORTANT]
> **Kryptografia kliencka (BigInt RSA w JS)**: Właściwy model prywatności wymaga, aby operacje zaślepienia (`m × r^e mod n`) i odślepienia (`sig × r⁻¹ mod n`) były wykonywane przez klienta. Implementujemy to w czystym JavaScript (BigInt). Jest to poprawne dla demo/PoC — w produkcji użyto by WebAssembly lub biblioteki jak `forge`.

> [!WARNING]
> **Jeden backend = dwie "służby"**: W demo Gov A i Gov B będą obsługiwane przez jeden serwer FastAPI na różnych routerach (`/gov-a/` i `/gov-b/`). W produkcji byłyby to oddzielne, izolowane serwisy. Dla hackathonu to akceptowalne uproszczenie.

## Proponowane zmiany

### 1. Backend — FastAPI

#### [NEW] `backend/main.py`
Główny plik serwera FastAPI z routerami. Startuje na porcie `8000`.

#### [NEW] `backend/gov_a.py` — Router Rządu A (mObywatel)
- `GET /gov-a/public-key` → `{e, n}` — klucz publiczny RSA do zaślepiania tokenów przez klienta
- `POST /gov-a/sign` → `{blind_signature}` — weryfikuje PESEL, podpisuje ślepo zaślepiony token

#### [NEW] `backend/gov_b.py` — Router Rządu B (NASK)
- `GET /gov-b/oprf-params` → `{p, g}` — publiczne parametry OPRF
- `POST /gov-b/oprf-eval` → `{result}` — przetwarza zaślepione dane OPRF kluczem serwera
- `POST /gov-b/issue-code` → `{code, expires_in}` — weryfikuje podpis Gov A, wystawia 6-cyfrowy kod
- `POST /gov-b/verify-code` → `{valid, reason}` — weryfikuje kod (używane przez Stronę 18+), spala po użyciu

#### [NEW] `backend/crypto_core.py`
Refaktoryzacja klas z `age_verification_poc.py` — wyodrębnione prymitywy kryptograficzne (`ParaKluczyRSA`, `SlepyRSA`, `NieswiadomaFunkcjaPRF`) użyte przez routery. Logika biznesowa przeniesiona do routerów.

#### [NEW] `backend/requirements.txt`
```
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
```

---

### 2. Frontend — nowe pliki

#### [NEW] `svelte-app/src/lib/bigint-rsa.js`
Implementacja operacji RSA w BigInt po stronie klienta:
- `blindToken(hashHex, eHex, nHex)` → `{blinded, r}` — zaślepienie
- `unblind(blindSigHex, rBigInt, nHex)` → `sigHex` — odślepienie
- `sha256ToBigInt(data)` → BigInt — haszowanie tokenu

#### [MODIFY] `svelte-app/src/lib/crypto.js`
Zastąpienie symulowanych kroków prawdziwymi wywołaniami `fetch()` do backendu. Nowe eksporty:
- `fetchPublicKey()` — `GET /gov-a/public-key`
- `requestBlindSign(pesel, blindedHex)` — `POST /gov-a/sign`
- `requestCode(tokenHashHex, sigHex, eHex, nHex)` — `POST /gov-b/issue-code`
- `verifyCode(code)` — `POST /gov-b/verify-code`

#### [MODIFY] `svelte-app/src/lib/stores.js`
Usunięcie `activeCodes` store (nie potrzeby — weryfikacja kodu odbywa się przez API).

#### [MODIFY] `svelte-app/src/components/Phone.svelte`
Zastąpienie symulacji (`buildCryptoSteps()` z fake danymi) prawdziwym przepływem async:
1. Pobierz klucz publiczny z `/gov-a/public-key`
2. Wygeneruj token, zaślep go w JS (BigInt)
3. Wyślij PESEL + zaślepiony token do `/gov-a/sign`
4. Odślep podpis w JS
5. Wyślij token + podpis do `/gov-b/issue-code`
6. Wyświetl prawdziwy kod z backendu

#### [MODIFY] `svelte-app/src/components/Site.svelte`
Zastąpienie weryfikacji przez store prawdziwym wywołaniem `POST /gov-b/verify-code`. Usunięcie importu `activeCodes`.

---

### 3. Konfiguracja

#### [MODIFY] `svelte-app/vite.config.js`
Dodanie proxy dla `/api` → `http://localhost:8000` (no-CORS w dev).

#### [NEW] `backend/start.sh`
Skrypt startowy backendu.

## Diagram przepływu po zmianach

```
[Phone.svelte]                    [FastAPI Backend]           [Site.svelte]
     │                                   │                         │
     │── GET /gov-a/public-key ─────────►│                         │
     │◄── {e, n} ───────────────────────-│                         │
     │                                   │                         │
     │ (BigInt w JS: blindToken)         │                         │
     │                                   │                         │
     │── POST /gov-a/sign ──────────────►│ (Gov A: weryfikuje PESEL│
     │   {pesel, blinded_hex}            │  podpisuje ślepo)       │
     │◄── {blind_sig_hex} ──────────────-│                         │
     │                                   │                         │
     │ (BigInt w JS: unblind)            │                         │
     │                                   │                         │
     │── POST /gov-b/issue-code ────────►│ (Gov B: weryfikuje      │
     │   {token_hash, sig, e, n}         │  podpis, wystawia kod)  │
     │◄── {code: "123456"} ─────────────-│                         │
     │                                   │                         │
     │ [wyświetla kod użytkownikowi]      │                         │
     │                                   │                         │
     │                                   │◄── POST /gov-b/verify ──│
     │                                   │    {code: "123456"}     │
     │                                   │── {valid: true} ───────►│
```

## Open Questions

> [!NOTE]
> Frontend generuje teraz prawdziwe losowe tokeny i wykonuje prawdziwe RSA blind signatures w BigInt JS. Klucz RSA jest 512-bitowy (jak w PoC) — wystarczy dla demo, szybkie generowanie przy starcie serwera.

> [!NOTE]
> PESEL jest hardcoded w `Phone.svelte` jako `"95030112345"` — czy chcesz dodać input field żeby użytkownik mógł wpisać dowolny PESEL? (Opcjonalne ulepszenie UX)

## Plan weryfikacji

### Testy automatyczne
- Istniejące testy w `tests/` powinny nadal przechodzić (kod Python niezmieniony w logice)
- `python -m pytest tests/ -v`

### Testy manualne (przeglądarka)
1. Uruchomić backend: `uvicorn backend.main:app --reload`
2. Uruchomić frontend: `cd svelte-app && npm run dev`
3. Kliknąć "Generuj anonimowy token" — dziennik powinien pokazywać prawdziwe hex-stringi z backendu
4. Skopiować kod i wpisać na Stronie 18+ — API powinno zwrócić odpowiedź
5. Wpisać kod ponownie — powinno zwrócić "Kod już wykorzystany"
