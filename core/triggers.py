"""Decide whether a Telegram message should trigger a given agent."""
from __future__ import annotations

import re

from aiogram.types import Message


def is_for_agent(message: Message, bot_username: str, self_bot_id: int) -> bool:
    """True if the message targets our bot via @mention or reply-to-us."""
    if message.from_user and message.from_user.id == self_bot_id:
        return False

    if (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == self_bot_id
    ):
        return True

    text = message.text or message.caption or ""
    if text and _contains_mention(text, bot_username):
        return True

    return False


def _contains_mention(text: str, username: str) -> bool:
    if not username:
        return False
    pattern = rf"(?<!\w)@{re.escape(username)}\b"
    return bool(re.search(pattern, text, re.IGNORECASE))


def strip_mention(text: str, username: str) -> str:
    if not username:
        return text.strip()
    pattern = rf"(?<!\w)@{re.escape(username)}\b"
    return re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
