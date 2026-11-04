# Stillspace: handoff to the mentor

> **Who this is for:** the mentor who takes over this repository. You might run it, teach it with the 16-session plan, or deploy it online, either yourself or after a student rebuilds it on their own PC.
> **Status (4 Nov 2026):** all build phases are complete and tested (phases 0–11). This file is the starting point; every other document is linked from here.
> **Helplines (India):** Tele-MANAS **14416** / 1-800-891-4416 (free, 24×7) · Emergency **112**.

---

## 1. What Stillspace is (in one minute)

A web chat app where a person writes how they feel and gets a supportive reply from an open-source **Qwen** model. Before every reply the app:

1. runs a **keyword safety check**. A crisis message gets a fixed helpline reply and **no AI is called**.
2. **classifies** the message: which **support strategy** fits (Validation, Reflection, Reassurance, Advice), plus emotion, intensity, stage and risk.
3. applies a **policy**: safety, then the user's own request, then the classifier's choice.
4. builds a **detailed prompt**: strategy instruction, meta details, today's mood and PHQ-9 band (never raw answers or date of birth), plus recent history.
5. replies, shows **which strategy was used** (badge plus side panel), and stores everything.

Around the chat there are optional **check-ins**: a one-time setup, a daily mood, a PHQ-9 every two weeks, and a reflection after each chat.

**Why:** research on emotional-support conversations (ESConv; Kang et al., ACL 2024) shows language models over-use a few strategies. Choosing the strategy separately makes replies more varied, explainable and measurable. The repo includes the evaluation tools to test exactly that.

**What it is not:** therapy, diagnosis, an emergency service, or a finished product. It is a student research and learning prototype.

## 2. Read these in order

| # | File | Why | Time |
|---|---|---|---|
| 1 | this file | The map | 15 min |
| 2 | `README.md` | Quick start (mock mode, 10 min) and folder map | 10 min |
| 3 | `flow.md` | How users sign in and move through the app; what happens per message; FAQ | 20 min |
| 4 | `docs/SAFETY.md` | **Required before any testing with people**, including what to do if a real disclosure happens | 15 min |
| 5 | `docs/ARCHITECTURE.md` | Each file's job, the tables, the endpoints, how to switch settings | 20 min |
| 6 | `mentoring.md` | If you teach a student: the 16 one-hour sessions | 1 h |
| 7 | `docs/DEPLOYMENT.md` | If you deploy: Supabase, Railway/Render, the pre-launch checklist | 30 min |
| — | `decisions.md` | The reasoning behind design choices (readable narrative) | as needed |
| — | `implementation.md` | Phase-by-phase build record, numbered decisions (D-01…D-60) and known issues (K-01…K-12) | as needed |
| — | `memory.md` | Build journal: what went wrong and how it was fixed; lessons for the mentor | as needed |
| — | `docs/TROUBLESHOOTING.md` | Look up any error message | as needed |
| — | `Stillspace_Build_Specification.docx` | The original specification the build follows | as needed |

## 3. Get the code

The finished work is on the branch **`claude/gracious-euler-tlrs89`** (it may have been merged into `main` before you received this; check which branch has `handoff.md`).

```powershell
git clone https://github.com/harsh300604/stillspace.git
```
```powershell
cd stillspace
```
```powershell
git checkout claude/gracious-euler-tlrs89
```

**Secrets are not in the repo.** `.env`, the database file and exports are git-ignored. You create your **own** keys and database (sections 4 and 7). Nothing from the developer's accounts (OpenRouter key, Supabase project, participant codes) carries over, and none should be reused.

## 4. Run it locally

Full beginner steps are in `docs/SETUP.md`. Short version on Windows PowerShell, inside the project folder:

**First time only**
```powershell
python -m venv .venv
```
```powershell
.\.venv\Scripts\Activate.ps1
```
```powershell
pip install -r requirements.txt
```
```powershell
Copy-Item .env.example .env
```

**Every time**
```powershell
.\.venv\Scripts\Activate.ps1
```
```powershell
uvicorn backend.main:app --reload
```
Open **http://localhost:8000**. Sign in with any code (e.g. `P001`).

- An empty `LLM_API_KEY` in `.env` means **mock mode**: built-in replies, no internet or key needed. Everything else works, including safety.
- **Real model, hosted:** set `LLM_BASE_URL=https://openrouter.ai/api/v1`, `LLM_API_KEY=sk-or-…` (create the key **with a spending limit**), `LLM_MODEL=qwen/qwen3-14b`. Restart.
- **Real model, free and local:** install Ollama, `ollama pull qwen3:4b-instruct-2507-q4_K_M`, then set `LLM_BASE_URL=http://localhost:11434/v1`, `LLM_API_KEY=ollama`, `LLM_MODEL=qwen3:4b-instruct-2507-q4_K_M`. Use an **instruct** model: "thinking" models are slow and can return nothing.
- **Database:** with no `DATABASE_URL`, data goes to the local file `data\stillspace.db` (open it with DB Browser for SQLite). With `DATABASE_URL` set, data goes to Supabase Postgres.
- After changing `.env`, **restart** uvicorn. The start-up line shows the active setup: `env=… | mock_mode=… | db=…`.

## 5. Repository map

```
backend/            Python server (FastAPI)
  main.py           app, routes, serves the frontend, start-up checks
  config.py         reads .env; helplines; strategy loading
  safety.py         keyword crisis check (runs first), crisis reply, PHQ item-9 rule
  classifier.py     strategy + meta classifier (temperature 0, JSON, retry, fallback)
  strategy_policy.py  safety > request > classifier > default
  prompt_builder.py system prompt + strategy + meta + check-ins + history
  llm.py            one OpenAI-compatible call; removes "thinking" text
  mock.py           offline replies and keyword classifier
  checkins.py       PHQ-9 scoring and bands, what's due, prompt context
  db.py, db_connect.py  SQL helpers; SQLite or Postgres
  ratelimit.py      message and sign-in limits (online)
  auth.py           sign-in tokens: every request is tied to the signed-in participant
  routes/           config, participants, checkins, sessions, chat endpoints
  data/             strategy sets, crisis keywords, prompt .txt files, schemas, consent text
frontend/           index.html, styles.css, app.js (the mentor's mockup design, wired to the API)
scripts/            eval_classifier, eval_responses, export_data, create_codes, safety_report, delete_participant
eval/               test_messages.csv (30 labelled), safety_prompts.csv (30: 20 crisis, 10 normal)
student_starter/    the same app with the "brain" functions as TODOs, for the 16-session course
docs/               SETUP, ARCHITECTURE, SAFETY, TROUBLESHOOTING, DEPLOYMENT, mockup/
```

All prompt text lives in `backend/data/prompts/*.txt`, and strategies in `backend/data/strategies_*.json`. Both can be edited without touching Python.

## 6. The two ways forward

### Path A: teach a student, who then deploys their own build
1. Read `mentoring.md` Part A. Give the student **only** `student_starter/` as a zip (command in `mentoring.md`, "Giving the student the starter"), so the finished app (the answer key) isn't one folder away.
2. Run sessions 1–16. Each session lists mentor prep, the exact files and TODOs, hints, a "done when" command, and where the answer is in the finished app.
3. The student's finished starter is the same app, so it deploys **exactly like the reference app** (Path B, from step 1). The deploy files and scripts are already in the starter.

### Path B: deploy this reference app
Follow `docs/DEPLOYMENT.md`. In short:
1. **Supabase:** a new project in **South Asia (Mumbai)**. Copy the **Session pooler** connection string (add `?sslmode=require`). Tables and Row Level Security are created automatically on first start.
2. **OpenRouter:** a key with a spending limit.
3. **Railway or Render:** connect the repo; start command `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`; set the environment variables (table in `docs/DEPLOYMENT.md` §4). **`APP_ENV=production` and `FOLLOWUP_CONTACT` are required**: without a follow-up contact the app refuses to start.
4. **Participant codes:** from your laptop with the same `DATABASE_URL`, run `python scripts/create_codes.py --count 20`. Only these codes can sign in online. Hand them out privately.
5. **Complete the pre-launch checklist** (`docs/DEPLOYMENT.md` §5) **before sharing the link**.

**What production mode switches on:** only issued codes can sign in; age question (18+, or under-18 with guardian confirmation); the study's consent text; 40 messages per hour per participant and 700 per day for the app (the safety reply is never blocked); demo tools and `/docs` turned off.

### User isolation (in every mode)
The participant code is typed **once**. Sign-in returns a random **sign-in token**, and the browser sends it with every request (`Authorization: Bearer …`). `backend/auth.py` finds the participant **from the token**, so a request can only ever reach the signed-in person's own data. Session ids are checked against that participant too.
- Tokens expire after `SIGN_IN_HOURS` (default 12) and are deleted on *Switch participant* and when a participant is deleted.
- Only a SHA-256 hash of each token is stored (table `auth_tokens`, RLS on in Supabase).
- Codes never appear in web addresses or server logs (logs show the internal participant number).
- A crisis message is answered with the safety reply even if the sign-in has expired.
- Verified by a 30-check isolation test on SQLite and Postgres: participant B cannot read, change or chat into anything of A's (D-60).
- **Remaining limit:** the code itself is still the sign-in secret (no password, by spec design). Hand codes out privately. A PIN or password could be added later if the study needs it.

## 7. Before real participants: non-negotiable

| ☐ | Item |
|---|---|
| ☐ | **Ethics approval** from the supervising organisation |
| ☐ | **Approved consent wording** in `backend/data/consent.txt`. The current text has placeholders. Include where data is stored (e.g. Supabase Mumbai), the AI provider, retention and withdrawal |
| ☐ | **Guardian consent forms** collected *before* giving an under-18 a code (or set `AGE_POLICY=18plus_only`) |
| ☐ | **A named follow-up adult** in `FOLLOWUP_CONTACT`, who knows the procedure in `docs/SAFETY.md` §5 |
| ☐ | **A safety review routine:** there is **no automatic alert**. Someone runs `python scripts/safety_report.py --days 1` daily (or as agreed) and follows up |
| ☐ | **Privacy notice and DPDP Act 2023 check:** PHQ-9 answers and dates of birth are health and personal data |
| ☐ | **Retention plan:** when and how data is deleted (`delete_participant.py`, or delete the Supabase project) |
| ☐ | **Your own** OpenRouter key and Supabase project; nothing reused from development |

Running the study: `python scripts/safety_report.py --days 1` (flags: code, time, type, never message text) · `python scripts/export_data.py` (CSV backups; keep them private) · `python scripts/delete_participant.py <code>` (withdrawal).

## 8. Safety design (what you must not weaken)

- **The keyword check runs before any AI call** (`backend/safety.py`, `backend/data/crisis_keywords.json`). It covers English, Hinglish and Devanagari, plus spelling tricks (`k1ll`, `s.u.i.c.i.d.e`, `d i e`, `dieee`). A match means a fixed reply with helplines.
- **Classifier risk "high"** (or anything unclear) gives the same fixed reply. **PHQ-9 item 9 > 0** triggers a follow-up notice whatever the total score.
- The **"Safety" line in `choose_strategy`** must never be removed.
- **Test after every safety change:** the one-liner in `docs/SAFETY.md` §4 must print `30 rows, 0 mismatches`.
- **Known limits:** it can miss unusual wording, and it keeps known false positives on purpose ("suicide squad"). Never add an exception that could hide a real crisis.

## 9. Verified results

| What | Result |
|---|---|
| Safety test set | 30/30 correct (20 crisis caught, 10 figures of speech passed) |
| Classifier, `qwen3:4b-instruct` on Ollama | **27/30 = 90%**, all valid JSON, no single-strategy bias (10/8/5/7). Misses T18, T21, T23 (expected Reassurance), left un-tuned on purpose for teaching session 8 |
| Automated end-to-end suites (dev chat) | Pass on SQLite and on Postgres (journey, check-ins, chat, explainability, summary, production safeguards) |
| User isolation test (D-60) | 30/30 on SQLite, Postgres and the starter: one participant cannot read, change or chat into another's data |
| Supabase | Connected (Mumbai), RLS on all 4 tables, codes and safety report working |
| Student starter | Runs in mock mode with safe placeholders; with the finished functions swapped in, every "done when" check passes |
| Not yet run | The **blind A/B rating study** (`eval_responses.py`). It is designed and the tools work; the ratings are the student's work in sessions 13–14 |

## 10. Known issues and open items

| Id | Issue | What to do |
|---|---|---|
| K-03 | Keyword safety can miss indirect wording and flags some harmless text | By design; the classifier is a second net; review flags via the safety report |
| K-04 | No mental-health fine-tuned comparison model chosen | Optional; `eval_responses.py --models a,b` compares models when one is chosen |
| K-06 | A mood or style chosen on the consent page before sign-in isn't saved | Minor; choose after signing in |
| K-07 | A page refresh starts a new chat session (messages stay in the database) | Known limitation |
| K-09 | Rate limits are kept in memory (reset on restart; per process) | Fine for one small instance; use a shared store if you scale |
| K-11 | Beginner setup verified on Linux, not on a Windows laptop | Follow `docs/SETUP.md` once on Windows, or with the student in session 2 |
| K-12 | The code is still the only secret needed to sign in (no password, by spec design) | Hand codes out privately; a PIN could be added if the ethics board asks |

Full list with history: `implementation.md` → Known issues.

## 11. Changing things

| To… | Do |
|---|---|
| Change a reply's tone or rules | Edit `backend/data/prompts/system.txt` |
| Improve strategy choice | Edit descriptions in `backend/data/strategies_4.json` or `prompts/classifier.txt`, then run `python scripts/eval_classifier.py` |
| Use the 8 ESConv strategies | `STRATEGY_SET=strategies_esconv8` |
| Use another model | `LLM_MODEL=…` (and `CLASSIFIER_MODEL=…` for a separate classifier). Check the provider's model list first; models get removed |
| Leave check-ins out of the prompt | `INCLUDE_CHECKINS_IN_PROMPT=false` |
| Add a crisis phrase | Add it with an id to `crisis_keywords.json`, then run the safety test (must stay 30/0) |
| Look at the data | DB Browser for SQLite on `data\stillspace.db`, the Supabase Table Editor, or `python scripts/export_data.py` |

## 12. Stack and requirements

Python 3.10+ (built and tested on 3.11), FastAPI + uvicorn, pydantic, openai SDK (any OpenAI-compatible provider), python-dotenv, tzdata, psycopg (Postgres). Plain HTML/CSS/JavaScript with no build step. SQLite locally; Supabase Postgres online. Laptop minimum: 8 GB RAM, no GPU needed (a GPU only helps for Ollama).

---

*Built from `Stillspace_Build_Specification.docx` and the mockup `docs/mockup/Stillspace-2.html`. PHQ-9 developed by Drs. Robert L. Spitzer, Janet B. W. Williams, Kurt Kroenke and colleagues.*
