# Development

## Lokal workflow

```bash
source .venv/bin/activate
python run.py
```

To'rtta bot bitta jarayonda parallel ishlaydi. Loglar konsolga chiqadi. To'xtatish: `Ctrl+C` (asyncio barcha botni tozalab yopadi).

## Yangi agent qo'shish

Misol: `Architect` agentni qo'shaylik.

1. **BotFather:** yangi bot oching (`@myname_architect_bot`), privacy `disable`
2. **`.env` va `.env.example`'ga qo'shing:**
   ```env
   ARCHITECT_BOT_TOKEN=...
   ARCHITECT_MODEL=claude-opus-4-7
   ```
3. **`prompts/architect.md`** yozing (struktura uchun [agents.md](agents.md#prompt-strukturasi) ga qarang)
4. **`bots/architect.py`:**
   ```python
   from core.agent import BaseAgent

   class ArchitectAgent(BaseAgent):
       name = "architect"
       prompt_file = "prompts/architect.md"
   ```
5. **`settings.py`'ga model mapping qo'shing:**
   ```python
   AGENT_MODELS["architect"] = os.getenv("ARCHITECT_MODEL", "claude-opus-4-7")
   AGENT_TOKENS["architect"] = os.getenv("ARCHITECT_BOT_TOKEN")
   ```
6. **`run.py`** ichida ishga tushiring:
   ```python
   architect = ArchitectAgent(token=AGENT_TOKENS["architect"], model=AGENT_MODELS["architect"])
   tasks.append(architect.start())
   ```
7. **[docs/agents.md](agents.md)** ga tavsifni qo'shing
8. Telegram guruhga yangi botni qo'shing, admin qiling

## LLM provider qo'shish

`llms/base.py:LLM` protokoliga rioya qiluvchi yangi sinf yozing:

```python
from typing import Protocol

class LLM(Protocol):
    async def chat(
        self,
        system: str,
        messages: list[dict],   # [{"role": "user"|"assistant", "content": str}, ...]
        model: str,
    ) -> str: ...
```

Keyin `core/agent.py`'da router'ga ulang (model nomidan provider topish, masalan `claude-*` -> Anthropic, `gpt-*` -> OpenAI, `gemini-*` -> Google).

## Konvensiyalar

| Maydon | Qoida |
|---|---|
| Til (kod, comment, identifier) | Ingliz tilida |
| Til (bot javoblari) | O'zbekcha (prompt'da aniqlangan) |
| Import | Absolute (`from core.agent import ...`) |
| Async | Hamma I/O async; `time.sleep` o'rniga `asyncio.sleep` |
| Type hints | Public funksiya va sinflarda majburiy |
| Logging | `logging` modul; `LOG_LEVEL` env orqali boshqariladi |
| Loglashda taqiq | Token, API kalit, to'liq prompt mazmuni |
| Commit message | Imperative mood, qisqa: `add qa agent`, `fix mention parsing` |
| Branch | Hozircha hammasi `main`'da (MVP, bitta dev) |

## Test

```bash
pytest tests/ -v
```

| Daraja | Yondashuv |
|---|---|
| Unit | LLM chaqirig'i `AsyncMock` bilan mock qilinadi |
| Trigger | `core/triggers.py` toza, `Message` mock'lari bilan testlash oson |
| Memory | SQLite'ni `:memory:` bilan ishlatish, oraliq xabar yozish va o'qish |
| Integration | Real test bot bilan (BotFather'da alohida `@test_pm_bot` oching) |
| Manual | `python run.py` va Telegram guruh |

## Debug

| Vaziyat | Buyruq |
|---|---|
| Bitta bot ishini tekshirish | `python -m bots.developer` (alohida ishga tushadi) |
| To'liq LLM kontekstini ko'rish | `LOG_LEVEL=DEBUG python run.py` |
| SQLite tarixini ko'rish | `sqlite3 data/memory.sqlite "SELECT bot_name, substr(text,1,80) FROM messages ORDER BY id DESC LIMIT 20;"` |
| Webhook xato | Polling rejimida webhook ishlatilmaydi; `getUpdates` chaqirig'i ishlaydi |
| Telegram API limit | Aiogram avtomatik backoff qiladi; agar tez-tez bo'lsa, `HISTORY_LIMIT`'ni pasaytiring (kamroq parallel chaqiriq) |

## Git

`.gitignore`'da bo'lishi kerak:

```
.venv/
__pycache__/
*.pyc
.env
data/
.idea/
.DS_Store
```

## Performance kuzatish (kelajak)

- Token sarfi: har LLM chaqiriqdan keyin `usage` log'lash
- Latency: chaqiriq vaqtini o'lchash, agar 10s'dan oshsa eskartirish
- DB hajmi: oylik bir marta eski xabarlarni arxivlash (hozir kerak emas)

## Yo'l xaritasi

| Bosqich | Mazmun |
|---|---|
| MVP (hozir) | 4 bot, bitta guruh, matn, mention-asoslangan trigger |
| v0.2 | Rate limit, xato qayta urinish (retry), uzun xabar splitter |
| v0.3 | Tool use (Dev fayl yozish, QA test ishga tushirish) |
| v0.4 | Multi-group support, har guruh uchun alohida proyekt holati |
| v0.5 | Web dashboard (kuzatish, prompt tahrirlash) |
