"""Exercise gate boundaries, authentication, CORS, and validation via HTTP."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, NoReturn

import jwt
import pytest
from fastapi.testclient import TestClient

from app.config import JWT_ALGO, JWT_SECRET
from app.routers import qa
from app.schemas import Citation

if TYPE_CHECKING:
    from tests.conftest import FakeRetriever


def make_hits(scores: list[float]) -> list[tuple[dict[str, Any], float]]:
    """Create valid, distinguishable chunks in the supplied score order."""
    return [
        (
            {
                "chunk_id": row,
                "source": "course.pdf",
                "page": row + 1,
                "text": "Gradient descent updates parameters to minimize loss.",
            },
            score,
        )
        for row, score in enumerate(scores)
    ]


@pytest.mark.parametrize("threshold", (0.20, 0.35, 0.95))
def test_exact_gate_boundary_answers(
    client: TestClient,
    fake_retriever: FakeRetriever,
    auth_headers: dict[str, str],
    question_payload: dict[str, Any],
    threshold: float,
) -> None:
    """Equality passes, including both permitted threshold endpoints."""
    fake_retriever.hits = make_hits([threshold])
    question_payload["threshold"] = threshold
    response = client.post("/ask", headers=auth_headers, json=question_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answered"
    assert body["answer"].strip()
    assert body["max_score"] == pytest.approx(threshold)
    assert body["threshold"] == threshold
    assert len(body["citations"]) == 1
    assert body["latency_ms"] >= 0
    assert fake_retriever.calls == [(question_payload["question"], 5)]


@pytest.mark.parametrize("threshold", (0.20, 0.35, 0.95))
def test_score_just_below_threshold_refuses(
    client: TestClient,
    fake_retriever: FakeRetriever,
    auth_headers: dict[str, str],
    question_payload: dict[str, Any],
    threshold: float,
) -> None:
    """Gating compares original scores rather than rounded display values."""
    score: float = threshold - 0.0001
    fake_retriever.hits = make_hits([score])
    question_payload["threshold"] = threshold
    response = client.post("/ask", headers=auth_headers, json=question_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "refused"
    assert body["max_score"] == pytest.approx(score)
    assert body["max_score"] < body["threshold"]
    assert body["citations"] == []


def test_empty_retrieval_refuses(
    client: TestClient,
    auth_headers: dict[str, str],
    question_payload: dict[str, Any],
) -> None:
    """An empty corpus result has zero support and no citations."""
    response = client.post("/ask", headers=auth_headers, json=question_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "refused"
    assert body["max_score"] == 0.0
    assert body["citations"] == []


@pytest.mark.parametrize("threshold", (0.19, 0.96))
def test_out_of_range_threshold_rejected(
    client: TestClient,
    fake_retriever: FakeRetriever,
    auth_headers: dict[str, str],
    question_payload: dict[str, Any],
    threshold: float,
) -> None:
    """Invalid thresholds fail validation before retrieval occurs."""
    question_payload["threshold"] = threshold
    response = client.post("/ask", headers=auth_headers, json=question_payload)
    assert response.status_code == 422
    assert fake_retriever.calls == []


def test_refusal_never_invokes_synthesis(
    client: TestClient,
    fake_retriever: FakeRetriever,
    auth_headers: dict[str, str],
    question_payload: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A below-threshold request returns normally with synthesis forbidden."""
    fake_retriever.hits = make_hits([0.10])

    def forbidden_synthesis(
        question: str, citations: list[Citation]
    ) -> NoReturn:
        raise AssertionError("Refused questions must never reach synthesis")

    monkeypatch.setattr(qa, "synthesize", forbidden_synthesis)
    response = client.post("/ask", headers=auth_headers, json=question_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "refused"
    assert response.json()["citations"] == []


def test_unsorted_hits_filter_before_rounding(
    client: TestClient,
    fake_retriever: FakeRetriever,
    auth_headers: dict[str, str],
    question_payload: dict[str, Any],
) -> None:
    """Use the true maximum and exclude a hit that would round up to tau."""
    fake_retriever.hits = make_hits([0.20, 0.87654321, 0.40, 0.39999])
    question_payload["threshold"] = 0.40
    response = client.post("/ask", headers=auth_headers, json=question_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answered"
    assert body["max_score"] == pytest.approx(0.87654321)
    assert [citation["chunk_id"] for citation in body["citations"]] == [1, 2]
    assert [citation["score"] for citation in body["citations"]] == [0.8765, 0.40]


@pytest.mark.parametrize("token_case", ("expired", "wrong_secret"))
def test_invalid_signed_token_rejected(
    client: TestClient,
    fake_retriever: FakeRetriever,
    question_payload: dict[str, Any],
    token_case: str,
) -> None:
    """Expired or incorrectly signed JWTs fail before retrieval."""
    now: datetime = datetime.now(timezone.utc)
    expires: datetime = now + timedelta(minutes=5)
    secret: str = JWT_SECRET
    if token_case == "expired":
        expires = now - timedelta(minutes=5)
    else:
        secret = JWT_SECRET + "-deliberately-different-test-signing-key"

    token: str = jwt.encode(
        {"sub": "divyansh", "exp": expires}, secret, algorithm=JWT_ALGO
    )
    response = client.post(
        "/ask",
        headers={"Authorization": f"Bearer {token}"},
        json=question_payload,
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert fake_retriever.calls == []


@pytest.mark.parametrize(
    "authorization",
    ("Basic ZGl2eWFuc2g6YWRtaW4xMjM=", "Bearer", "Bearer not-a-jwt"),
    ids=("wrong-scheme", "missing-bearer-value", "malformed-jwt"),
)
def test_malformed_authorization_rejected(
    client: TestClient,
    fake_retriever: FakeRetriever,
    question_payload: dict[str, Any],
    authorization: str,
) -> None:
    """Wrong schemes, empty bearer values, and malformed tokens return 401."""
    response = client.post(
        "/ask",
        headers={"Authorization": authorization},
        json=question_payload,
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert fake_retriever.calls == []


def test_missing_authorization_rejected(
    client: TestClient,
    fake_retriever: FakeRetriever,
    question_payload: dict[str, Any],
) -> None:
    """A missing authorization header returns 401 before retrieval."""
    response = client.post("/ask", json=question_payload)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert fake_retriever.calls == []


@pytest.mark.parametrize(
    "origin",
    (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ),
)
def test_allowed_cors_preflight(client: TestClient, origin: str) -> None:
    """Configured browser origins may send authenticated JSON requests."""
    response = client.options(
        "/ask",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"
    allowed_headers: set[str] = {
        value.strip().lower()
        for value in response.headers["access-control-allow-headers"].split(",")
    }
    assert {"authorization", "content-type"} <= allowed_headers


def test_disallowed_cors_origin(client: TestClient) -> None:
    """An unapproved origin receives no browser access grant."""
    response = client.options(
        "/ask",
        headers={
            "Origin": "http://evil.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    ("field", "value"),
    (("question", "hi"), ("question", "x" * 1001), ("top_k", 0), ("top_k", 11)),
    ids=("question-too-short", "question-too-long", "top-k-zero", "top-k-eleven"),
)
def test_invalid_input_rejected(
    client: TestClient,
    fake_retriever: FakeRetriever,
    auth_headers: dict[str, str],
    question_payload: dict[str, Any],
    field: str,
    value: str | int,
) -> None:
    """Out-of-range question lengths and top_k values return 422."""
    question_payload[field] = value
    response = client.post("/ask", headers=auth_headers, json=question_payload)
    assert response.status_code == 422
    assert fake_retriever.calls == []