"""Google Gemini wrapper using the google-genai SDK.

Gemini's free tier (AI Studio) is generous for personal-scale bots:
no credit card required, ~15 RPM and ~1500 daily requests for the
2.5-flash model.

Note: Gemini uses "model" instead of "assistant" for the bot side
of the conversation; we translate from our internal ChatMessage
format on the way in.
"""
from __future__ import annotations

import logging

from google import genai
from google.genai import types

from llms.base import ChatMessage

logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 4096


class GeminiLLM:
    def __init__(self, api_key: str) -> None:
        self.client = genai.Client(api_key=api_key)

    async def chat(
        self,
        system: str,
        messages: list[ChatMessage],
        model: str,
    ) -> str:
        contents = [
            types.Content(
                role="model" if m["role"] == "assistant" else "user",
                parts=[types.Part(text=m["content"])],
            )
            for m in messages
        ]
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )
        response = await self.client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
        return response.text or ""
