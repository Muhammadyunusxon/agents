"""Postgres-backed message history via asyncpg.

Designed for Supabase but works with any vanilla Postgres. The
connection pool is created lazily on first use and reused for the
process lifetime.
"""
from __future__ import annotations

import logging

import asyncpg

from core.memory import StoredMessage

logger = logging.getLogger(__name__)


SCHEMA = """
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

CREATE INDEX IF NOT EXISTS idx_messages_chat_created
    ON messages(chat_id, created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_messages_chat_msg
    ON messages(chat_id, message_id);
"""


class PostgresMemory:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def _ensure(self) -> asyncpg.Pool:
        if self._pool is not None:
            return self._pool
        self._pool = await asyncpg.create_pool(
            self.dsn,
            min_size=1,
            max_size=10,
            command_timeout=30,
        )
        async with self._pool.acquire() as conn:
            await conn.execute(SCHEMA)
        return self._pool

    async def save(self, msg: StoredMessage) -> None:
        pool = await self._ensure()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO messages
                    (chat_id, message_id, user_id, user_name,
                     is_bot, bot_name, text, reply_to_message_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (chat_id, message_id) DO NOTHING
                """,
                msg.chat_id,
                msg.message_id,
                msg.user_id,
                msg.user_name,
                msg.is_bot,
                msg.bot_name,
                msg.text,
                msg.reply_to_message_id,
            )

    async def recent(self, chat_id: int, limit: int) -> list[StoredMessage]:
        pool = await self._ensure()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT chat_id, message_id, user_id, user_name,
                       is_bot, bot_name, text, reply_to_message_id
                FROM messages
                WHERE chat_id = $1
                ORDER BY id DESC
                LIMIT $2
                """,
                chat_id,
                limit,
            )
        rows = list(reversed(rows))
        return [
            StoredMessage(
                chat_id=r["chat_id"],
                message_id=r["message_id"],
                user_id=r["user_id"],
                user_name=r["user_name"],
                is_bot=r["is_bot"],
                bot_name=r["bot_name"],
                text=r["text"],
                reply_to_message_id=r["reply_to_message_id"],
            )
            for r in rows
        ]
