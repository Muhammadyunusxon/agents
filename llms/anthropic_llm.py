"""Anthropic Claude wrapper."""
from __future__ import annotations

import logging

from anthropic import AsyncAnthropic

from llms.base import ChatMessage

logger = logging.getLogger(__name__)

MAX_TOKENS = 4096


class AnthropicLLM:
    def __init__(self, api_key: str) -> None:
        self.client = AsyncAnthropic(api_key=api_key)

    async def chat(
        self,
        system: str,
        messages: list[ChatMessage],
        model: str,
    ) -> str:
        response = await self.client.messages.create(
            model=model,
            system=system,
            messages=messages,
            max_tokens=MAX_TOKENS,
        )
        parts = [b.text for b in response.content if getattr(b, "type", "") == "text"]
        return "".join(parts)
