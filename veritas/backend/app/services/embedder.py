"""Load MiniLM once and produce normalized float32 embeddings."""

from functools import lru_cache

import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

from app.config import EMBED_DIM, MODEL_NAME


@lru_cache(maxsize=None)
def get_model(model_name: str = MODEL_NAME) -> SentenceTransformer:
    """Return one cached sentence-transformer instance per model name."""
    return SentenceTransformer(model_name)


def encode(
    texts: list[str], batch_size: int = 64, show_progress: bool = False
) -> NDArray[np.float32]:
    """Encode texts as an (n, 384) array of L2-normalized float32 vectors."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")
    if not texts:
        return np.empty((0, EMBED_DIM), dtype=np.float32)

    vectors: NDArray[np.float32] = np.ascontiguousarray(
        get_model().encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ),
        dtype=np.float32,
    )
    if vectors.shape != (len(texts), EMBED_DIM):
        raise ValueError(f"Expected embeddings with shape ({len(texts)}, {EMBED_DIM})")
    return vectors
