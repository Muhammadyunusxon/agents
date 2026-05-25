"""LLM provider protocol."""
from __future__ import annotations

from typing import Protocol, TypedDict


class ChatMessage(TypedDict):
    role: str  # "user" or "assistant"
    content: str


class LLM(Protocol):
    async def chat(
        self,
        system: str,
        messages: list[ChatMessage],
        model: str,
    ) -> str:
        ...
