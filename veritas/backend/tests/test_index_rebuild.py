"""Test real FAISS replacement with deterministic, offline embeddings."""

import hashlib
import json
from pathlib import Path
from typing import Any, NoReturn

import numpy as np
import pytest
from numpy.typing import NDArray

from app.config import EMBED_DIM
from app.services import retriever as retriever_module


def deterministic_encode(
    texts: list[str], batch_size: int = 64, show_progress: bool = False
) -> NDArray[np.float32]:
    """Map text to repeatable unit vectors without loading an ML model."""
    vectors: NDArray[np.float32] = np.empty((len(texts), EMBED_DIM), dtype=np.float32)
    for row, text in enumerate(texts):
        digest: bytes = hashlib.shake_256(text.encode("utf-8")).digest(EMBED_DIM)
        vector: NDArray[np.float32] = (
            np.frombuffer(digest, dtype=np.uint8).astype(np.float32) - 127.5
        )
        vectors[row] = vector / np.linalg.norm(vector)
    return vectors


def test_index_rebuild_replaces_vectors_and_chunks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rebuilding replaces both artifacts and restarts chunk IDs from zero."""
    monkeypatch.setattr(retriever_module, "encode", deterministic_encode)

    def forbidden_model(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Index rebuild tests must not load a real model")

    monkeypatch.setattr(retriever_module, "get_model", forbidden_model)

    old_chunks: list[dict[str, Any]] = [
        {"source": "old.pdf", "page": row + 1, "text": f"Old-only passage {row}."}
        for row in range(6)
    ]
    assert retriever_module.Retriever.build(old_chunks, tmp_path) == 6
    original = retriever_module.Retriever(tmp_path)
    assert original.index.ntotal == 6
    first_results = original.search(old_chunks[0]["text"], top_k=10)
    assert len(first_results) == 6
    assert first_results[0][0]["text"] == old_chunks[0]["text"]

    new_chunks: list[dict[str, Any]] = [
        {"source": "new.pdf", "page": row + 1, "text": f"New-only passage {row}."}
        for row in range(3)
    ]
    assert retriever_module.Retriever.build(new_chunks, tmp_path) == 3
    rebuilt = retriever_module.Retriever(tmp_path)
    assert rebuilt.index.ntotal == 3
    assert rebuilt.index.d == EMBED_DIM

    with (tmp_path / "chunks.json").open("r", encoding="utf-8") as handle:
        stored: list[dict[str, Any]] = json.load(handle)
    expected: list[dict[str, Any]] = [
        {**chunk, "chunk_id": row} for row, chunk in enumerate(new_chunks)
    ]
    assert stored == rebuilt.chunks == expected
    old_texts: set[str] = {chunk["text"] for chunk in old_chunks}
    assert old_texts.isdisjoint(chunk["text"] for chunk in stored)
    assert [chunk["chunk_id"] for chunk in stored] == [0, 1, 2]

    expected_vectors = deterministic_encode([chunk["text"] for chunk in new_chunks])
    np.testing.assert_allclose(
        rebuilt.index.reconstruct_n(0, len(new_chunks)),
        expected_vectors,
        rtol=0,
        atol=1e-7,
    )

    results = rebuilt.search(new_chunks[0]["text"], top_k=10)
    assert len(results) == 3
    assert results[0][0]["text"] == new_chunks[0]["text"]
    assert all(chunk["source"] == "new.pdf" for chunk, _ in results)
    assert all(chunk["text"] not in old_texts for chunk, _ in results)