"""Validation and chunking for plain-text document uploads."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

MAX_SEGMENT_CHARACTERS = 800
MAX_FILENAME_LENGTH = 255
SUPPORTED_TEXT_EXTENSIONS = {
    ".txt": "text/plain",
    ".md": "text/markdown",
}


class UnsupportedDocumentTypeError(Exception):
    """The uploaded file extension is outside the current allowlist."""


class EmptyDocumentError(Exception):
    """The uploaded file contains no usable text."""


class InvalidDocumentTextError(Exception):
    """The uploaded file is not valid UTF-8 text."""


class DocumentTooLargeError(Exception):
    """The uploaded file exceeds the configured size limit."""


@dataclass(frozen=True)
class TextSegmentDraft:
    """One normalized piece of text and its source line range."""

    position: int
    content: str
    token_count: int
    line_start: int
    line_end: int


@dataclass(frozen=True)
class PreparedTextUpload:
    """A validated text file ready to be stored."""

    filename: str
    title: str
    media_type: str
    content_hash: str
    data: bytes
    segments: tuple[TextSegmentDraft, ...]


def prepare_text_upload(
    filename: str | None,
    data: bytes,
    max_bytes: int,
) -> PreparedTextUpload:
    """Validate a text upload and split its content into ordered segments."""
    if len(data) > max_bytes:
        raise DocumentTooLargeError

    safe_filename = _validated_filename(filename)
    media_type = _media_type_for_filename(safe_filename)

    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise InvalidDocumentTextError from error

    segments = tuple(chunk_text(text))
    if not segments:
        raise EmptyDocumentError

    return PreparedTextUpload(
        filename=safe_filename,
        title=_title_from_filename(safe_filename),
        media_type=media_type,
        content_hash=hashlib.sha256(data).hexdigest(),
        data=data,
        segments=segments,
    )


def chunk_text(text: str) -> list[TextSegmentDraft]:
    """Group text into line-located segments of at most 800 characters."""
    drafts: list[TextSegmentDraft] = []
    buffered_lines: list[str] = []
    line_start: int | None = None
    line_end: int | None = None

    def flush() -> None:
        nonlocal buffered_lines, line_start, line_end
        if line_start is None or line_end is None or not buffered_lines:
            buffered_lines = []
            line_start = None
            line_end = None
            return

        content = "\n".join(buffered_lines).strip()
        if content:
            drafts.append(
                TextSegmentDraft(
                    position=len(drafts),
                    content=content,
                    token_count=len(content.split()),
                    line_start=line_start,
                    line_end=line_end,
                )
            )
        buffered_lines = []
        line_start = None
        line_end = None

    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            flush()
            continue

        pieces = _split_line(line)
        for piece in pieces:
            projected = "\n".join([*buffered_lines, piece])
            if buffered_lines and len(projected) > MAX_SEGMENT_CHARACTERS:
                flush()
            if line_start is None:
                line_start = line_number
            buffered_lines.append(piece)
            line_end = line_number

    flush()
    return drafts


def _validated_filename(filename: str | None) -> str:
    if filename is None:
        raise InvalidDocumentTextError

    safe_filename = Path(filename).name
    if not safe_filename or len(safe_filename) > MAX_FILENAME_LENGTH:
        raise InvalidDocumentTextError
    return safe_filename


def _media_type_for_filename(filename: str) -> str:
    media_type = SUPPORTED_TEXT_EXTENSIONS.get(Path(filename).suffix.lower())
    if media_type is None:
        raise UnsupportedDocumentTypeError
    return media_type


def _title_from_filename(filename: str) -> str:
    title = Path(filename).stem.strip()
    return title or "Untitled"


def _split_line(line: str) -> list[str]:
    if len(line) <= MAX_SEGMENT_CHARACTERS:
        return [line]
    return [
        line[start : start + MAX_SEGMENT_CHARACTERS]
        for start in range(0, len(line), MAX_SEGMENT_CHARACTERS)
    ]
