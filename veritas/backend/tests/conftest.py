"""Shared API fixtures that never run the application's real lifespan."""

from collections.abc import Iterator
from typing import Any, NoReturn

import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.security import create_token


class FakeRetriever:
    """Return configurable canned hits and record retrieval calls."""

    def __init__(self) -> None:
        self.hits: list[tuple[dict[str, Any], float]] = []
        self.calls: list[tuple[str, int]] = []

    def search(
        self, query: str, top_k: int
    ) -> list[tuple[dict[str, Any], float]]:
        """Return a fresh list containing at most top_k canned hits."""
        self.calls.append((query, top_k))
        return list(self.hits[:top_k])


@pytest.fixture
def fake_retriever(monkeypatch: pytest.MonkeyPatch) -> FakeRetriever:
    """Install isolated fake state and fail if a test starts the real lifespan."""
    retriever: FakeRetriever = FakeRetriever()
    monkeypatch.setattr(
        main_module.app.state, "retriever", retriever, raising=False
    )

    def forbidden_startup(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("API tests must not construct the real Retriever")

    monkeypatch.setattr(main_module, "Retriever", forbidden_startup)
    return retriever


@pytest.fixture
def client(fake_retriever: FakeRetriever) -> Iterator[TestClient]:
    """Create a client without a with block and close it after each test."""
    test_client: TestClient = TestClient(main_module.app)
    try:
        yield test_client
    finally:
        test_client.close()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Return a valid bearer token without making a login request."""
    return {"Authorization": f"Bearer {create_token('divyansh')}"}


@pytest.fixture
def question_payload() -> dict[str, Any]:
    """Return fresh valid request data for each test."""
    return {
        "question": "What is gradient descent?",
        "top_k": 5,
        "threshold": 0.35,
    }