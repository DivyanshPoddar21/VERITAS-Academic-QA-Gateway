"""Health endpoint for the VERITAS service."""

from fastapi import APIRouter

router: APIRouter = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "veritas"}
