"""FastAPI application wiring and startup initialization."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, INDEX_DIR
from app.routers import auth, health, qa
from app.services.retriever import Retriever


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load the persisted retriever once during application startup."""
    app.state.retriever = Retriever(INDEX_DIR)
    yield


app: FastAPI = FastAPI(
    title="VERITAS — Academic QA Gateway",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(qa.router)
app.include_router(health.router)

# VERITAS_LOCAL_FRONTEND_BEGIN
from pathlib import Path as _VeritasFrontendPath
from fastapi.staticfiles import StaticFiles as _VeritasFrontendFiles

_VERITAS_FRONTEND_DIST = (
    _VeritasFrontendPath(__file__).resolve().parents[2] / "frontend" / "dist"
)

# Keep this mount after every API router so API routes retain priority.
app.mount(
    "/",
    _VeritasFrontendFiles(
        directory=str(_VERITAS_FRONTEND_DIST),
        html=True,
        check_dir=False,
    ),
    name="veritas_frontend",
)
# VERITAS_LOCAL_FRONTEND_END
