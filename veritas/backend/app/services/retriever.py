"""Persist and search normalized embeddings with FAISS inner product."""

import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from numpy.typing import NDArray

from app.config import EMBED_DIM, INDEX_DIR, MODEL_NAME
from app.services.embedder import encode, get_model


def _encode_for_model(texts: list[str], model_name: str) -> NDArray[np.float32]:
    """Honor the selected model while enforcing the shared vector contract."""
    if model_name == MODEL_NAME:
        return encode(texts)

    vectors: NDArray[np.float32] = np.ascontiguousarray(
        get_model(model_name).encode(
            texts,
            batch_size=64,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ),
        dtype=np.float32,
    )
    if vectors.shape != (len(texts), EMBED_DIM):
        raise ValueError(f"Expected embeddings with shape ({len(texts)}, {EMBED_DIM})")
    return vectors


class Retriever:
    """Load a saved chunk index and return cosine-ranked search results."""

    def __init__(
        self, index_dir: Path = INDEX_DIR, model_name: str = MODEL_NAME
    ) -> None:
        """Load both artifacts and verify vector dimensions and row counts."""
        self.index_dir: Path = index_dir
        self.model_name: str = model_name
        index_path: Path = index_dir / "faiss.index"
        chunks_path: Path = index_dir / "chunks.json"
        if not index_path.is_file() or not chunks_path.is_file():
            raise FileNotFoundError(
                f"Missing faiss.index or chunks.json in {index_dir}. "
                "From backend/, run: python scripts/build_index.py "
                f'--index-dir "{index_dir}"'
            )

        self.index: faiss.Index = faiss.read_index(str(index_path))
        with chunks_path.open("r", encoding="utf-8") as handle:
            self.chunks: list[dict[str, Any]] = json.load(handle)

        assert self.index.ntotal == len(self.chunks), "Index/chunk count mismatch"
        assert self.index.d == EMBED_DIM, f"Index dimension must be {EMBED_DIM}"

    @staticmethod
    def build(
        chunks: list[dict[str, Any]],
        index_dir: Path,
        model_name: str = MODEL_NAME,
    ) -> int:
        """Build and overwrite both artifacts with contiguous chunk IDs."""
        if not chunks:
            raise ValueError("Cannot build an index from an empty chunk list")

        indexed_chunks: list[dict[str, Any]] = [
            {**chunk, "chunk_id": row} for row, chunk in enumerate(chunks)
        ]
        texts: list[str] = [chunk["text"] for chunk in indexed_chunks]
        vectors: NDArray[np.float32] = _encode_for_model(texts, model_name)

        # Inner product on L2-normalized vectors equals cosine similarity.
        index: faiss.IndexFlatIP = faiss.IndexFlatIP(EMBED_DIM)
        index.add(vectors)
        index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(index_dir / "faiss.index"))
        with (index_dir / "chunks.json").open("w", encoding="utf-8") as handle:
            json.dump(indexed_chunks, handle, ensure_ascii=False, indent=2)

        return len(indexed_chunks)

    def search(self, query: str, top_k: int) -> list[tuple[dict[str, Any], float]]:
        """Return up to top_k chunks ordered by decreasing cosine score."""
        if not query.strip():
            raise ValueError("query must not be blank")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        count: int = min(top_k, self.index.ntotal)
        if count == 0:
            return []

        query_vector: NDArray[np.float32] = _encode_for_model(
            [query.strip()], self.model_name
        )
        scores, row_ids = self.index.search(query_vector, count)
        results: list[tuple[dict[str, Any], float]] = [
            (self.chunks[int(row)], float(score))
            for row, score in zip(row_ids[0], scores[0], strict=True)
            if row != -1
        ]
        results.sort(key=lambda result: result[1], reverse=True)
        return results
