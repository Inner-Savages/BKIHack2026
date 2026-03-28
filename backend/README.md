# Anonimowa Weryfikacja Wieku — Backend API

Serwer FastAPI obsługujący logikę kryptograficzną dla systemu anonimowej weryfikacji pełnoletności. Implementuje rozdzielenie ról między dwa podmioty rządowe (Gov A i Gov B) przy zachowaniu matematycznych gwarancji prywatności.

## Technologie

- **Python 3.8+**
- **FastAPI** — framework webowy
- **Uvicorn** — serwer ASGI
- **Pydantic** — walidacja danych

## Szybki start

### 1. Instalacja zależności

```bash
cd backend
pip install -r requirements.txt
```

### 2. Uruchomienie serwera

```bash
uvicorn main:app --reload --port 8000
```

Serwer będzie dostępny pod adresem: [http://localhost:8000](http://localhost:8000)
Dokumentacja Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

## Architektura API

Backend jest podzielony na dwa główne routery symulujące niezależne instytucje:

### Gov A (mObywatel) — `/gov-a`
Odpowiada za weryfikację tożsamości i wieku.
- `GET /gov-a/public-key`: Zwraca klucz publiczny RSA używany przez klienta do zaślepiania.
- `POST /gov-a/sign`: Przyjmuje PESEL i zaślepiony token. Zwraca ślepy podpis.

### Gov B (NASK) — `/gov-b`
Odpowiada za wydawanie i weryfikację anonimowych kodów.
- `GET /gov-b/oprf-params`: Zwraca parametry grupy dla OPRF.
- `POST /gov-b/issue-code`: Przyjmuje anonimowy token z podpisem Gov A. Weryfikuje podpis i wystawia 6-cyfrowy kod.
- `POST /gov-b/verify-code`: Punkt styku dla zewnętrznych stron (np. 18+). Sprawdza ważność kodu i "spala" go po użyciu.

## Model Prywatności

System wykorzystuje:
1. **Ślepe Podpisy RSA (RSA Blind Signatures)**: Gov A podpisuje token nie widząc jego zawartości.
2. **OPRF (Oblivious Pseudo-Random Function)**: Gov B przetwarza dane bez powiązania ich z tożsamością.
3. **Kliencką Kryptografię**: Zaślepianie i odślepianie odbywa się wyłącznie w przeglądarce użytkownika.

Nawet zmowa obu podmiotów rządowych (Gov A + Gov B) nie pozwala na powiązanie tożsamości (PESEL) z konkretnym wygenerowanym kodem lub stroną, na której został użyty.
