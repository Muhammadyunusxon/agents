"""Pick an LLM provider based on model name prefix."""
from __future__ import annotations

from llms.anthropic_llm import AnthropicLLM
from llms.base import LLM
from llms.openai_llm import OpenAILLM
from settings import ANTHROPIC_API_KEY, OPENAI_API_KEY

_anthropic: AnthropicLLM | None = None
_openai: OpenAILLM | None = None


def llm_for(model: str) -> LLM:
    global _anthropic, _openai

    if model.startswith("claude-"):
        if not ANTHROPIC_API_KEY:
            raise RuntimeError(
                f"ANTHROPIC_API_KEY is not set; cannot use model {model}"
            )
        if _anthropic is None:
            _anthropic = AnthropicLLM(ANTHROPIC_API_KEY)
        return _anthropic

    if model.startswith(("gpt-", "o1", "o3", "o4")):
        if not OPENAI_API_KEY:
            raise RuntimeError(
                f"OPENAI_API_KEY is not set; cannot use model {model}"
            )
        if _openai is None:
            _openai = OpenAILLM(OPENAI_API_KEY)
        return _openai

    raise ValueError(f"unknown model provider for: {model}")
