"""Load configuration from environment and expose typed config objects."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

_db_raw = os.getenv("DB_PATH", "./data/memory.sqlite")
DB_PATH = Path(_db_raw)
if not DB_PATH.is_absolute():
    DB_PATH = ROOT / DB_PATH
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "20"))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or None
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or None


@dataclass(frozen=True)
class AgentConfig:
    name: str
    token: str
    model: str
    prompt_file: Path


def _maybe_agent(
    name: str,
    token_env: str,
    model_env: str,
    default_model: str,
) -> AgentConfig | None:
    token = os.getenv(token_env)
    if not token:
        return None
    return AgentConfig(
        name=name,
        token=token,
        model=os.getenv(model_env, default_model),
        prompt_file=ROOT / "prompts" / f"{name}.md",
    )


AGENTS: dict[str, AgentConfig] = {}
for _cfg in (
    _maybe_agent("pm", "PM_BOT_TOKEN", "PM_MODEL", "claude-sonnet-4-6"),
    _maybe_agent("developer", "DEV_BOT_TOKEN", "DEV_MODEL", "claude-opus-4-7"),
    _maybe_agent("qa", "QA_BOT_TOKEN", "QA_MODEL", "claude-sonnet-4-6"),
    _maybe_agent("designer", "DESIGNER_BOT_TOKEN", "DESIGNER_MODEL", "gpt-4o"),
):
    if _cfg is not None:
        AGENTS[_cfg.name] = _cfg
