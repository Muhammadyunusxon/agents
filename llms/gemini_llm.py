"""Google Gemini wrapper using the google-genai SDK.

Gemini's free tier (AI Studio) is generous for personal-scale bots:
no credit card required, ~15 RPM and ~1500 daily requests for the
2.5-flash model.

Note: Gemini uses "model" instead of "assistant" for the bot side
of the conversation; we translate from our internal ChatMessage
format on the way in.

Transient 5xx errors are retried with exponential backoff because
Google occasionally returns `503 UNAVAILABLE` ("high demand") on
the free tier.
"""
from __future__ import annotations

import asyncio
import logging

from google import genai
from google.genai import errors, types

from llms.base import ChatMessage

logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 4096
TRANSIENT_CODES = (500, 502, 503, 504)
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 2


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

        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                response = await self.client.aio.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                return response.text or ""
            except errors.APIError as exc:
                last_exc = exc
                code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                if code in TRANSIENT_CODES and attempt < MAX_RETRIES - 1:
                    wait = BASE_BACKOFF_SECONDS * (2 ** attempt)
                    logger.warning(
                        "gemini %s on %s, retrying in %ds (attempt %d/%d)",
                        code, model, wait, attempt + 1, MAX_RETRIES,
                    )
                    await asyncio.sleep(wait)
                    continue
                raise

        assert last_exc is not None  # for type narrowing
        raise last_exc
