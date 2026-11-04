# Stillspace

A **strategy-aware mental health support chatbot**, built as a **student research prototype**.

Before each reply, Stillspace checks the message for crisis words, asks a small AI classifier which **support strategy** fits (Validation, Reflection, Reassurance or Advice), reads the emotion, intensity and conversation stage, and then builds a detailed prompt for an open-source **Qwen** model. The strategy it used is shown on screen, so the reasoning is visible. Around the chat there are optional check-ins (a one-time setup, a daily mood, the PHQ-9 every two weeks) and a short reflection after each session.

> **Not therapy, diagnosis or an emergency service.** In an emergency call **112** or **Tele-MANAS 14416** (free, 24x7). Use it with **synthetic or role-played** conversations unless you have ethics approval, consent (and guardian consent for under-18s) and a named adult for follow-up. See `docs/SAFETY.md`.

---

## 10-minute quick start (mock mode, no AI key needed)

Windows PowerShell, with Python 3.10+ installed (first time? follow `docs/SETUP.md`, which explains every step):

```powershell
git clone https://github.com/harsh300604/stillspace.git
cd stillspace
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn backend.main:app --reload
```

Open **http://localhost:8000**, type a participant code such as `P001`, tick the box and click **Continue**. With no API key the app runs in **mock mode**: replies are built-in examples, but the safety layer, check-ins, strategy panel and summary all work. You'll see a small "Mock mode" tag.

(macOS/Linux: `source .venv/bin/activate` and `cp .env.example .env`.)

## Use a real AI model

Edit `.env`, then restart uvicorn (Ctrl+C, run it again):

| Option | `.env` | Notes |
|---|---|---|
| **OpenRouter** (hosted, paid credits) | `LLM_BASE_URL=https://openrouter.ai/api/v1`<br>`LLM_API_KEY=sk-or-...`<br>`LLM_MODEL=qwen/qwen3-14b` | No GPU needed. **Set a spending limit on the key.** |
| **Ollama** (free, runs on your computer) | `LLM_BASE_URL=http://localhost:11434/v1`<br>`LLM_API_KEY=ollama`<br>`LLM_MODEL=qwen3:4b-instruct-2507-q4_K_M` | Needs ~4 GB free RAM/VRAM. Use an **instruct** model (others "think" and are slow). |

Only `.env` changes; the code stays the same.

## What's in the folder

```
stillspace/
├── README.md            this file
├── flow.md              how the app flows: users, sign-in, journey, chat pipeline, safety
├── implementation.md    phased build plan, checks, decisions log, known issues
├── decisions.md         why things were built this way (for the mentor)
├── memory.md            build journal: problems hit and how they were fixed
├── handoff.md           start here if you are taking over the project
├── mentoring.md         16-session teaching plan (one hour each)
├── requirements.txt     Python packages
├── .env.example         all settings, copy to .env
├── frontend/            index.html, styles.css, app.js (the mockup's design)
├── backend/
│   ├── main.py          FastAPI app: serves the page and the API
│   ├── config.py        reads .env
│   ├── safety.py        crisis-word check, fixed crisis reply, PHQ item-9 rule
│   ├── classifier.py    AI call → strategy, emotion, intensity, stage, risk
│   ├── strategy_policy.py  requested vs classified → used strategy
│   ├── prompt_builder.py   builds the messages for the reply model
│   ├── llm.py           one function that talks to any OpenAI-compatible model
│   ├── mock.py          offline replies and keyword classifier
│   ├── checkins.py      PHQ-9 scoring and what's due
│   ├── db.py, db_connect.py  SQLite (local) or Postgres/Supabase (online)
│   ├── ratelimit.py     message and sign-in limits (online)
│   ├── routes/          the API endpoints
│   └── data/            strategy files, crisis words, prompts (.txt), schemas, consent text
├── eval/                30 classifier test messages, 30 safety test messages
├── scripts/             evaluation, export, codes, safety report, delete participant
├── docs/                SETUP, ARCHITECTURE, SAFETY, TROUBLESHOOTING, DEPLOYMENT, mockup
└── student_starter/     the same app with the five "brain" functions left as TODOs
```

## Documentation

| Read this | When |
|---|---|
| `docs/SETUP.md` | Installing everything on a new computer (beginner friendly, Windows first) |
| **`handoff.md`** | **Taking over the project (mentor): start here** |
| `flow.md` | Understanding who does what and what happens behind each click |
| `docs/ARCHITECTURE.md` | Understanding the code, the pipeline and the database |
| `docs/SAFETY.md` | Before any testing with people; what to do if a real disclosure happens |
| `docs/TROUBLESHOOTING.md` | Something doesn't work |
| `docs/DEPLOYMENT.md` | Putting it online (Supabase + Railway/Render) and the pre-launch checklist |
| `mentoring.md` | Teaching a student to build it in 16 one-hour sessions |

## Privacy in one paragraph

Data is stored in a local SQLite file (or your own Supabase project when deployed). Nothing is sent anywhere **except the chat text to the AI provider you configure** (none in mock mode; your own computer with Ollama), and that provider's data policy applies. PHQ-9 answers and dates of birth are never sent to the AI. The database, exports and `.env` are git-ignored. PHQ-9 and date of birth are health and personal data under India's DPDP Act 2023.

PHQ-9 developed by Drs. Robert L. Spitzer, Janet B. W. Williams, Kurt Kroenke and colleagues.
