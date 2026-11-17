"""Write an answer that can be traced to retrieved passages."""

from docreader.application.search import RetrievedSegment
from docreader.infrastructure.chat import ChatClient

NO_MATCH_ANSWER = "I cannot find this in the uploaded documents."


def build_grounding_prompt(
    question: str,
    matches: list[RetrievedSegment],
) -> tuple[str, str]:
    """Build the system and user prompts for one grounded answer."""
    system_prompt = (
        "Answer the question using only the passages below. "
        "If the passages do not contain the answer, say you cannot find it "
        "in the documents. Cite each claim as [filename:line_start-line_end]."
    )
    passages = "\n\n".join(
        (f"[{match.filename}:{match.line_start}-{match.line_end}]\n{match.content}")
        for match in matches
    )
    user_prompt = f"Question: {question}\n\nPassages:\n{passages}"
    return system_prompt, user_prompt


async def answer_question(
    chat: ChatClient,
    question: str,
    matches: list[RetrievedSegment],
) -> str:
    """Ask the chat model to answer from the retrieved passages."""
    if not matches:
        return NO_MATCH_ANSWER
    system_prompt, user_prompt = build_grounding_prompt(question, matches)
    return await chat.complete(system_prompt, user_prompt)
