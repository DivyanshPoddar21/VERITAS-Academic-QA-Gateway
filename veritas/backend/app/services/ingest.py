"""Extract page-local word windows from course PDFs."""

from pathlib import Path

import fitz

from app.config import MIN_CHUNK_WORDS, PDF_DIR, STRIDE_WORDS, WINDOW_WORDS


def chunk_pdf(
    path: Path,
    window: int = WINDOW_WORDS,
    stride: int = STRIDE_WORDS,
    min_words: int = MIN_CHUNK_WORDS,
) -> list[dict[str, str | int]]:
    """Return normalized chunks with filename and one-based page provenance."""
    if window <= 0:
        raise ValueError("window must be greater than zero")
    if not 0 < stride <= window:
        raise ValueError("stride must satisfy 0 < stride <= window")

    chunks: list[dict[str, str | int]] = []
    with fitz.open(path) as document:
        for page_number, page in enumerate(document, start=1):
            ignored_lines: set[str] = {
                "ankita singh, dept. of it, akgec",
                "bcs 055",
            }
            clean_lines: list[str] = [
                line
                for line in page.get_text("text").splitlines()
                if " ".join(line.split()).casefold() not in ignored_lines
            ]
            words: list[str] = " ".join(clean_lines).split()
            if not words or len(words) < min_words:
                continue

            for start in range(0, len(words), stride):
                end: int = min(start + window, len(words))
                chunk_words: list[str] = words[start:end]
                if len(chunk_words) >= min_words:
                    chunks.append(
                        {
                            "source": path.name,
                            "page": page_number,
                            "text": " ".join(chunk_words),
                        }
                    )
                if end == len(words):
                    break

    return chunks


def ingest_directory(pdf_dir: Path = PDF_DIR) -> list[dict[str, str | int]]:
    """Concatenate chunks from sorted PDF files, requiring at least one PDF."""
    pdf_paths: list[Path] = sorted(
        path for path in pdf_dir.glob("*.pdf") if path.is_file()
    )
    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files (*.pdf) found in directory: {pdf_dir}")

    chunks: list[dict[str, str | int]] = []
    for path in pdf_paths:
        chunks.extend(chunk_pdf(path))
    return chunks
