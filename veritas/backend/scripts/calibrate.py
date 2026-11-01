"""Evaluate retrieval-score separation and recommend a confidence threshold."""

import sys
from pathlib import Path

# Resolve app imports when invoked as python scripts/calibrate.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import json
import logging
from statistics import mean
from typing import TYPE_CHECKING, Any

from app.config import INDEX_DIR, TAU_MAX, TAU_MIN
from app.services.gating import passes_gate, validate_tau

if TYPE_CHECKING:
    from app.services.retriever import Retriever

logger: logging.Logger = logging.getLogger(__name__)
DEFAULT_EVAL_SET: Path = Path(__file__).resolve().parents[1] / "tests" / "eval_set.json"


def load_eval_set(path: Path) -> tuple[list[str], list[str]]:
    """Load two nonempty groups containing only nonblank question strings."""
    with path.open("r", encoding="utf-8") as handle:
        data: Any = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Evaluation JSON must be an object")

    groups: list[list[str]] = []
    for name in ("in_scope", "out_of_scope"):
        questions: Any = data.get(name)
        if not isinstance(questions, list) or not questions:
            raise ValueError(f"'{name}' must be a nonempty list of questions")
        if any(not isinstance(q, str) or not q.strip() for q in questions):
            raise ValueError(f"'{name}' must contain only nonblank strings")
        groups.append([q.strip() for q in questions])
    return groups[0], groups[1]


def score_questions(retriever: "Retriever", questions: list[str]) -> list[float]:
    """Retrieve five hits per question and retain the true maximum score."""
    scores: list[float] = []
    for question in questions:
        _, max_score = passes_gate(retriever.search(question, top_k=5), TAU_MIN)
        scores.append(max_score)
    return scores


def print_group_summary(name: str, scores: list[float]) -> None:
    """Print sample count and maximum-score distribution statistics."""
    print(
        f"{name}: n={len(scores)}, mean={mean(scores):.4f}, "
        f"min={min(scores):.4f}, max={max(scores):.4f}"
    )


def print_sweep(in_scores: list[float], out_scores: list[float]) -> float:
    """Print threshold metrics and return the best tau, preferring higher ties."""
    print("\n tau | in-scope recall | out-of-scope rejection | sum")
    print("-----|-----------------|------------------------|------")
    best_key: tuple[int, float] = (-1, TAU_MIN)

    for hundredths in range(round(TAU_MIN * 100), round(TAU_MAX * 100) + 1, 5):
        tau: float = validate_tau(hundredths / 100.0)
        accepted: int = sum(score >= tau for score in in_scores)
        rejected: int = sum(score < tau for score in out_scores)
        recall: float = accepted / len(in_scores)
        rejection: float = rejected / len(out_scores)
        print(f"{tau:.2f} | {recall:15.2%} | {rejection:22.2%} | {recall + rejection:.4f}")

        # A common denominator makes objective ties exact, even for unequal groups.
        objective: int = accepted * len(out_scores) + rejected * len(in_scores)
        candidate: tuple[int, float] = (objective, tau)
        if candidate > best_key:
            best_key = candidate

    return best_key[1]


def main() -> int:
    """Calibrate against an existing index without modifying any configuration."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Recommend a VERITAS confidence threshold from labeled questions."
    )
    parser.add_argument("--index-dir", type=Path, default=INDEX_DIR)
    parser.add_argument("--eval-set", type=Path, default=DEFAULT_EVAL_SET)
    args: argparse.Namespace = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        in_questions, out_questions = load_eval_set(args.eval_set)

        from app.services.retriever import Retriever

        retriever: Retriever = Retriever(args.index_dir)
        in_scores: list[float] = score_questions(retriever, in_questions)
        out_scores: list[float] = score_questions(retriever, out_questions)
        print(f"Index: {args.index_dir}\nEvaluation set: {args.eval_set}")
        print_group_summary("In scope", in_scores)
        print_group_summary("Out of scope", out_scores)
        recommended_tau: float = print_sweep(in_scores, out_scores)
        print(f"\nRecommended tau: {recommended_tau:.2f}")
        print("Objective: maximize recall + rejection; ties favor the higher tau.")
        print("Advisory only: DEFAULT_TAU has not been changed.")
        print("Use corpus-matched questions and a separate held-out set for evaluation.")
    except Exception as error:
        logger.error("Calibration failed (%s): %s", type(error).__name__, error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
