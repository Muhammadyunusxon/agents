# Telegram Chat Dev Team

A virtual dev team in Telegram: four agent bots (PM, Developer, QA, Designer) collaborate in a single group chat. Users address agents via `@mention`; agents hand off to each other by mentioning the next role.

## Stack

- Python 3.11+, aiogram 3.x (Telegram)
- LLM router (chosen by model name prefix):
  - Google Gemini via `google-genai` (default; free tier; `gemini-*`)
  - Anthropic Claude via `anthropic` (paid; `claude-*`)
  - OpenAI via `openai` (paid; `gpt-*`, `o1-*`, `o3-*`, `o4-*`)
- Memory backend: SQLite via `aiosqlite` (default) or Postgres via `asyncpg` (e.g. Supabase)
- `python-dotenv` for env loading

## Layout

- `bots/`: one file per agent; each subclasses `core/agent.py:BaseAgent`
- `core/`: agent base, memory Protocol + backends, trigger detection
  - `core/memory.py`: `StoredMessage`, `Memory` Protocol, `create_memory()` factory
  - `core/memory_sqlite.py`, `core/memory_postgres.py`: backend implementations
- `llms/`: LLM providers (Anthropic, OpenAI) implementing `llms/base.py:LLM`
- `prompts/`: system prompt per agent (markdown, written in Uzbek so the bot replies in Uzbek)
- `run.py`: entry point; launches all agents in parallel via `asyncio.gather`
- `settings.py`: reads `.env`, exposes per-agent token, model, and DB config
- `data/`: SQLite file (gitignored; only used when `DB_KIND=sqlite`)
- `docs/`: full project documentation (English)

## Key documents

- [docs/architecture.md](docs/architecture.md): system design and components
- [docs/setup.md](docs/setup.md): BotFather setup, local run, optional Supabase
- [docs/agents.md](docs/agents.md): each agent's role, model, prompt
- [docs/development.md](docs/development.md): adding agents, conventions, debugging

## Conventions

- User-facing chat (with the human author): Uzbek
- Documentation (`CLAUDE.md`, `docs/`, any `README.md`): English
- Code, identifiers, comments: English
- System prompts (`prompts/*.md`): Uzbek (they instruct the bot to reply in Uzbek)
- Bot user-facing replies: Uzbek (unless a prompt says otherwise)
- Never commit `.env`; only `.env.example`
- Never log bot tokens, API keys, or `DATABASE_URL`
- No emojis (in code, prompts, or replies)
- Async everywhere; no blocking I/O on the event loop
- Commits are author-only; no `Co-Authored-By` footer
- Memory backend is configurable: keep `Memory` Protocol-compatible when changing internals

## Running locally

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in tokens and API keys
python run.py
```

Default backend is SQLite. To switch to Supabase, set `DB_KIND=postgres` and `DATABASE_URL` in `.env`; see [docs/setup.md](docs/setup.md).

## Testing

- Local: `python run.py`, add all four bots to a Telegram group, mention them
- Unit: `pytest tests/` (with mocked LLM)
- Single agent: `python -m bots.developer`

## Don'ts

- Do not leave BotFather privacy mode `Enable`; the bot will not see group messages
- Do not send LLM output to Telegram unchecked; first verify length (4096 char limit) and parse mode
- Do not hard-code API keys, tokens, or `DATABASE_URL` in source; load only from `.env`
- Two bots must not respond to the same message simultaneously; trigger rules live in `core/triggers.py`
- No synchronous `time.sleep` in `run.py`; use `asyncio.sleep`

## Project status

MVP stage. Single group chat, text only, no rate limiting. SQLite and Postgres backends both supported.
