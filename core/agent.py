"""Base agent: a Telegram bot wired to an LLM with shared group memory."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import ClassVar

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatAction, ChatType
from aiogram.types import Message

from core.memory import Memory, StoredMessage
from core.triggers import is_for_agent, strip_mention
from llms.base import ChatMessage
from llms.router import llm_for
from settings import HISTORY_LIMIT, ROOT

logger = logging.getLogger(__name__)

TELEGRAM_MSG_LIMIT = 4000  # safe margin under Telegram's 4096 hard limit
TYPING_REFRESH_SECONDS = 4  # Telegram's chat-action expires after ~5s


class BaseAgent:
    """Subclass must set `name` and `prompt_file`."""

    name: str = ""
    prompt_file: str = ""
    # Short Uzbek line sent immediately on trigger, later replaced
    # by the LLM's actual response via `message.edit_text()`.
    thinking_text: str = "...o'ylab ko'rayapman"

    # Class-level registry: telegram bot user_id -> agent name.
    # Populated as each agent starts; used to label other agents'
    # messages when recording history.
    _agent_usernames: ClassVar[dict[int, str]] = {}

    def __init__(self, token: str, model: str, memory: Memory) -> None:
        if not self.name:
            raise RuntimeError(f"{type(self).__name__}.name must be set")
        if not self.prompt_file:
            raise RuntimeError(f"{type(self).__name__}.prompt_file must be set")

        self.token = token
        self.model = model
        self.memory = memory
        self.bot = Bot(token=token)
        self.dispatcher = Dispatcher()

        self._bot_id: int = 0
        self._username: str = ""
        self._system_prompt: str = ""

        self.dispatcher.message.register(
            self._on_message,
            F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP, ChatType.PRIVATE}),
        )

    def _load_prompt(self) -> str:
        path = Path(self.prompt_file)
        if not path.is_absolute():
            path = ROOT / path
        return path.read_text(encoding="utf-8")

    async def _on_message(self, message: Message) -> None:
        text = message.text or message.caption
        if not text or not message.from_user:
            return

        await self._record(message, text)

        if not is_for_agent(message, self._username, self._bot_id):
            return

        clean_text = strip_mention(text, self._username)
        if not clean_text:
            return

        speaker = message.from_user.username or message.from_user.full_name
        logger.info(
            "[%s] triggered by %s in chat %s: %s",
            self.name,
            speaker,
            message.chat.id,
            clean_text[:80],
        )

        # Quick acknowledgement: shows up immediately, gets edited
        # later with the real response.
        placeholder: Message | None = None
        try:
            placeholder = await message.reply(self.thinking_text)
        except Exception:
            logger.exception("[%s] placeholder reply failed", self.name)

        # Keep Telegram's typing indicator alive while the LLM works.
        typing_task = asyncio.create_task(self._keep_typing(message.chat.id))

        try:
            history = await self._build_history(message.chat.id)
            llm = llm_for(self.model)
            response = await llm.chat(
                system=self._system_prompt,
                messages=history,
                model=self.model,
            )
        except Exception as exc:
            logger.exception("[%s] LLM call failed", self.name)
            await self._finalize_error(message, placeholder, exc)
            return
        finally:
            typing_task.cancel()

        response = (response or "").strip()
        if not response:
            if placeholder is not None:
                try:
                    await placeholder.delete()
                except Exception:
                    logger.debug("[%s] could not delete empty placeholder", self.name)
            return

        await self._deliver(message, placeholder, response)

    async def _keep_typing(self, chat_id: int) -> None:
        """Refresh Telegram's typing indicator while the LLM is busy."""
        try:
            while True:
                try:
                    await self.bot.send_chat_action(chat_id, ChatAction.TYPING)
                except Exception:
                    return
                await asyncio.sleep(TYPING_REFRESH_SECONDS)
        except asyncio.CancelledError:
            pass

    async def _finalize_error(
        self,
        message: Message,
        placeholder: Message | None,
        exc: Exception,
    ) -> None:
        text = _friendly_llm_error(exc)
        if placeholder is not None:
            try:
                await placeholder.edit_text(text)
                return
            except Exception:
                logger.debug("[%s] could not edit placeholder with error", self.name)
        try:
            await message.reply(text)
        except Exception:
            logger.exception("[%s] error reply failed", self.name)

    async def _record(self, message: Message, text: str) -> None:
        user = message.from_user
        if user is None:
            return
        bot_name: str | None = None
        if user.is_bot:
            bot_name = self._agent_usernames.get(user.id)
        try:
            await self.memory.save(
                StoredMessage(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    user_id=user.id,
                    user_name=user.username or user.full_name,
                    is_bot=user.is_bot,
                    bot_name=bot_name,
                    text=text,
                    reply_to_message_id=(
                        message.reply_to_message.message_id
                        if message.reply_to_message
                        else None
                    ),
                )
            )
        except Exception:
            logger.exception("[%s] memory.save failed", self.name)

    async def _build_history(self, chat_id: int) -> list[ChatMessage]:
        rows = await self.memory.recent(chat_id, HISTORY_LIMIT)
        out: list[ChatMessage] = []
        for r in rows:
            # Skip the placeholder ourselves saved as our own message;
            # only the final delivered text should appear in history.
            if r.is_bot and r.user_id == self._bot_id and r.text == self.thinking_text:
                continue
            if r.is_bot and r.user_id == self._bot_id:
                out.append({"role": "assistant", "content": r.text})
            else:
                speaker = r.user_name or "user"
                if r.is_bot and r.bot_name:
                    speaker = f"@{r.bot_name}"
                out.append(
                    {"role": "user", "content": f"{speaker}: {r.text}"}
                )

        while out and out[0]["role"] == "assistant":
            out.pop(0)

        merged: list[ChatMessage] = []
        for m in out:
            if merged and merged[-1]["role"] == m["role"]:
                merged[-1] = {
                    "role": m["role"],
                    "content": merged[-1]["content"] + "\n\n" + m["content"],
                }
            else:
                merged.append(dict(m))
        return merged

    async def _deliver(
        self,
        message: Message,
        placeholder: Message | None,
        text: str,
    ) -> None:
        chunks = split_text(text, TELEGRAM_MSG_LIMIT)
        first = chunks[0]
        rest = chunks[1:]

        sent_first: Message | None = None
        if placeholder is not None:
            try:
                edited = await placeholder.edit_text(first)
                # edit_text returns Message for chat messages, bool for inline
                sent_first = edited if isinstance(edited, Message) else placeholder
            except Exception:
                logger.warning(
                    "[%s] placeholder edit failed; resending as new",
                    self.name,
                )
                try:
                    await placeholder.delete()
                except Exception:
                    pass
                sent_first = None

        if sent_first is None:
            try:
                sent_first = await message.reply(first)
            except Exception:
                logger.exception("[%s] first reply failed", self.name)
                return

        await self._save_own(sent_first, message.message_id, first)

        for chunk in rest:
            try:
                sent = await message.reply(chunk)
            except Exception:
                logger.exception("[%s] reply chunk failed", self.name)
                continue
            await self._save_own(sent, message.message_id, chunk)

    async def _save_own(
        self,
        sent: Message,
        reply_to: int,
        text: str,
    ) -> None:
        try:
            await self.memory.save(
                StoredMessage(
                    chat_id=sent.chat.id,
                    message_id=sent.message_id,
                    user_id=self._bot_id,
                    user_name=self._username,
                    is_bot=True,
                    bot_name=self.name,
                    text=text,
                    reply_to_message_id=reply_to,
                )
            )
        except Exception:
            logger.exception("[%s] saving own reply failed", self.name)

    async def start(self) -> None:
        self._system_prompt = self._load_prompt()
        me = await self.bot.get_me()
        self._bot_id = me.id
        self._username = me.username or ""
        BaseAgent._agent_usernames[me.id] = self.name
        logger.info("[%s] started polling as @%s", self.name, self._username)
        try:
            await self.dispatcher.start_polling(self.bot, handle_signals=False)
        finally:
            await self.bot.session.close()


def _friendly_llm_error(exc: Exception) -> str:
    """Map a raw LLM exception to an Uzbek user-facing message."""
    text = str(exc).lower()
    if "503" in text or "unavailable" in text or "overload" in text:
        return (
            "Hozir model band (server overload). "
            "Bir necha daqiqadan keyin qayta yozing."
        )
    if (
        "429" in text
        or "rate limit" in text
        or "quota" in text
        or "resource_exhausted" in text
    ):
        return (
            "API limit oshdi. Kunlik kvota tugagan bo'lishi mumkin. "
            "`.env`'da kuchsizroq model tanlang (masalan, DEV_MODEL=gemini-2.5-flash) "
            "yoki ertaga qayta urinib ko'ring."
        )
    if (
        "401" in text
        or "403" in text
        or "unauthorized" in text
        or "permission_denied" in text
    ):
        return (
            "API kalit noto'g'ri yoki ruxsat yo'q. "
            "`.env`'dagi `GOOGLE_API_KEY` (yoki tegishli kalit)ni tekshiring."
        )
    if "timeout" in text or "timed out" in text:
        return "So'rov vaqti tugadi. Qayta yozing."
    return "Kechirasiz, javob olib bo'lmadi (LLM xatosi). Qayta yozing."


def split_text(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    while text:
        if len(text) <= limit:
            parts.append(text)
            break
        cut = text.rfind("\n", 0, limit)
        if cut <= 0:
            cut = text.rfind(" ", 0, limit)
        if cut <= 0:
            cut = limit
        parts.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    return parts
