"""Verify ingestion using PDFs generated entirely within the test suite."""

from pathlib import Path

import fitz
import pytest

from app.services.ingest import chunk_pdf, ingest_directory


def write_pdf(path: Path, pages: list[list[str]]) -> None:
    """Write word lists to pages and fail if any text would be clipped."""
    with fitz.open() as document:
        for words in pages:
            page = document.new_page(width=595, height=842)
            space_left: float = page.insert_textbox(
                fitz.Rect(36, 36, 559, 806),
                " \t ".join(words),
                fontsize=8,
            )
            assert space_left >= 0, "Generated test text must fit on its page"
        document.save(path)


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create pages of 400, 50, and 10 uniquely identifiable words."""
    path: Path = tmp_path / "course.pdf"
    pages: list[list[str]] = [
        [f"page1word{i:03d}" for i in range(400)],
        [f"page2word{i:03d}" for i in range(50)],
        [f"page3word{i:03d}" for i in range(10)],
    ]
    write_pdf(path, pages)
    with fitz.open(path) as document:
        for page, expected_words in zip(document, pages, strict=True):
            assert page.get_text("text").split() == expected_words
    return path


def test_chunk_contract(sample_pdf: Path) -> None:
    """Chunks contain only the required fields and one-based page numbers."""
    chunks = chunk_pdf(sample_pdf)
    assert chunks
    for chunk in chunks:
        assert set(chunk) == {"source", "page", "text"}
        assert chunk["source"] == sample_pdf.name
        assert isinstance(chunk["page"], int)
        assert 1 <= chunk["page"] <= 3
        assert isinstance(chunk["text"], str)
        assert chunk["text"] == " ".join(chunk["text"].split())


def test_chunks_preserve_page_boundaries(sample_pdf: Path) -> None:
    """Each chunk belongs to exactly one page; short pages are excluded."""
    chunks = chunk_pdf(sample_pdf)
    assert {chunk["page"] for chunk in chunks} == {1, 2}
    for chunk in chunks:
        text = chunk["text"]
        assert isinstance(text, str)
        assert all(word.startswith(f"page{chunk['page']}word") for word in text.split())
    assert sum(chunk["page"] == 2 for chunk in chunks) == 1


def test_overlapping_windows(sample_pdf: Path) -> None:
    """Adjacent windows share exactly window minus stride original words."""
    window: int = 180
    stride: int = 120
    page_chunks = [
        chunk for chunk in chunk_pdf(sample_pdf, window, stride) if chunk["page"] == 1
    ]
    assert len(page_chunks) == 3
    for previous, current in zip(page_chunks, page_chunks[1:]):
        previous_text = previous["text"]
        current_text = current["text"]
        assert isinstance(previous_text, str)
        assert isinstance(current_text, str)
        previous_words: list[str] = previous_text.split()
        current_words: list[str] = current_text.split()
        overlap: int = window - stride
        assert previous_words[-overlap:] == current_words[:overlap]
        assert len(set(previous_words) & set(current_words)) == overlap


def test_chunk_size_limits(sample_pdf: Path) -> None:
    """Every emitted chunk meets the configured word-count bounds."""
    for chunk in chunk_pdf(sample_pdf, window=180, stride=120, min_words=30):
        text = chunk["text"]
        assert isinstance(text, str)
        assert 30 <= len(text.split()) <= 180


@pytest.mark.parametrize("word_count", [180, 181, 300, 400, 420])
def test_page_tail_without_duplicate(tmp_path: Path, word_count: int) -> None:
    """Emit exactly the necessary windows, including the page tail once."""
    path: Path = tmp_path / "tail.pdf"
    words: list[str] = [f"word{i:03d}" for i in range(word_count)]
    write_pdf(path, [words])
    chunks = chunk_pdf(path, window=180, stride=120, min_words=1)
    expected_count: int = 1 + (max(0, word_count - 180) + 119) // 120
    assert len(chunks) == expected_count
    texts: list[str] = []
    for chunk in chunks:
        text = chunk["text"]
        assert isinstance(text, str)
        texts.append(text)
    assert len(set(texts)) == len(texts)
    assert texts[-1].split()[-1] == words[-1]


@pytest.mark.parametrize(
    ("window", "stride"),
    [(0, 1), (-1, 1), (180, 0), (180, -1), (180, 181)],
)
def test_invalid_window_or_stride(
    sample_pdf: Path, window: int, stride: int
) -> None:
    """Reject invalid window and stride values before reading the PDF."""
    with pytest.raises(ValueError):
        chunk_pdf(sample_pdf, window=window, stride=stride)


def test_empty_directory(tmp_path: Path) -> None:
    """An empty PDF directory produces a clear error."""
    with pytest.raises(FileNotFoundError, match="No PDF files"):
        ingest_directory(tmp_path)


def test_directory_sorted_order(tmp_path: Path) -> None:
    """Directory ingestion follows filename order rather than creation order."""
    words: list[str] = [f"word{i:03d}" for i in range(50)]
    write_pdf(tmp_path / "z.pdf", [words])
    write_pdf(tmp_path / "a.pdf", [words])
    (tmp_path / "notes.txt").write_text("Ignored non-PDF file.", encoding="utf-8")
    chunks = ingest_directory(tmp_path)
    assert [chunk["source"] for chunk in chunks] == ["a.pdf", "z.pdf"]


def test_empty_page_is_skipped(tmp_path: Path) -> None:
    """Pages without extractable text return no chunks."""
    path: Path = tmp_path / "blank.pdf"
    write_pdf(path, [[]])
    assert chunk_pdf(path) == []
