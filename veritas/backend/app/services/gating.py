"""Pure similarity-threshold helpers for retrieved evidence."""

from typing import Any

from app.config import TAU_MAX, TAU_MIN

# Max-cosine gating is a heuristic, not a guarantee of answer correctness.


def passes_gate(
    hits: list[tuple[dict[str, Any], float]], tau: float
) -> tuple[bool, float]:
    """Return whether the true maximum score meets tau, and that score."""
    max_score: float = max((score for _, score in hits), default=0.0)
    return max_score >= tau, max_score


def validate_tau(tau: float) -> float:
    """Require a finite threshold within the inclusive configured bounds."""
    if not TAU_MIN <= tau <= TAU_MAX:
        raise ValueError(f"tau must be between {TAU_MIN:.2f} and {TAU_MAX:.2f}")
    return tau


def supported_hits(
    hits: list[tuple[dict[str, Any], float]], tau: float
) -> list[tuple[dict[str, Any], float]]:
    """Keep hits meeting tau without changing their original order."""
    return [(chunk, score) for chunk, score in hits if score >= tau]
