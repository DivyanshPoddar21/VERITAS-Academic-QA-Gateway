"""Exercise real MiniLM embeddings and FAISS persistence on a tiny corpus."""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from app.config import EMBED_DIM
from app.services.embedder import encode, get_model
from app.services.retriever import Retriever


@pytest.fixture(scope="module")
def chunks() -> list[dict[str, Any]]:
    """Provide eight academic chunks across three distinct topics."""
    texts: list[str] = [
        "Gradient descent minimizes a loss function by repeatedly updating model "
        "parameters in the direction of the negative gradient.",
        "The learning rate controls the step size of gradient descent. A large "
        "learning rate can overshoot the minimum and cause divergence.",
        "Stochastic gradient descent estimates the gradient from one training "
        "example. Mini-batch training uses a small group of examples per update.",
        "A decision tree predicts outcomes by splitting data at internal nodes "
        "using feature conditions. Leaf nodes contain final predictions.",
        "Decision tree classification uses Gini impurity or information gain "
        "to choose a feature split that separates class labels.",
        "Pruning removes branches from a decision tree to reduce overfitting "
        "and improve generalization on unseen examples.",
        "Photosynthesis converts light energy into chemical energy in plants. "
        "Chlorophyll absorbs sunlight in chloroplasts.",
        "During photosynthesis, plants use carbon dioxide and water to produce "
        "sugars and release oxygen. The Calvin cycle fixes carbon.",
    ]
    return [
        {"source": "course.pdf", "page": row // 3 + 1, "text": text}
        for row, text in enumerate(texts)
    ]


@pytest.fixture(scope="module")
def saved_index(
    tmp_path_factory: pytest.TempPathFactory, chunks: list[dict[str, Any]]
) -> Path:
    """Build once with the real model; reuse the artifacts across tests."""
    directory: Path = tmp_path_factory.mktemp("retriever")
    assert Retriever.build(chunks, directory) == len(chunks)
    return directory


def test_persistence_and_reload(
    saved_index: Path, chunks: list[dict[str, Any]]
) -> None:
    """Both artifacts persist and reload with the original chunk metadata."""
    assert (saved_index / "faiss.index").is_file()
    assert (saved_index / "chunks.json").is_file()
    retriever: Retriever = Retriever(saved_index)
    assert retriever.index.ntotal == len(chunks)
    assert retriever.index.d == EMBED_DIM
    assert retriever.chunks == [
        {**chunk, "chunk_id": row} for row, chunk in enumerate(chunks)
    ]


def test_gradient_descent_ranks_first(saved_index: Path) -> None:
    """A definition query retrieves the matching gradient-descent chunk first."""
    results = Retriever(saved_index).search(
        "How does gradient descent minimize loss using the negative gradient?", 3
    )
    assert len(results) == 3
    chunk, score = results[0]
    assert chunk["chunk_id"] == 0
    assert 0.0 <= score <= 1.0


def test_scores_are_sorted(saved_index: Path) -> None:
    """Search scores appear in descending order."""
    results = Retriever(saved_index).search("decision tree feature splits", 8)
    scores: list[float] = [score for _, score in results]
    assert scores == sorted(scores, reverse=True)


def test_top_k_exceeds_corpus(saved_index: Path) -> None:
    """An oversized top_k returns each available row once without sentinels."""
    retriever: Retriever = Retriever(saved_index)
    results = retriever.search("photosynthesis in plants", 100)
    assert len(results) == retriever.index.ntotal
    assert len({chunk["chunk_id"] for chunk, _ in results}) == len(results)


def test_chunk_ids_match_rows(saved_index: Path) -> None:
    """Persisted chunk IDs equal their zero-based vector row positions."""
    with (saved_index / "chunks.json").open("r", encoding="utf-8") as handle:
        stored_chunks: list[dict[str, Any]] = json.load(handle)
    assert [chunk["chunk_id"] for chunk in stored_chunks] == list(
        range(len(stored_chunks))
    )


def test_missing_index(tmp_path: Path) -> None:
    """Missing artifacts explain how to build the index."""
    with pytest.raises(FileNotFoundError, match=r"scripts/build_index\.py"):
        Retriever(tmp_path / "missing")


def test_empty_build(tmp_path: Path) -> None:
    """Building an empty corpus fails before loading a model."""
    with pytest.raises(ValueError, match="empty chunk list"):
        Retriever.build([], tmp_path)


@pytest.mark.parametrize("query", ["", " ", "\n\t"])
def test_blank_query(saved_index: Path, query: str) -> None:
    """Blank queries are rejected."""
    with pytest.raises(ValueError, match="blank"):
        Retriever(saved_index).search(query, 3)


def test_encode_contract() -> None:
    """Embeddings are contiguous float32 unit vectors with 384 dimensions."""
    vectors = encode(["Gradient descent optimizes model parameters.", "Plants grow."])
    assert vectors.shape == (2, EMBED_DIM)
    assert vectors.dtype == np.float32
    assert vectors.flags.c_contiguous
    np.testing.assert_allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-6)
    assert get_model() is get_model()


def test_empty_encode() -> None:
    """An empty input preserves the embedding array shape and dtype."""
    vectors = encode([])
    assert vectors.shape == (0, EMBED_DIM)
    assert vectors.dtype == np.float32


def test_rebuild_overwrites(
    tmp_path: Path, chunks: list[dict[str, Any]]
) -> None:
    """Rebuilding replaces old rows rather than appending duplicates."""
    assert Retriever.build(chunks, tmp_path) == 8
    assert Retriever.build(chunks[:2], tmp_path) == 2
    retriever: Retriever = Retriever(tmp_path)
    assert retriever.index.ntotal == 2
    assert [chunk["chunk_id"] for chunk in retriever.chunks] == [0, 1]
