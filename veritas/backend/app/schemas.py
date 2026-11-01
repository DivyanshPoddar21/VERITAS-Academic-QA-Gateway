"""Shared request and response contracts for the VERITAS API."""

from typing import Literal

from pydantic import BaseModel, Field

from app.config import TAU_MAX, TAU_MIN


class LoginRequest(BaseModel):
    """Represent username and password credentials."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Return a bearer access token."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"


class QuestionRequest(BaseModel):
    """Describe a question and its retrieval settings."""

    question: str = Field(..., min_length=3, max_length=1000)
    top_k: int = Field(5, ge=1, le=10)
    threshold: float = Field(0.35, ge=TAU_MIN, le=TAU_MAX)


class Citation(BaseModel):
    """Preserve retrieved evidence and its page-level provenance."""

    chunk_id: int
    source: str
    page: int
    score: float
    text: str


class QuestionResponse(BaseModel):
    """Return an answered or refused question with supporting evidence."""

    status: Literal["answered", "refused"]
    answer: str
    max_score: float
    threshold: float
    citations: list[Citation]
    latency_ms: float