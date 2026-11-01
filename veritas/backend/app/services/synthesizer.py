"""Deterministic extractive answer synthesis from supplied citations."""

import re

from app.schemas import Citation

STOPWORDS: frozenset[str] = frozenset(
    """
    a about above after again against all am an and any are as at
    be because been before being below between both but by
    can could did do does doing down during each few for from
    further had has have having he her here hers herself him
    himself his how i if in into is it its itself just me more
    most my myself no nor not of off on once only or other our
    ours ourselves out over own same she should so some such
    than that the their theirs them themselves then there these
    they this those through to too under until up us very was
    we were what when where which while who whom why will with
    would you your yours yourself yourselves
    """.split()
)


def _tokens(text: str) -> set[str]:
    """Extract lowercase alphanumeric tokens without English stopwords."""
    return set(re.findall(r"[^\W_]+", text.lower())) - STOPWORDS


def _tag(citation: Citation) -> str:
    """Format the source filename and page as an evidence tag."""
    return f"[{citation.source} p.{citation.page}]"


def synthesize(question: str, citations: list[Citation]) -> str:
    """Extract evidence sentences; this interface is a seam for a future LLM."""
    if not citations:
        return ""

    question_tokens: set[str] = _tokens(question)
    candidates: list[tuple[int, float, str, Citation]] = []

    for citation in citations:
        for raw_sentence in re.split(r"(?<=[.!?])\s+", citation.text):
            sentence: str = " ".join(raw_sentence.split())
            if not sentence:
                continue

            overlap: int = len(question_tokens & _tokens(sentence))
            if overlap > 0:
                candidates.append(
                    (overlap, citation.score, sentence, citation)
                )

    candidates.sort(
        key=lambda candidate: (candidate[0], candidate[1]),
        reverse=True,
    )

    selected: list[str] = []
    seen: set[str] = set()

    for _, _, sentence, citation in candidates:
        identity: str = sentence.casefold()
        if identity in seen:
            continue

        seen.add(identity)
        selected.append(sentence)
        if len(selected) == 3:
            break

    if selected:
        return "\n".join(selected)

    top_citation: Citation = max(
        citations,
        key=lambda citation: citation.score,
    )
    return top_citation.text[:300]
