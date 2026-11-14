"""Tests for text upload validation and segment creation."""

import pytest

from docreader.ingestion.text import (
    EmptyDocumentError,
    InvalidDocumentTextError,
    UnsupportedDocumentTypeError,
    chunk_text,
    prepare_text_upload,
)


def test_chunk_text_preserves_paragraph_line_ranges() -> None:
    segments = chunk_text("Alpha line\nBeta line\n\nGamma line\n")

    assert [(segment.line_start, segment.line_end) for segment in segments] == [
        (1, 2),
        (4, 4),
    ]
    assert segments[0].content == "Alpha line\nBeta line"
    assert segments[1].position == 1


def test_prepare_text_upload_accepts_markdown() -> None:
    upload = prepare_text_upload("guide.md", b"# Guide\n", max_bytes=100)

    assert upload.media_type == "text/markdown"
    assert upload.title == "guide"
    assert upload.segments[0].content == "# Guide"


def test_prepare_text_upload_rejects_unsupported_extension() -> None:
    with pytest.raises(UnsupportedDocumentTypeError):
        prepare_text_upload("report.pdf", b"text", max_bytes=100)


def test_prepare_text_upload_rejects_empty_text() -> None:
    with pytest.raises(EmptyDocumentError):
        prepare_text_upload("empty.txt", b" \n\n", max_bytes=100)


def test_prepare_text_upload_rejects_invalid_utf8() -> None:
    with pytest.raises(InvalidDocumentTextError):
        prepare_text_upload("broken.txt", b"\xff", max_bytes=100)
