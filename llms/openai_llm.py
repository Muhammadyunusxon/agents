"""OpenAI wrapper."""
from __future__ import annotations

import logging

from openai import AsyncOpenAI

from llms.base import ChatMessage

logger = logging.getLogger(__name__)


class OpenAILLM:
    def __init__(self, api_key: str) -> None:
        self.client = AsyncOpenAI(api_key=api_key)

    async def chat(
        self,
        system: str,
        messages: list[ChatMessage],
        model: str,
    ) -> str:
        payload: list[dict] = [{"role": "system", "content": system}]
        payload.extend({"role": m["role"], "content": m["content"]} for m in messages)
        response = await self.client.chat.completions.create(
            model=model,
            messages=payload,
        )
        return response.choices[0].message.content or ""
