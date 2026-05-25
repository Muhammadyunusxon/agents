"""Message history Protocol and backend factory.

The MVP supports two backends, selected by `DB_KIND`:
- `sqlite`: local file via aiosqlite (default; zero setup)
- `postgres`: hosted Postgres via asyncpg (e.g. Supabase)

Both implementations expose the same `Memory` Protocol, so agent code
is backend-agnostic.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class StoredMessage:
    chat_id: int
    message_id: int
    user_id: int
    user_name: str | None
    is_bot: bool
    bot_name: str | None
    text: str
    reply_to_message_id: int | None


class Memory(Protocol):
    async def save(self, msg: StoredMessage) -> None:
        ...

    async def recent(self, chat_id: int, limit: int) -> list[StoredMessage]:
        ...


def create_memory(
    kind: str,
    *,
    sqlite_path: Path | None = None,
    dsn: str | None = None,
) -> Memory:
    """Return the Memory implementation matching `kind`.

    Lazy-imports the backend module so we do not require both
    dependencies installed when only one is used.
    """
    kind = (kind or "sqlite").lower()

    if kind == "sqlite":
        if not sqlite_path:
            raise RuntimeError("DB_KIND=sqlite requires DB_PATH in .env")
        from core.memory_sqlite import SQLiteMemory
        return SQLiteMemory(sqlite_path)

    if kind == "postgres":
        if not dsn:
            raise RuntimeError("DB_KIND=postgres requires DATABASE_URL in .env")
        from core.memory_postgres import PostgresMemory
        return PostgresMemory(dsn)

    raise ValueError(f"unknown DB_KIND: {kind!r} (use 'sqlite' or 'postgres')")
