"""Test the confidence gate with fake hits and no embedding dependencies."""

from typing import Any

import pytest

from app.services.gating import passes_gate, supported_hits, validate_tau


def fake_hits(scores: list[float]) -> list[tuple[dict[str, Any], float]]:
    """Create identifiable fake chunks in the supplied score order."""
    return [({"chunk_id": row}, score) for row, score in enumerate(scores)]


def test_empty_hits() -> None:
    """No retrieved evidence fails a valid positive threshold."""
    assert passes_gate([], 0.35) == (False, 0.0)


def test_exact_boundary_passes() -> None:
    """A score equal to tau passes the inclusive comparison."""
    assert passes_gate(fake_hits([0.35]), 0.35) == (True, 0.35)


def test_score_just_below_tau_fails() -> None:
    """A score even slightly below tau fails."""
    score: float = 0.35 - 1e-6
    assert passes_gate(fake_hits([score]), 0.35) == (False, score)


def test_unsorted_hits_use_true_maximum() -> None:
    """The maximum is computed independently of retrieval order."""
    assert passes_gate(fake_hits([0.21, 0.82, 0.40]), 0.80) == (True, 0.82)


def test_negative_maximum_is_preserved() -> None:
    """Zero is the empty-list default, not a floor on actual scores."""
    assert passes_gate(fake_hits([-0.40, -0.10]), 0.35) == (False, -0.10)


@pytest.mark.parametrize("tau", [0.19, 0.96, float("nan"), float("inf")])
def test_invalid_tau(tau: float) -> None:
    """Out-of-range and non-finite thresholds are rejected."""
    with pytest.raises(ValueError, match="tau must be between"):
        validate_tau(tau)


@pytest.mark.parametrize("tau", [0.20, 0.35, 0.95])
def test_valid_tau(tau: float) -> None:
    """Both interval endpoints and an interior value are accepted."""
    assert validate_tau(tau) == tau


def test_supported_hits_preserve_order_and_input() -> None:
    """Filtering includes the boundary, preserves order, and leaves input intact."""
    hits = fake_hits([0.60, 0.10, 0.35, 0.90, 0.349999])
    original = hits.copy()
    assert supported_hits(hits, 0.35) == [hits[0], hits[2], hits[3]]
    assert hits == original


def test_supported_hits_empty() -> None:
    """Filtering an empty hit list returns an empty list."""
    assert supported_hits([], 0.35) == []


def test_supported_hits_all_rejected() -> None:
    """Filtering removes every hit below the threshold."""
    assert supported_hits(fake_hits([0.10, 0.20]), 0.35) == []
