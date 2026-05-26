"""Pick an LLM provider based on model name prefix.

Each provider is lazy-imported so users who only configure one
backend do not need every SDK installed.
"""
from __future__ import annotations

from llms.base import LLM
from settings import ANTHROPIC_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY

_anthropic: LLM | None = None
_openai: LLM | None = None
_gemini: LLM | None = None


def llm_for(model: str) -> LLM:
    global _anthropic, _openai, _gemini

    if model.startswith("claude-"):
        if not ANTHROPIC_API_KEY:
            raise RuntimeError(
                f"ANTHROPIC_API_KEY is not set; cannot use model {model}"
            )
        if _anthropic is None:
            from llms.anthropic_llm import AnthropicLLM
            _anthropic = AnthropicLLM(ANTHROPIC_API_KEY)
        return _anthropic

    if model.startswith("gemini-"):
        if not GOOGLE_API_KEY:
            raise RuntimeError(
                f"GOOGLE_API_KEY is not set; cannot use model {model}"
            )
        if _gemini is None:
            from llms.gemini_llm import GeminiLLM
            _gemini = GeminiLLM(GOOGLE_API_KEY)
        return _gemini

    if model.startswith(("gpt-", "o1", "o3", "o4")):
        if not OPENAI_API_KEY:
            raise RuntimeError(
                f"OPENAI_API_KEY is not set; cannot use model {model}"
            )
        if _openai is None:
            from llms.openai_llm import OpenAILLM
            _openai = OpenAILLM(OPENAI_API_KEY)
        return _openai

    raise ValueError(f"unknown model provider for: {model}")
