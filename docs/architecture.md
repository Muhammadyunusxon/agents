# Arxitektura

## Umumiy g'oya

4 ta alohida Telegram bot bitta guruh chatga qo'shiladi. Har bot bitta agentni (rol) ifodalaydi. Foydalanuvchi `@mention` orqali kerakli agentni chaqiradi. Agentlar bir-birini ham mention qila oladi; bu estafeta hosil qiladi.

## Komponentlar

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
                  │   BaseAgent           │  (umumiy logika)
                  │   - poll handler      │
                  │   - mention/reply     │
                  │   - LLM call          │
                  │   - history store     │
                  └───────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        core/memory.py   core/triggers.py   llms/*
        SQLite           mention parse      Claude / OpenAI
```

## Komponentlar javobgarligi

| Komponent | Javobgarlik |
|---|---|
| `run.py` | 4 botni asyncio.gather bilan parallel ishga tushirish, signal handling, graceful shutdown |
| `settings.py` | `.env`'dan tokenlar, model mapping, DB path o'qish |
| `core/agent.py:BaseAgent` | Bot + Dispatcher boshqaruvi, message handler ulash, LLM chaqirish, javob yuborish |
| `core/memory.py` | SQLite ulanish, xabar yozish/o'qish, kontekst yig'ish (so'nggi N xabar) |
| `core/triggers.py` | Xabarda mention bormi, reply kimga, bu botga tegishlimi (filter) |
| `llms/base.py` | `LLM` protokoli: `async chat(system, messages, model) -> str` |
| `llms/anthropic_llm.py` | Claude API wrapper |
| `llms/openai_llm.py` | OpenAI API wrapper |
| `bots/<name>.py` | Konkret agent: nom, prompt fayli, ehtimol qo'shimcha tool'lar |
| `prompts/<name>.md` | System prompt (rol, format, estafeta qoidalari) |

## Ma'lumot oqimi

1. **Foydalanuvchi yozadi:** `@dev_bot login ekranini yoz`
2. **Telegram polling:** Dev bot xabarni oladi (`aiogram` long polling)
3. **Trigger check:** `core/triggers.py` aniqlaydi:
   - Bu xabar Dev'ga qaratilganmi? (mention yoki reply)
   - Reply'da bo'lsa, kimning xabariga?
4. **History yig'ish:** `core/memory.py` so'nggi N (default: 20) xabarni guruh tarixidan oladi
5. **LLM chaqiriq:** `llms/anthropic_llm.py`:
   - System prompt (`prompts/developer.md`)
   - History (role/content juftlari)
   - Yangi user xabar
6. **Javob yuborish:** Dev bot `message.reply(text)` qiladi
7. **History saqlash:** Yangi user xabar va bot javobi SQLite'ga yoziladi
8. **Estafeta:** Agar Dev javobida `@qa_bot` mention bo'lsa, QA bot avtomatik trigger bo'ladi (3-bosqichdan boshlab)

## Bir nechta bot bitta xabarga qanday reaksiya qiladi

Risk: bitta xabarda `@pm_bot @dev_bot` ikkalasi mention qilinsa, ikkalasi javob beradi. Bu boshlang'ich MVP'da ruxsat etiladi (zanjir uchun foydali). Kelajakda turn-taking qoidasi qo'shish mumkin.

Echo loop'dan saqlanish:
- Bot O'ZINI mention qilgan xabarga javob bermaydi (`message.from_user.is_bot and message.from_user.id == self.bot.id`)
- Agar boshqa bot bizni mention qilsa, javob beramiz (estafeta)

## Privacy mode

BotFather, bot tanlang, `/setprivacy`, **Disable**.

Busiz bot faqat o'ziga mention bo'lgan xabarlarni ko'radi va guruh kontekstini yig'a olmaydi (boshqa botlarning javoblarini ham ko'rmaydi).

## Konkurensiya modeli

- Bitta Python jarayoni, bitta asyncio event loop
- Har bot uchun alohida `aiogram.Bot` va `aiogram.Dispatcher` instansiyasi
- LLM chaqiriqlari async (`anthropic.AsyncAnthropic`, `openai.AsyncOpenAI`)
- SQLite `aiosqlite` orqali, bitta yozish navbati (lock yo'q, single writer)
- Bitta xabar uchun bitta agent ichida ketma-ket: history o'qish, LLM, javob, history yozish

## Kontekst hajmi

- Default: guruhdagi so'nggi 20 ta xabar (taxminan 2-4k token)
- LLM context'ga sig'masa: eski xabarlardan trim qilish (token counter bilan emas, xabar soni bilan, MVP uchun yetarli)
- Agar token limiti yetmasa: `settings.py:HISTORY_LIMIT`'ni pasaytirish

## Saqlash sxemasi (SQLite)

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    user_name TEXT,
    is_bot INTEGER NOT NULL DEFAULT 0,
    bot_name TEXT,           -- agent nomi (pm/dev/qa/designer), bot bo'lmasa NULL
    text TEXT NOT NULL,
    reply_to_message_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_chat_created ON messages(chat_id, created_at DESC);
```

## Cheklovlar (MVP)

- Faqat bitta guruh chatda ishlashi nazarda tutilgan (multi-tenancy yo'q)
- Telegram xabar limiti 4096 belgi; uzun javob bo'laklarga bo'linadi (`split_long_text`)
- Faqat matn (tasvir/fayl/voice yo'q)
- Rate limit yo'q (shaxsiy ishlatish uchun)
- Auth yo'q: guruhdagi har kim har botga murojaat qila oladi
- Test qatlami minimal (LLM mock bilan unit testlar yetarli MVP uchun)
