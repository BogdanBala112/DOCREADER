"""RAGAS-powered semantic evaluation of the RAG pipeline.

RAGAS uses an LLM as a judge to score three dimensions:

  Faithfulness       — are all claims in the answer supported by the retrieved
                       passages? (detects hallucination)
  ResponseRelevancy  — does the answer actually address the question?
                       (detects topic drift)
  ContextPrecision   — are the most relevant passages ranked highest?
                       (detects retrieval ordering problems; needs a reference)

Usage
-----
Install the eval dependency group first:

    uv sync --group eval

Then run from a script or notebook with a running LM Studio instance:

    from docreader.core.config import get_settings
    from docreader.evaluation.ragas_eval import (
        EvalInput, make_ragas_llm, run_ragas_evaluation,
    )

    settings = get_settings()
    llm = make_ragas_llm(
        settings.chat_base_url, settings.chat_api_key, settings.chat_model
    )
    scores = await run_ragas_evaluation(inputs, llm)
    print(scores)  # {"faithfulness": 0.91, "response_relevancy": 0.87, ...}
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from docreader.application.search import RetrievedSegment


@dataclass(frozen=True)
class EvalInput:
    """One complete Q&A exchange ready for RAGAS scoring.

    Attributes
    ----------
    question:
        The natural-language question posed to the system.
    answer:
        The answer the pipeline produced.
    segments:
        The passages retrieved from the vector store.
    reference:
        Optional ground-truth answer. Required for ContextPrecision /
        ContextRecall metrics; omit for Faithfulness + ResponseRelevancy.
    """

    question: str
    answer: str
    segments: list[RetrievedSegment] = field(default_factory=list)
    reference: str | None = None


def build_ragas_dataset(inputs: Sequence[EvalInput]):  # -> EvaluationDataset
    """Convert pipeline outputs into a RAGAS EvaluationDataset.

    Each EvalInput must become one ragas.SingleTurnSample.
    The RAGAS field mapping is:
      user_input         ← input.question
      response           ← input.answer
      retrieved_contexts ← [seg.content for seg in input.segments]
      reference          ← input.reference  (may be None)

    Returns a ragas.EvaluationDataset wrapping the list of samples.
    """
    # TODO(human): implement this function
    # Hint: from ragas import EvaluationDataset, SingleTurnSample
    from ragas import EvaluationDataset, SingleTurnSample

    samples = [
        SingleTurnSample(
            user_input = input.question,
            response = input.answer,
            retrieved_contexts = [seg.content for seg in input.segments],
            reference = input.reference
        )
        for input in inputs
    ]

    return EvaluationDataset(samples = samples)

def make_ragas_llm(base_url: str, api_key: str, model: str):  # -> LangchainLLMWrapper
    """Wrap the project's OpenAI-compatible chat model for use as a RAGAS judge.

    This connects RAGAS to the same LM Studio instance the application uses,
    so no extra API keys or cloud services are required.
    """
    from langchain_openai import ChatOpenAI
    from ragas.llms import LangchainLLMWrapper

    llm = ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=0,
    )
    return LangchainLLMWrapper(llm)


async def run_ragas_evaluation(
    inputs: Sequence[EvalInput],
    llm_wrapper,  # LangchainLLMWrapper
    metrics: list | None = None,
) -> dict[str, float]:
    """Score a batch of Q&A exchanges with RAGAS and return mean scores.

    Parameters
    ----------
    inputs:
        One EvalInput per question-answer pair to evaluate.
    llm_wrapper:
        A LangchainLLMWrapper around the project's chat model.
    metrics:
        RAGAS metric instances to run. Defaults to Faithfulness and
        ResponseRelevancy (no reference answer required). Pass
        ContextPrecision() as well when EvalInput.reference is set.

    Returns
    -------
    dict mapping metric name to its mean score across all inputs, e.g.:
        {"faithfulness": 0.91, "response_relevancy": 0.87}
    """
    from ragas import evaluate
    from ragas.metrics import Faithfulness, ResponseRelevancy

    if metrics is None:
        metrics = [Faithfulness(), ResponseRelevancy()]

    for metric in metrics:
        metric.llm = llm_wrapper

    dataset = build_ragas_dataset(inputs)
    result = evaluate(dataset=dataset, metrics=metrics)
    return result.to_pandas().mean(numeric_only=True).to_dict()
