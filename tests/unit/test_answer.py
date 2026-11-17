"""Tests for grounded answer prompts."""

from uuid import UUID

from docreader.application.answer import (
    NO_MATCH_ANSWER,
    answer_question,
    build_grounding_prompt,
)
from docreader.application.search import RetrievedSegment


def test_grounding_prompt_includes_the_source_location() -> None:
    match = RetrievedSegment(
        document_id=UUID("0b6f6f0e-2f0a-4f8a-9c1d-6d5c2a9e8f11"),
        title="investment-topics",
        filename="investment-topics.md",
        position=3,
        content="Compound interest grows over time.",
        line_start=7,
        line_end=11,
        distance=0.12,
    )

    system_prompt, user_prompt = build_grounding_prompt(
        "What is compound interest?",
        [match],
    )

    assert "only the passages" in system_prompt
    assert "[investment-topics.md:7-11]" in user_prompt
    assert "Compound interest grows over time." in user_prompt


async def test_answer_without_passages_does_not_call_the_model() -> None:
    answer = await answer_question(None, "What is compound interest?", [])

    assert answer == NO_MATCH_ANSWER
