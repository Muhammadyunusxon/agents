# Agentlar

Har agent ikki qismdan iborat: `bots/<name>.py` (Python sinf) va `prompts/<name>.md` (system prompt).

## PM (Product Manager)

- **Fayl:** [bots/pm.py](../bots/pm.py)
- **Prompt:** [prompts/pm.md](../prompts/pm.md)
- **Default model:** `claude-sonnet-4-6`
- **Roli:** Foydalanuvchi g'oyasini aniq spec'ga aylantirish, vazifalarni bo'lish, prioritet qo'yish, acceptance criteria yozish
- **Chiqish formati:** Markdown spec, ro'yxat shaklida vazifalar, prioritet teglari (P0/P1/P2)
- **Estafeta:** `@dev_bot` (amalga oshirish), `@designer_bot` (UI/UX fikrlash kerak bo'lsa)

## Developer

- **Fayl:** [bots/developer.py](../bots/developer.py)
- **Prompt:** [prompts/developer.md](../prompts/developer.md)
- **Default model:** `claude-opus-4-7`
- **Roli:** Kod yozish, refaktor, texnik savollarga javob, arxitektura takliflari, kutubxona tanlash
- **Chiqish formati:** Kod blok (til ko'rsatilgan), qisqa tushuntirish, agar kerak bo'lsa `setup` qadamlari
- **Estafeta:** `@qa_bot` (test kerak), `@pm_bot` (talab noaniq), `@designer_bot` (UI detal kerak)

## QA (Tester)

- **Fayl:** [bots/qa.py](../bots/qa.py)
- **Prompt:** [prompts/qa.md](../prompts/qa.md)
- **Default model:** `claude-sonnet-4-6`
- **Roli:** Test rejasi yozish, edge case topish, qo'lda test ssenariy, bug report formatlash
- **Chiqish formati:** Given/When/Then test case ro'yxati, aniqlangan kamchiliklar, severity teglari
- **Estafeta:** `@dev_bot` (bug topilsa), `@pm_bot` (talab gapida bo'shliq bor)

## Designer (UX/UI)

- **Fayl:** [bots/designer.py](../bots/designer.py)
- **Prompt:** [prompts/designer.md](../prompts/designer.md)
- **Default model:** `gpt-4o`
- **Roli:** UX copy, error xabarlari, empty state, layout takliflari, ranglar va tipografika maslahati, mikro-interaksiya g'oyalari
- **Chiqish formati:** Variant ro'yxati (kamida 2-3 ta), har birining sababini qisqacha izoh
- **Estafeta:** `@dev_bot` (amalga oshirish), `@pm_bot` (priority kerak)

## Prompt strukturasi

Har `prompts/*.md` quyidagi bloklardan iborat:

```markdown
# Rol: [nom]

Sen [rol]san. [1-2 jumla, kim, nima qiladi, kim uchun].

## Maqsad
- [bittali maqsad 1]
- [bittali maqsad 2]

## Yondashuv
- [printsip 1, masalan: "Avval kontekstni so'ra, keyin javob ber"]
- [printsip 2]

## Chiqish formati
- [aniq tuzilma, masalan: markdown sarlavhalar, ro'yxat]
- [uzunlik chegarasi, masalan: "300 so'zdan oshmasin"]

## Estafetani uzatish qoidalari
- Agar [shart] => `@other_bot` ni mention qil va savol ber
- Agar [shart] => o'zing javob ber, mention qilma

## Stil
- O'zbekcha javob ber (foydalanuvchi boshqa tilda yozsa, o'sha tilda)
- Qisqa, aniq, emoji ishlatma
- Kod blokda til belgisi (` ```python ` kabi)
```

## Model tanlash mantiqi

| Agent | Model | Nima uchun |
|---|---|---|
| PM | `claude-sonnet-4-6` | Struktura va ro'yxat, arzon, tez |
| Developer | `claude-opus-4-7` | Eng yaxshi kod sifati, murakkab refaktor |
| QA | `claude-sonnet-4-6` | Analiz, edge case topish, arzon |
| Designer | `gpt-4o` | UX copy va kreativ variantlar uchun yaxshi |

`.env` orqali har birini o'zgartirish mumkin: `DEV_MODEL=gpt-4o`. Model nomi prefiksi bo'yicha provider tanlanadi (`claude-*` -> Anthropic, `gpt-*`/`o1-*`/`o3-*` -> OpenAI).

## Yangi agent qo'shish

To'liq qadamlar uchun [development.md](development.md) ga qarang.
