"""Build persisted FAISS artifacts from the configured course PDFs."""

import sys
from pathlib import Path

# Make app imports resolve when invoked as python scripts/build_index.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import logging
from time import perf_counter

from app.config import INDEX_DIR, PDF_DIR
from app.services.ingest import ingest_directory
from app.services.retriever import Retriever

logger: logging.Logger = logging.getLogger(__name__)


def main() -> int:
    """Parse directories, build the index, and report a readable outcome."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Build the VERITAS PDF embedding index."
    )
    parser.add_argument("--pdf-dir", type=Path, default=PDF_DIR)
    parser.add_argument("--index-dir", type=Path, default=INDEX_DIR)
    args: argparse.Namespace = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    started: float = perf_counter()

    try:
        chunks = ingest_directory(args.pdf_dir)
        logger.info("Ingested %d chunks from %s", len(chunks), args.pdf_dir)
        count: int = Retriever.build(chunks, args.index_dir)
    except Exception as error:
        logger.error("Index build failed (%s): %s", type(error).__name__, error)
        return 1

    elapsed: float = perf_counter() - started
    logger.info("Built %d chunks in %.2f seconds", count, elapsed)
    print(f"Saved {count} chunks to {args.index_dir} in {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
