# Development

## Local workflow

```bash
source .venv/bin/activate
python run.py
```

All four bots run in one process. Logs are written to the console. Stop with `Ctrl+C` (asyncio cleanly shuts each bot down).

## Adding a new agent

Example: add an `Architect` agent.

1. **BotFather:** create a new bot (`@myname_architect_bot`); set privacy `Disable`
2. **Update `.env` and `.env.example`:**
   ```env
   ARCHITECT_BOT_TOKEN=...
   ARCHITECT_MODEL=claude-opus-4-7
   ```
3. **Write `prompts/architect.md`** (see the structure in [agents.md](agents.md#prompt-structure))
4. **Create `bots/architect.py`:**
   ```python
   from core.agent import BaseAgent


   class ArchitectAgent(BaseAgent):
       name = "architect"
       prompt_file = "prompts/architect.md"
   ```
5. **Register in `settings.py`:** add to the tuple inside the `AGENTS` loop:
   ```python
   _maybe_agent("architect", "ARCHITECT_BOT_TOKEN", "ARCHITECT_MODEL", "claude-opus-4-7"),
   ```
6. **Wire it up in `run.py`:**
   ```python
   from bots.architect import ArchitectAgent

   AGENT_CLASSES["architect"] = ArchitectAgent
   ```
7. **Document it** in [docs/agents.md](agents.md)
8. Add the new bot to the Telegram group and make it admin

## Adding a new LLM provider

Implement the `llms/base.py:LLM` protocol:

```python
from typing import Protocol


class LLM(Protocol):
    async def chat(
        self,
        system: str,
        messages: list[dict],   # [{"role": "user" | "assistant", "content": str}, ...]
        model: str,
    ) -> str: ...
```

Then plug it into `llms/router.py` (choose the provider by model name prefix, e.g. `gemini-*` -> Google).

## Conventions

| Area | Rule |
|---|---|
| Language (code, comments, identifiers) | English |
| Language (docs, CLAUDE.md, README) | English |
| Language (prompts/*.md) | Uzbek (they instruct the bot in the user's language) |
| Language (bot replies) | Uzbek (set in the prompt) |
| Imports | Absolute (`from core.agent import ...`) |
| Async | All I/O async; never `time.sleep` in handlers, use `asyncio.sleep` |
| Type hints | Required on public functions and classes |
| Logging | `logging` module; level controlled by `LOG_LEVEL`; never log tokens, API keys, or full prompts |
| Commit messages | Imperative mood, short: `add qa agent`, `fix mention parsing` |
| Commit author | Author-only; do not add `Co-Authored-By` footers |
| Branching | All work on `main` for now (MVP, single dev) |

## Testing

```bash
pytest tests/ -v
```

| Layer | Approach |
|---|---|
| Unit | Mock the LLM call with `AsyncMock` |
| Triggers | `core/triggers.py` is pure; easy to test with `Message` mocks |
| Memory | Use `:memory:` SQLite; write and read sample messages |
| Integration | Use a real test bot (create `@test_pm_bot` in BotFather) |
| Manual | `python run.py` and a Telegram group |

## Debugging

| Situation | Command |
|---|---|
| Check a single bot in isolation | `python -m bots.developer` |
| Print the full LLM context | `LOG_LEVEL=DEBUG python run.py` |
| Inspect SQLite history | `sqlite3 data/memory.sqlite "SELECT bot_name, substr(text,1,80) FROM messages ORDER BY id DESC LIMIT 20;"` |
| Webhook errors | This setup uses polling, not webhooks; only `getUpdates` runs |
| Telegram rate limit | aiogram applies automatic backoff; if it happens often, lower `HISTORY_LIMIT` |

## Git

`.gitignore` already excludes:

```
.venv/
__pycache__/
*.pyc
.env
data/
.idea/
.DS_Store
```

## Performance monitoring (future)

- Token spend: log `usage` after each LLM call
- Latency: measure call time; warn if it exceeds 10s
- DB size: monthly archive of old messages (not needed yet)

## Roadmap

| Stage | Scope |
|---|---|
| MVP (now) | Four bots, single group, text, mention-based triggers |
| v0.2 | Rate limiting; retry on transient errors; long-message splitter improvements |
| v0.3 | Tool use (Dev writes files; QA runs tests) |
| v0.4 | Multi-group support; per-group project state |
| v0.5 | Web dashboard (observability, prompt editing) |
