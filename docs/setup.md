# Setup

## 1. Create four bots in BotFather

In [@BotFather](https://t.me/BotFather), for each agent:

1. `/newbot`, choose a username (e.g. `@myname_pm_bot`)
2. Copy the token; you will paste it into `.env` later
3. `/setprivacy`, select the bot, **Disable** (CRITICAL: without this, the bot will not see group messages)
4. (optional) `/setdescription`, `/setuserpic` for nicer presentation

Required bots for the full pipeline: PM, Developer, QA, Designer. Agents with empty tokens in `.env` are simply skipped, so you can start with one or two.

## 2. API keys

The router picks a provider from the model name prefix. Fill in only the keys you actually use.

### Default: Google Gemini (free tier, no credit card)

1. Sign in at https://aistudio.google.com/apikey
2. Click **Create API key**; pick or create a project
3. Copy the key (starts with `AIza...`)
4. Paste into `.env` as `GOOGLE_API_KEY=`

Free tier quotas (Google may change these):

| Model | Requests/min | Requests/day |
|---|---|---|
| `gemini-2.5-flash` | ~15 | ~1500 |
| `gemini-2.5-pro` | ~5 | ~25 |
| `gemini-2.0-flash` | ~15 | ~1500 |

For a personal MVP, flash quotas are plenty. The `gemini-2.5-pro` daily cap is the main thing to watch: if Developer hits it, fall back to `DEV_MODEL=gemini-2.5-flash`.

### Alternative: Anthropic Claude (paid, $5+ credit)

- Account: https://console.anthropic.com
- Billing: **Plans & Billing -> Add credits** (minimum $5)
- API key: **API Keys -> Create Key**; paste as `ANTHROPIC_API_KEY=`
- To use, set the model env, e.g. `DEV_MODEL=claude-opus-4-7`

### Alternative: OpenAI (paid)

- https://platform.openai.com/api-keys
- Paste as `OPENAI_API_KEY=`
- To use, set e.g. `DESIGNER_MODEL=gpt-4o`

## 3. Local run

```bash
cd /Users/muhammadyunusxon/StudioProjects/agents

python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# open .env and fill in tokens and at least one provider key

python run.py
```

When the console shows `started polling` for each configured agent, the system is ready.

## 4. Telegram group setup

1. Create a new group (or reuse an existing one)
2. **Add the bots:** Add member, type each bot username
3. Make each bot an **admin**: Manage group, Administrators, Add Administrator. Even with privacy disabled, admin status is often required for the bot to receive all group messages
4. Test: write `@pm_bot hello`; PM should reply

## 5. `.env.example` contents

```env
# Telegram bot tokens
PM_BOT_TOKEN=
DEV_BOT_TOKEN=
QA_BOT_TOKEN=
DESIGNER_BOT_TOKEN=

# LLM provider keys (fill in the ones matching the models below)
GOOGLE_API_KEY=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Per-agent model. Provider is chosen by name prefix.
PM_MODEL=gemini-2.5-flash
DEV_MODEL=gemini-2.5-pro
QA_MODEL=gemini-2.5-flash
DESIGNER_MODEL=gemini-2.5-flash

# Memory backend: sqlite (default) or postgres (e.g. Supabase)
DB_KIND=sqlite
DB_PATH=./data/memory.sqlite
DATABASE_URL=

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
google-genai>=0.8
aiosqlite>=0.20
asyncpg>=0.29
python-dotenv>=1.0
```

All three LLM SDKs are installed, but the router lazy-imports each one; only the providers you actually use are loaded at runtime.

## Optional: use Supabase Postgres instead of SQLite

Local SQLite is the default. Switch to Supabase when you want hosted storage, multi-device access, or are preparing for a web dashboard later.

### a. Create a Supabase project

1. Sign up at https://supabase.com
2. **New project**: name it, pick a region close to you, set a strong database password (save it; you will paste it into the connection string)
3. Wait ~2 minutes for the project to provision

### b. Get the connection string

1. In the project, go to **Project Settings -> Database**
2. Scroll to **Connection string**
3. Select the **Session pooler** tab (most compatible with home networks; IPv4-friendly)
4. Copy the URL; replace `[YOUR-PASSWORD]` with your database password
5. The format looks like:
   ```
   postgresql://postgres.PROJECTREF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres
   ```

Why Session pooler (5432) and not Transaction pooler (6543)? This MVP runs long-lived async processes that benefit from session-level features (prepared statements, etc.). Transaction pooler is meant for short, stateless serverless workloads.

### c. Configure `.env`

```env
DB_KIND=postgres
DATABASE_URL=postgresql://postgres.PROJECTREF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres
```

### d. Run

```bash
python run.py
```

On first run, the `messages` table is created automatically (`CREATE TABLE IF NOT EXISTS ...`). The console will log:

```
memory backend: postgres
```

### e. Verify

- Supabase Studio -> **Table Editor** -> `messages` should exist
- Supabase Studio -> **SQL Editor**:
  ```sql
  SELECT bot_name, substr(text, 1, 80) FROM messages ORDER BY id DESC LIMIT 20;
  ```

### Switching back

Set `DB_KIND=sqlite` in `.env` to use the local file again. The two stores do not sync automatically; each has its own history.

## Common issues

| Issue | Fix |
|---|---|
| Bot does not see group messages | Privacy mode must be `Disable`; BotFather, `/mybots`, select bot, Bot Settings, Group Privacy |
| `Unauthorized` error | Token is wrong or revoked; check with BotFather |
| LLM `401` / `403` | API key is wrong or the account is out of credits |
| Gemini `429` (rate limit) | Hit free-tier quota. Switch the affected agent's model to `gemini-2.5-flash` or `gemini-2.0-flash`, or wait until the daily reset |
| `chat_id` not found | After adding the bot to the group, send any message; the log will show `chat_id` |
| Bot does not reply, no error in log | Is `@username` typed correctly? Re-check privacy mode |
| Two bots reply to one message | Normal: each bot reads mentions independently and decides if the message is theirs |
| `memory init failed: DB_KIND=postgres requires DATABASE_URL` | Set `DATABASE_URL` in `.env`, or switch `DB_KIND=sqlite` |
| `asyncpg.exceptions.InvalidPasswordError` | Wrong password in `DATABASE_URL`; reset it in Supabase: Project Settings -> Database -> Reset database password |
| Postgres connection times out | Your network may block IPv6; make sure you copied the **Session pooler** URL, not the direct connection |

## Security

- Never commit `.env` (it is in `.gitignore`)
- Do not log API keys, tokens, or the full `DATABASE_URL`
- Supabase Postgres password should be unique; rotate via Project Settings -> Database -> Reset password
- This MVP is for personal use; before exposing it to a public group, add an auth rule
