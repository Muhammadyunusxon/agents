# Agents

Each agent has two parts: `bots/<name>.py` (Python class) and `prompts/<name>.md` (system prompt).

## PM (Product Manager)

- **File:** [bots/pm.py](../bots/pm.py)
- **Prompt:** [prompts/pm.md](../prompts/pm.md)
- **Default model:** `gemini-2.5-flash`
- **Role:** Turns the user's idea into a clear spec; breaks work into tasks; assigns priorities; writes acceptance criteria
- **Output format:** Markdown spec; task list with priority tags (P0/P1/P2)
- **Handoff:** `@dev_bot` (to implement), `@designer_bot` (if UI/UX input is needed)

## Developer

- **File:** [bots/developer.py](../bots/developer.py)
- **Prompt:** [prompts/developer.md](../prompts/developer.md)
- **Default model:** `gemini-2.5-pro`
- **Role:** Writes code, refactors, answers technical questions, suggests architecture, picks libraries
- **Output format:** Code block (with language tag); short explanation; setup steps if needed
- **Handoff:** `@qa_bot` (when tests are needed), `@pm_bot` (when requirements are unclear), `@designer_bot` (when UI detail is missing)

## QA (Tester)

- **File:** [bots/qa.py](../bots/qa.py)
- **Prompt:** [prompts/qa.md](../prompts/qa.md)
- **Default model:** `gemini-2.5-flash`
- **Role:** Writes test plans, finds edge cases, drafts manual test scenarios, reports bugs
- **Output format:** Given/When/Then test cases; identified defects; severity tags
- **Handoff:** `@dev_bot` (when a bug is found), `@pm_bot` (when a requirement gap is found)

## Designer (UX/UI)

- **File:** [bots/designer.py](../bots/designer.py)
- **Prompt:** [prompts/designer.md](../prompts/designer.md)
- **Default model:** `gemini-2.5-flash`
- **Role:** UX copy, error messages, empty states, layout suggestions, color and typography advice, micro-interaction ideas
- **Output format:** Several variants (at least 2-3), each with a short rationale
- **Handoff:** `@dev_bot` (to implement), `@pm_bot` (when priority is needed)

## Prompt structure

Each `prompts/*.md` follows this layout (note: prompt bodies are in Uzbek so the bot replies in Uzbek; only the structure is shown here in English):

```markdown
# Rol: [name]

You are [role]. [1-2 sentences: who, what they do, for whom]

## Maqsad (Goal)
- [single-sentence goal 1]
- [single-sentence goal 2]

## Yondashuv (Approach)
- [principle 1, e.g. "ask for context first, then answer"]
- [principle 2]

## Chiqish formati (Output format)
- [clear structure: markdown headings, lists]
- [length limit, e.g. "no more than 300 words"]

## Estafetani uzatish (Handoff rules)
- If [condition] => mention `@other_bot` and ask a question
- If [condition] => answer yourself, do not mention anyone

## Stil (Style)
- Reply in Uzbek (if the user writes in another language, reply in that language)
- Concise, precise, no emojis
- Use language tags in code blocks (` ```python ` etc.)
```

## Model selection rationale

The defaults aim for "good enough on the free tier". Override per agent in `.env`.

| Agent | Default model | Why | Cheaper / faster | Stronger |
|---|---|---|---|---|
| PM | `gemini-2.5-flash` | Structured output, free, fast | `gemini-2.0-flash` | `gemini-2.5-pro`, `claude-sonnet-4-6` |
| Developer | `gemini-2.5-pro` | Best free-tier code quality | `gemini-2.5-flash` | `claude-opus-4-7` |
| QA | `gemini-2.5-flash` | Edge-case generation, free | `gemini-2.0-flash` | `claude-sonnet-4-6` |
| Designer | `gemini-2.5-flash` | UX copy variants, free | `gemini-2.0-flash` | `gpt-4o` |

The provider is chosen by model name prefix:

- `gemini-*` -> Google (free tier; needs `GOOGLE_API_KEY`)
- `claude-*` -> Anthropic (paid; needs `ANTHROPIC_API_KEY`)
- `gpt-*`, `o1-*`, `o3-*`, `o4-*` -> OpenAI (paid; needs `OPENAI_API_KEY`)

Free tier quotas on Gemini are tight for `gemini-2.5-pro` (~5 RPM, ~25/day). If the Developer agent hits rate limits during heavy testing, switch `DEV_MODEL=gemini-2.5-flash`.

## Adding a new agent

See [development.md](development.md) for the full procedure.
