"""Shared configuration for the VERITAS backend."""

import os as _os
from pathlib import Path as _Path

BASE_DIR: _Path = _Path(__file__).resolve().parent.parent
PDF_DIR: _Path = BASE_DIR / "data" / "pdfs"
INDEX_DIR: _Path = BASE_DIR / "data" / "index"
MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM: int = 384
WINDOW_WORDS: int = 180
STRIDE_WORDS: int = 120
MIN_CHUNK_WORDS: int = 30
TAU_MIN: float = 0.20
TAU_MAX: float = 0.95
DEFAULT_TAU: float = 0.35
DEFAULT_TOP_K: int = 5
JWT_SECRET: str = _os.environ.get("VERITAS_JWT_SECRET", "dev-only-change-me")
JWT_ALGO: str = "HS256"
TOKEN_TTL_HOURS: int = 2
CORS_ORIGINS: list[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5187",
    "http://127.0.0.1:5187",
]
