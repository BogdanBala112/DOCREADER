"""RAG evaluation metrics: context relevance, faithfulness, and answer relevance."""

from dataclasses import dataclass

from docreader.application.search import RetrievedSegment


@dataclass(frozen=True)
class EvalSample:
    """One question with a reference answer for offline evaluation."""

    question: str
    reference_answer: str


@dataclass(frozen=True)
class EvalResult:
    """Scores for one evaluated question-answer pair."""

    question: str
    answer: str
    context_relevance: float  # 0.0–1.0: how relevant are the retrieved segments?
    faithfulness: float  # 0.0–1.0: how grounded is the answer in the context?
    answer_relevance: float  # 0.0–1.0: does the answer address the question?

    @property
    def overall(self) -> float:
        """Mean of all three component scores."""
        return (self.context_relevance + self.faithfulness + self.answer_relevance) / 3


def score_context_relevance(
    question: str,
    segments: list[RetrievedSegment],
) -> float:
    """Score how relevant the retrieved segments are to the question (0.0–1.0).

    Each RetrievedSegment carries:
      - .distance  — cosine distance from pgvector (0 = identical, 1 = orthogonal)
      - .content   — the raw text of the passage

    Return 0.0 if no segments were retrieved.
    """
    if len(segments) == 0:
        return 0.0
    
    distances = [seg.distance for seg in segments]
    return 1.0 - min(distances)

def score_faithfulness(answer: str, segments: list[RetrievedSegment]) -> float:
    """Score how grounded the answer is in the retrieved context (0.0–1.0).

    Measures the fraction of significant answer words (length > 3) that
    also appear in the combined context. A high score means the answer
    sticks to the retrieved material rather than introducing new claims.
    """
    if not segments or not answer:
        return 0.0
    answer_tokens = set(answer.lower().split())
    context_tokens = set(" ".join(seg.content for seg in segments).lower().split())
    significant = {t for t in answer_tokens if len(t) > 3}
    if not significant:
        return 1.0
    return len(significant & context_tokens) / len(significant)


def score_answer_relevance(question: str, answer: str) -> float:
    """Score how directly the answer addresses the question (0.0–1.0).

    Measures the fraction of significant question words (length > 3) that
    appear anywhere in the answer. A low score signals topic drift.
    """
    if not answer or not question:
        return 0.0
    question_tokens = {t for t in question.lower().split() if len(t) > 3}
    answer_tokens = set(answer.lower().split())
    if not question_tokens:
        return 1.0
    return len(question_tokens & answer_tokens) / len(question_tokens)
