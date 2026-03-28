"""
Główna aplikacja FastAPI — Anonimowa Weryfikacja Wieku.

Uruchomienie:
  uvicorn backend.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .gov_a import router as gov_a_router
from .gov_b import router as gov_b_router

app = FastAPI(
    title="Anonimowa Weryfikacja Wieku — API",
    description=(
        "Backend systemu anonimowej weryfikacji pełnoletności. "
        "Gov A (mObywatel): weryfikuje wiek i ślepo podpisuje tokeny. "
        "Gov B (NASK): wystawia i weryfikuje jednorazowe kody dostępu."
    ),
    version="0.1.0",
)

# CORS — w dev zezwalamy na wszystko (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(gov_a_router)
app.include_router(gov_b_router)


@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}
