# Setup

## 1. BotFather'da 4 ta bot ochish

[@BotFather](https://t.me/BotFather) bilan har bir agent uchun:

1. `/newbot`, username tanlang (masalan `@myname_pm_bot`)
2. Tokenni nusxalang, keyin `.env`'ga yozasiz
3. `/setprivacy`, bot tanlang, **Disable** (MUHIM, busiz bot guruh xabarlarini ko'rmaydi)
4. (ixtiyoriy) `/setdescription`, `/setuserpic` orqali tasvirlash

Kerakli 4 bot: PM, Developer, QA, Designer.

## 2. API kalitlar

- **Anthropic:** https://console.anthropic.com, API Keys, Create
- **OpenAI** (faqat Designer yoki boshqa rol GPT bo'lsa): https://platform.openai.com/api-keys

## 3. Lokal ishga tushirish

```bash
cd /Users/muhammadyunusxon/StudioProjects/agents

python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env'ni ochib, barcha qiymatlarni to'ldiring

python run.py
```

Konsolda hamma 4 bot `started polling` deb yozsa, tayyor.

## 4. Telegram guruh sozlash

1. Yangi guruh oching (yoki mavjudni ishlatib)
2. **Hamma 4 botni qo'shing:** Add member, har bir bot username'ini yozing
3. Har birini **admin** qiling: Manage group, Administrators, Add Administrator. Faqat admin bot guruh xabarlarini to'liq ko'ra oladi (privacy `disable` bo'lsa ham, ko'p paytda admin status kerak)
4. Test: `@pm_bot salom` yozing, PM javob berishi kerak

## 5. `.env.example` mazmuni

```env
# Telegram bot tokenlari
PM_BOT_TOKEN=
DEV_BOT_TOKEN=
QA_BOT_TOKEN=
DESIGNER_BOT_TOKEN=

# LLM provider kalitlari
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Har agent uchun model (default qiymatlar settings.py'da)
PM_MODEL=claude-sonnet-4-6
DEV_MODEL=claude-opus-4-7
QA_MODEL=claude-sonnet-4-6
DESIGNER_MODEL=gpt-4o

# SQLite yo'l
DB_PATH=./data/memory.sqlite

# Kontekst (so'nggi nechta xabar LLM'ga beriladi)
HISTORY_LIMIT=20

# Loglash
LOG_LEVEL=INFO
```

## 6. `requirements.txt`

```
aiogram>=3.4,<4
anthropic>=0.40
openai>=1.50
aiosqlite>=0.20
python-dotenv>=1.0
```

## Tez-tez uchraydigan muammolar

| Muammo | Yechim |
|---|---|
| Bot guruhda xabarlarni ko'rmayapti | Privacy mode `disable` qilinganmi? BotFather, `/mybots`, bot tanlang, Bot Settings, Group Privacy |
| `Unauthorized` xato | Token noto'g'ri yoki bot revoke qilingan, BotFather'da `/revoke` qilinganmi tekshiring |
| LLM `401` | API kalit noto'g'ri yoki kredit tugagan |
| `chat_id` topilmayapti | Botni guruhga qo'shgandan keyin guruhda biror xabar yozing, log'da `chat_id` ko'rinadi |
| Bot javob bermaydi, log'da xato yo'q | Mention `@username` to'g'ri yozilganmi? Privacy mode tekshiring |
| Ikkala bot bitta xabarga javob beradi | Normal: mention'larga qarab har biri o'ziga tegishli deb javob beradi |

## Xavfsizlik

- `.env` faylini hech qachon commit qilmang (`.gitignore`'da bor)
- API kalit yoki tokenni log'ga chiqarmang
- Bu MVP shaxsiy ishlatish uchun; ommaviy guruhga qo'yishdan oldin auth qoidasi qo'shing
