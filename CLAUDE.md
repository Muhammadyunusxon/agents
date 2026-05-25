# Telegram Chat Dev Team

Telegramda 4 ta agent bot (PM, Developer, QA, Designer) bitta guruh chatda hamkorlik qiladi. Foydalanuvchi `@mention` orqali murojaat qiladi; botlar bir-birini chaqirib estafetani uzatadi.

## Stack

- Python 3.11+, aiogram 3.x (Telegram)
- Anthropic Claude API, OpenAI API (router orqali)
- SQLite (guruh chat tarixi), `aiosqlite`
- `python-dotenv` (env yuklash)

## Tuzilma

- `bots/`: har agent uchun bitta fayl, `core/agent.py:BaseAgent`'dan meros oladi
- `core/`: agent asosi, hotira, trigger aniqlash
- `llms/`: LLM provider'lar (Anthropic, OpenAI), umumiy `base.py:LLM` protokoli
- `prompts/`: har agent uchun system prompt (markdown)
- `run.py`: entrypoint, 4 botni `asyncio.gather` orqali ishga tushiradi
- `settings.py`: `.env`'dan token va model mapping
- `data/`: SQLite fayli (gitignore'da)
- `docs/`: to'liq dokumentatsiya

## Asosiy hujjatlar

- [docs/architecture.md](docs/architecture.md): tizim dizayni va komponentlar
- [docs/setup.md](docs/setup.md): BotFather va lokal ishga tushirish
- [docs/agents.md](docs/agents.md): har agent roli, modeli, prompt strategiyasi
- [docs/development.md](docs/development.md): yangi agent qo'shish, konvensiyalar

## Konvensiyalar

- Foydalanuvchi bilan muloqot: o'zbekcha
- Kod, identifier, comment: ingliz tilida
- Botning user-facing javoblari: o'zbekcha (agar prompt boshqacha aytmasa)
- `.env` hech qachon commit qilinmaydi; faqat `.env.example`
- Hech qaysi bot tokeni yoki API kalit log'da chiqmasligi kerak
- Emoji ishlatilmaydi (kod, prompt, javoblar)
- Async hamma joyda: hech qanday blocking I/O

## Ishga tushirish

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # tokenlarni to'ldiring
python run.py
```

## Test

- Lokal: `python run.py`, Telegram guruhga 4 botni qo'shing, mention qiling
- Birlik test: `pytest tests/` (LLM mock bilan)
- Bitta agentni alohida: `python -m bots.developer`

## Don'ts

- BotFather privacy mode'ni `Enable` qoldirmang; bot guruh xabarlarini ko'rmay qoladi
- LLM javobini Telegramga to'g'ridan-to'g'ri yubormang; avval uzunlikni (4096 belgi) va `parse_mode`'ni tekshiring
- API key'ni `settings.py`'da hard-code qilmang; faqat `.env` orqali
- Bitta xabarni ikki bot bir vaqtda javoblamasin; trigger qoidalari `core/triggers.py`'da aniq bo'lishi kerak
- `run.py` ichida sinxron `time.sleep` yo'q; faqat `asyncio.sleep`

## Loyiha holati

MVP bosqichida. Faqat bitta guruh chat, faqat matn, rate limit yo'q.
