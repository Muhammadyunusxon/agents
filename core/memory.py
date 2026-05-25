"""SQLite-backed message history for group chats.

A single shared store across all agents. Each row is identified by
(chat_id, message_id); when multiple bots receive the same group message,
the unique index makes redundant inserts a no-op.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)


SCHEMA = """
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

CREATE INDEX IF NOT EXISTS idx_messages_chat_created
    ON messages(chat_id, created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_messages_chat_msg
    ON messages(chat_id, message_id);
"""


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


class Memory:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._initialized = False

    async def _ensure(self) -> None:
        if self._initialized:
            return
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(SCHEMA)
            await db.commit()
        self._initialized = True

    async def save(self, msg: StoredMessage) -> None:
        await self._ensure()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR IGNORE INTO messages
                    (chat_id, message_id, user_id, user_name,
                     is_bot, bot_name, text, reply_to_message_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    msg.chat_id,
                    msg.message_id,
                    msg.user_id,
                    msg.user_name,
                    int(msg.is_bot),
                    msg.bot_name,
                    msg.text,
                    msg.reply_to_message_id,
                ),
            )
            await db.commit()

    async def recent(self, chat_id: int, limit: int) -> list[StoredMessage]:
        await self._ensure()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT chat_id, message_id, user_id, user_name,
                       is_bot, bot_name, text, reply_to_message_id
                FROM messages
                WHERE chat_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (chat_id, limit),
            )
            rows = await cur.fetchall()
        rows = list(reversed(rows))
        return [
            StoredMessage(
                chat_id=r["chat_id"],
                message_id=r["message_id"],
                user_id=r["user_id"],
                user_name=r["user_name"],
                is_bot=bool(r["is_bot"]),
                bot_name=r["bot_name"],
                text=r["text"],
                reply_to_message_id=r["reply_to_message_id"],
            )
            for r in rows
        ]
