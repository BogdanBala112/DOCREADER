"""Unit tests for RAG evaluation metrics."""

from uuid import UUID

import pytest

from docreader.application.search import RetrievedSegment
from docreader.evaluation.metrics import (
    EvalResult,
    EvalSample,
    score_answer_relevance,
    score_context_relevance,
    score_faithfulness,
)

_DOC_ID = UUID("0b6f6f0e-2f0a-4f8a-9c1d-6d5c2a9e8f11")


def _seg(content: str, distance: float) -> RetrievedSegment:
    return RetrievedSegment(
        document_id=_DOC_ID,
        title="test-doc",
        filename="test.md",
        position=0,
        content=content,
        line_start=1,
        line_end=5,
        distance=distance,
    )


# --- score_context_relevance -------------------------------------------------


def test_context_relevance_no_segments_returns_zero() -> None:
    assert score_context_relevance("what is RAG?", []) == 0.0


def test_context_relevance_uses_best_segment() -> None:
    segments = [
        _seg("retrieval augmented generation", 0.4),
        _seg("unrelated text", 0.9),
    ]
    score = score_context_relevance("what is RAG?", segments)
    assert score == pytest.approx(0.6)  # 1.0 - 0.4 (the min distance)


def test_context_relevance_single_perfect_match() -> None:
    score = score_context_relevance("test", [_seg("test content", 0.0)])
    assert score == pytest.approx(1.0)


# --- score_faithfulness ------------------------------------------------------


def test_faithfulness_empty_answer_returns_zero() -> None:
    assert score_faithfulness("", [_seg("some context", 0.1)]) == 0.0


def test_faithfulness_empty_segments_returns_zero() -> None:
    assert score_faithfulness("some answer", []) == 0.0


def test_faithfulness_answer_grounded_in_context() -> None:
    seg = _seg("compound interest grows exponentially over time", 0.1)
    score = score_faithfulness("compound interest grows over time", [seg])
    assert score > 0.8


def test_faithfulness_answer_not_in_context() -> None:
    seg = _seg("the sky is blue on clear days", 0.1)
    score = score_faithfulness("quantum entanglement violates locality", [seg])
    assert score < 0.3


# --- score_answer_relevance --------------------------------------------------


def test_answer_relevance_empty_returns_zero() -> None:
    assert score_answer_relevance("what is RAG?", "") == 0.0


def test_answer_relevance_on_topic() -> None:
    score = score_answer_relevance(
        "what does retrieval augmented generation mean?",
        "retrieval augmented generation combines search with language models",
    )
    assert score > 0.4


def test_answer_relevance_off_topic() -> None:
    score = score_answer_relevance(
        "what does retrieval augmented generation mean?",
        "the weather today is sunny and warm outside",
    )
    assert score < 0.3


# --- EvalResult overall ------------------------------------------------------


def test_eval_result_overall_is_mean() -> None:
    result = EvalResult(
        question="q",
        answer="a",
        context_relevance=0.8,
        faithfulness=0.6,
        answer_relevance=0.4,
    )
    assert result.overall == pytest.approx(0.6)


def test_eval_sample_stores_fields() -> None:
    sample = EvalSample(
        question="what is pgvector?",
        reference_answer="a Postgres extension",
    )
    assert sample.question == "what is pgvector?"
    assert sample.reference_answer == "a Postgres extension"
