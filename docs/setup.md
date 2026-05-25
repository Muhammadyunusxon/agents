# Setup

## 1. Create four bots in BotFather

In [@BotFather](https://t.me/BotFather), for each agent:

1. `/newbot`, choose a username (e.g. `@myname_pm_bot`)
2. Copy the token; you will paste it into `.env` later
3. `/setprivacy`, select the bot, **Disable** (CRITICAL: without this, the bot will not see group messages)
4. (optional) `/setdescription`, `/setuserpic` for nicer presentation

Required bots: PM, Developer, QA, Designer.

## 2. API keys

- **Anthropic:** https://console.anthropic.com, API Keys, Create
- **OpenAI** (only if Designer or another role uses GPT): https://platform.openai.com/api-keys

## 3. Local run

```bash
cd /Users/muhammadyunusxon/StudioProjects/agents

python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# open .env and fill in tokens and keys

python run.py
```

When the console shows `started polling` for all four bots, the system is ready.

## 4. Telegram group setup

1. Create a new group (or reuse an existing one)
2. **Add all four bots:** Add member, type each bot username
3. Make each bot an **admin**: Manage group, Administrators, Add Administrator. Even with privacy disabled, admin status is often required for the bot to receive all group messages
4. Test: write `@pm_bot hello`; PM should reply

## 5. `.env.example` contents

```env
# Telegram bot tokens
PM_BOT_TOKEN=
DEV_BOT_TOKEN=
QA_BOT_TOKEN=
DESIGNER_BOT_TOKEN=

# LLM provider keys
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Per-agent model (defaults set in settings.py)
PM_MODEL=claude-sonnet-4-6
DEV_MODEL=claude-opus-4-7
QA_MODEL=claude-sonnet-4-6
DESIGNER_MODEL=gpt-4o

# SQLite path (relative to project root)
DB_PATH=./data/memory.sqlite

# How many recent messages go into the LLM context
HISTORY_LIMIT=20

# Logging level: DEBUG, INFO, WARNING, ERROR
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

## Common issues

| Issue | Fix |
|---|---|
| Bot does not see group messages | Privacy mode must be `Disable`; BotFather, `/mybots`, select bot, Bot Settings, Group Privacy |
| `Unauthorized` error | Token is wrong or revoked; check with BotFather |
| LLM `401` | API key is wrong or the account is out of credits |
| `chat_id` not found | After adding the bot to the group, send any message; the log will show `chat_id` |
| Bot does not reply and the log shows no error | Is `@username` typed correctly? Re-check privacy mode |
| Two bots reply to one message | Normal: each bot reads mentions independently and decides if the message is theirs |

## Security

- Never commit `.env` (it is in `.gitignore`)
- Do not log API keys or tokens
- This MVP is for personal use; before exposing it to a public group, add an auth rule
