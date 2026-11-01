"""Verify authentication and gated QA without loading a model or index."""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import qa
from app.schemas import Citation
from app.security import create_token, get_current_user


class FakeRetriever:
    """Return a configurable list of canned retrieval hits."""

    def __init__(self) -> None:
        """Initialize an empty hit list for each test."""
        self.hits: list[tuple[dict[str, Any], float]] = []

    def search(
        self, query: str, top_k: int
    ) -> list[tuple[dict[str, Any], float]]:
        """Return at most top_k canned hits without invoking a model."""
        return self.hits[:top_k]


def make_hit(chunk_id: int, score: float) -> tuple[dict[str, Any], float]:
    """Create a valid chunk and its retrieval score."""
    chunk: dict[str, Any] = {
        "chunk_id": chunk_id,
        "source": "course.pdf",
        "page": chunk_id + 1,
        "text": (
            "Gradient descent minimizes loss by updating model parameters "
            "in the direction of the negative gradient."
        ),
    }
    return chunk, score


@pytest.fixture
def fake_retriever(monkeypatch: pytest.MonkeyPatch) -> FakeRetriever:
    """Install a fake retriever and restore application state after the test."""
    retriever: FakeRetriever = FakeRetriever()
    monkeypatch.setattr(app.state, "retriever", retriever, raising=False)
    return retriever


@pytest.fixture
def client(fake_retriever: FakeRetriever) -> Iterator[TestClient]:
    """Create a client without a context manager so lifespan does not run."""
    test_client: TestClient = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Provide a valid bearer token for protected endpoint tests."""
    return {
        "Authorization": f"Bearer {create_token('divyansh')}",
    }


def test_login_success(client: TestClient) -> None:
    """Valid form credentials return a usable bearer token."""
    response = client.post(
        "/auth/login",
        data={"username": "divyansh", "password": "admin123"},
    )

    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]
    assert get_current_user(body["access_token"]) == "divyansh"


def test_login_wrong_password(client: TestClient) -> None:
    """An incorrect password returns an authentication error."""
    response = client.post(
        "/auth/login",
        data={"username": "divyansh", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
    assert response.headers["www-authenticate"] == "Bearer"


def test_ask_requires_token(client: TestClient) -> None:
    """The QA endpoint rejects requests without a bearer token."""
    response = client.post(
        "/ask",
        json={"question": "What is gradient descent?"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_ask_answered(
    client: TestClient,
    fake_retriever: FakeRetriever,
    auth_headers: dict[str, str],
) -> None:
    """Evidence above the threshold produces an answer and citations."""
    fake_retriever.hits = [make_hit(0, 0.80)]

    response = client.post(
        "/ask",
        headers=auth_headers,
        json={
            "question": "What is gradient descent?",
            "threshold": 0.35,
        },
    )

    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert body["status"] == "answered"
    assert body["answer"].strip()
    assert len(body["citations"]) == 1
    assert body["citations"][0]["chunk_id"] == 0
    assert body["citations"][0]["score"] == 0.80
    assert body["max_score"] == 0.80
    assert body["threshold"] == 0.35
    assert body["latency_ms"] >= 0


def test_ask_refused(
    client: TestClient,
    fake_retriever: FakeRetriever,
    auth_headers: dict[str, str],
) -> None:
    """Evidence below the threshold produces a refusal without citations."""
    fake_retriever.hits = [make_hit(0, 0.10)]

    response = client.post(
        "/ask",
        headers=auth_headers,
        json={
            "question": "How do I bake a chocolate cake?",
            "threshold": 0.35,
        },
    )

    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert body["status"] == "refused"
    assert body["answer"] == (
        "This question falls outside the indexed course material. "
        "VERITAS only answers from the loaded corpus."
    )
    assert body["citations"] == []
    assert body["max_score"] == 0.10
    assert body["threshold"] == 0.35
    assert body["latency_ms"] >= 0


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("threshold", 0.10),
        ("top_k", 0),
        ("top_k", 11),
        ("question", "hi"),
    ),
)
def test_invalid_question_request(
    client: TestClient,
    auth_headers: dict[str, str],
    field: str,
    value: str | int | float,
) -> None:
    """Invalid question lengths and retrieval settings return HTTP 422."""
    payload: dict[str, Any] = {
        "question": "What is gradient descent?",
        "top_k": 5,
        "threshold": 0.35,
    }
    payload[field] = value

    response = client.post(
        "/ask",
        headers=auth_headers,
        json=payload,
    )

    assert response.status_code == 422


def test_only_supported_hits_become_citations(
    client: TestClient,
    fake_retriever: FakeRetriever,
    auth_headers: dict[str, str],
) -> None:
    """Only individual hits meeting the threshold are included as evidence."""
    fake_retriever.hits = [
        make_hit(0, 0.80),
        make_hit(1, 0.50),
        make_hit(2, 0.20),
    ]

    response = client.post(
        "/ask",
        headers=auth_headers,
        json={
            "question": "What is gradient descent?",
            "top_k": 5,
            "threshold": 0.40,
        },
    )

    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert body["status"] == "answered"
    assert len(body["citations"]) == 2
    assert [citation["chunk_id"] for citation in body["citations"]] == [0, 1]
    assert [citation["score"] for citation in body["citations"]] == [0.80, 0.50]


def test_refusal_never_calls_synthesizer(
    client: TestClient,
    fake_retriever: FakeRetriever,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Refusal returns successfully even when synthesis would raise."""
    fake_retriever.hits = [make_hit(0, 0.10)]

    def forbidden_synthesis(
        question: str, citations: list[Citation]
    ) -> str:
        """Fail immediately if the refused path invokes synthesis."""
        raise AssertionError("Synthesis must never run on a refused request")

    monkeypatch.setattr(qa, "synthesize", forbidden_synthesis)

    response = client.post(
        "/ask",
        headers=auth_headers,
        json={
            "question": "How do I bake a chocolate cake?",
            "threshold": 0.35,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "refused"
    assert response.json()["citations"] == []