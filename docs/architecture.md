# Architecture

## Overview

Four separate Telegram bots join one group chat. Each bot represents one agent (role). Users address an agent via `@mention`. Agents can also mention each other to form a handoff chain.

## Components

```
┌──────────────────────────────────────────────────────────────┐
│                    run.py (entrypoint)                        │
│  asyncio.gather(pm.start(), dev.start(), qa.start(), ...)    │
└──────────────────────────────────────────────────────────────┘
                              │
        ┌─────────┬───────────┼───────────┬─────────┐
        ▼         ▼           ▼           ▼         ▼
     PM Agent  Dev Agent   QA Agent  Designer    [...]
        │         │           │           │
        └─────────┴───────────┼───────────┴─────────┘
                              ▼
                  ┌───────────────────────┐
                  │   core/agent.py       │
                  │   BaseAgent           │  (shared logic)
                  │   - poll handler      │
                  │   - mention / reply   │
                  │   - LLM call          │
                  │   - history store     │
                  └───────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        core/memory.py   core/triggers.py   llms/*
        (Protocol +      mention parser     Claude / OpenAI
         backends)
              │
        ┌─────┴──────┐
        ▼            ▼
   SQLite         Postgres
   (aiosqlite)    (asyncpg, e.g. Supabase)
```

## Component responsibilities

| Component | Responsibility |
|---|---|
| `run.py` | Launch all bots in parallel via `asyncio.gather`; create memory backend; handle graceful shutdown |
| `settings.py` | Read tokens, model mapping, DB kind, and connection info from `.env` |
| `core/agent.py:BaseAgent` | Manage `Bot` + `Dispatcher`, register handlers, call LLM, send replies |
| `core/memory.py` | `StoredMessage` dataclass; `Memory` Protocol; `create_memory()` factory |
| `core/memory_sqlite.py` | `SQLiteMemory` implementation (default, local) |
| `core/memory_postgres.py` | `PostgresMemory` implementation (hosted, e.g. Supabase) |
| `core/triggers.py` | Detect mentions and replies; decide if a message targets this bot |
| `llms/base.py` | `LLM` protocol: `async chat(system, messages, model) -> str` |
| `llms/anthropic_llm.py` | Claude API wrapper |
| `llms/openai_llm.py` | OpenAI API wrapper |
| `llms/router.py` | Pick provider by model name prefix |
| `bots/<name>.py` | Concrete agent: name, prompt file, optional extra tools |
| `prompts/<name>.md` | System prompt (role, output format, handoff rules) |

## Data flow

1. **User writes:** `@dev_bot please write the login screen`
2. **Telegram polling:** the Dev bot receives the message (aiogram long polling)
3. **Trigger check:** `core/triggers.py` decides if the message targets our bot (mention or reply)
4. **History build:** the configured `Memory` backend fetches the last N messages (default: 20) from the group
5. **LLM call:** `llms/anthropic_llm.py`:
   - system prompt (`prompts/developer.md`)
   - history (role/content pairs, including the new user message just recorded)
6. **Reply:** Dev calls `message.reply(text)`
7. **Save:** the new user message and the bot reply are written via `Memory.save()`
8. **Handoff:** if Dev's reply mentions `@qa_bot`, the QA bot triggers automatically (starting at step 3)

## How multiple bots react to one message

If a message mentions `@pm_bot @dev_bot`, both will reply. The MVP accepts this because it is useful for chained collaboration. A turn-taking rule may be added later.

Avoiding echo loops:

- A bot does not reply to its OWN messages (`message.from_user.id == self.bot.id` is filtered out)
- A bot DOES reply when mentioned by ANOTHER bot (this is what enables the chain)

## Privacy mode

BotFather, select bot, `/setprivacy`, **Disable**.

Without disabling privacy, the bot only sees messages that mention it directly and cannot build group context (including other agents' replies).

## Concurrency model

- One Python process, one asyncio event loop
- One `aiogram.Bot` and `aiogram.Dispatcher` per agent
- LLM calls are async (`anthropic.AsyncAnthropic`, `openai.AsyncOpenAI`)
- Memory backends are async:
  - SQLite: per-call short-lived connections via `aiosqlite`
  - Postgres: a single shared `asyncpg.Pool` (min 1, max 10 connections), lazily created on first save/recent
- Per incoming message: sequential within a single agent (read history, call LLM, reply, save)

## Context window

- Default: the last 20 messages in the group (~2-4k tokens)
- If the LLM context overflows: drop older messages (count-based, sufficient for MVP)
- To shrink the window, lower `HISTORY_LIMIT` in `settings.py`

## Storage backend

The MVP supports two backends, chosen via `DB_KIND` in `.env`:

| Kind | Driver | Use case |
|---|---|---|
| `sqlite` (default) | `aiosqlite` | Local dev; offline; zero setup |
| `postgres` | `asyncpg` | Hosted (e.g. Supabase); multi-device; production |

Both expose the same `Memory` Protocol (`save()`, `recent()`), so the agent code is backend-agnostic. The factory `create_memory(kind, ...)` returns the right implementation and lazily imports its dependency.

### SQLite schema (`core/memory_sqlite.py`)

```sql
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    user_name TEXT,
    is_bot INTEGER NOT NULL DEFAULT 0,
    bot_name TEXT,
    text TEXT NOT NULL,
    reply_to_message_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### Postgres schema (`core/memory_postgres.py`)

```sql
CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    user_name TEXT,
    is_bot BOOLEAN NOT NULL DEFAULT FALSE,
    bot_name TEXT,
    text TEXT NOT NULL,
    reply_to_message_id BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Both backends create the same two indexes:

- `idx_messages_chat_created` for history retrieval (chat + recency)
- `uq_messages_chat_msg` (unique) for dedup when multiple bots receive the same group message
  - SQLite: `INSERT OR IGNORE`
  - Postgres: `INSERT ... ON CONFLICT (chat_id, message_id) DO NOTHING`

### Migration between backends

The schemas are equivalent but data is NOT auto-migrated. Each backend stores history independently. If you switch `DB_KIND`, expect agents to start with no group context until new messages arrive.

For a one-time migration (e.g. SQLite -> Postgres), export from one and `COPY` / `INSERT` into the other manually. Not provided as a built-in script in the MVP.

## MVP limitations

- Designed for a single group chat (no multi-tenancy)
- Telegram message limit of 4096 chars; long replies are split (`core/agent.py:split_text`)
- Text only (no images, files, voice)
- No rate limiting (personal use)
- No auth: anyone in the group can address any bot
- Minimal test layer (unit tests with mocked LLM are sufficient for MVP)
- No backend-to-backend migration tooling
