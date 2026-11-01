"""Confidence-gated question answering over the indexed course corpus."""

import time
from typing import Any

from fastapi import APIRouter, Depends, Request

from app.schemas import Citation, QuestionRequest, QuestionResponse
from app.security import get_current_user
from app.services.gating import passes_gate, supported_hits
from app.services.synthesizer import synthesize

router: APIRouter = APIRouter(tags=["qa"])

REFUSAL: str = (
    "This question falls outside the indexed course material. "
    "VERITAS only answers from the loaded corpus."
)


@router.post("/ask", response_model=QuestionResponse)
def ask(
    req: QuestionRequest,
    request: Request,
    _username: str = Depends(get_current_user),
) -> QuestionResponse:
    """Retrieve evidence and gate it before invoking answer synthesis."""
    t0: float = time.perf_counter()
    hits: list[tuple[dict[str, Any], float]] = (
        request.app.state.retriever.search(req.question, req.top_k)
    )
    ok, max_score = passes_gate(hits, req.threshold)

    if not ok:
        return QuestionResponse(
            status="refused",
            answer=REFUSAL,
            max_score=max_score,
            threshold=req.threshold,
            citations=[],
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
        )

    citations: list[Citation] = [
        Citation(
            chunk_id=chunk["chunk_id"],
            source=chunk["source"],
            page=chunk["page"],
            score=round(score, 4),
            text=chunk["text"],
        )
        for chunk, score in supported_hits(hits, req.threshold)
    ]
    answer: str = synthesize(req.question, citations)

    return QuestionResponse(
        status="answered",
        answer=answer,
        max_score=max_score,
        threshold=req.threshold,
        citations=citations,
        latency_ms=round((time.perf_counter() - t0) * 1000, 2),
    )