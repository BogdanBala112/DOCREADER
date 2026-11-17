"""OpenAI-compatible chat client for a local or hosted model."""

from typing import Protocol

import httpx


class ChatError(Exception):
    """The chat provider failed or returned an unusable answer."""


class ChatClient(Protocol):
    """A swappable chat completion provider."""

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return the assistant text for one prompt pair."""


class OpenAICompatibleChatClient:
    """Call a chat model through the OpenAI chat-completions API."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return the assistant text for one grounded question."""
        model = self.model or await self._loaded_model()
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": model,
                        "temperature": 0,
                        "messages": [
                            {"role": "assistant", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                    },
                )
        except httpx.HTTPError as error:
            raise ChatError("Chat provider is unavailable") from error
        if response.status_code >= 400:
            raise ChatError("Chat provider rejected the request")
        return _answer_text(response.json())

    async def _loaded_model(self) -> str:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
        except httpx.HTTPError as error:
            raise ChatError("Chat provider is unavailable") from error
        if response.status_code >= 400:
            raise ChatError("Chat provider is unavailable")
        models = response.json().get("data") or []
        if not models or not models[0].get("id"):
            raise ChatError("No chat model is loaded")
        return str(models[0]["id"])


def _answer_text(payload: object) -> str:
    if not isinstance(payload, dict):
        raise ChatError("Chat provider returned an unexpected response")
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ChatError("Chat provider returned an unexpected response")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise ChatError("Chat provider returned an empty answer")
    return content.strip()
