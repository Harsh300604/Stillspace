# Stillspace: Project Memory

> **What this is:** a running journal of the build. After every phase it records what was built, how it was verified, what went wrong and how it was fixed, and the current state of the developer's setup.
> **Why:** so the developer (and later the mentor) can pick the project up again without re-reading the whole conversation, and so the problems we hit become teaching material.
> **Related files:** `implementation.md` (plan + checks + short decisions log) · `decisions.md` (the reasoning behind decisions, for the mentor).
> **Updated:** at the end of every phase.

---

## Current state (keep this section up to date)

| Item | Value |
|---|---|
| Last completed phase | **Phase 11** – Deployment readiness (Supabase + online safety) |
| Current phase | **Phase 10 – Part 1** (docs, flow.md, student_starter) built, waiting for checks; Part 2 = mentoring.md |
| Next phase | Phase 10 – handover docs, student starter, mentoring.md (last) |
| Build order from here | 8 → 9 → **11 (deployment: Supabase + online safety)** → 10 (docs, student starter, mentoring.md last) |
| Branch | `claude/gracious-euler-tlrs89` (repo `harsh300604/stillspace`) |
| Project folder (dev laptop) | `D:\CreatED-cloud\stillspace` |
| Python | 3.11.9 (installed at `C:\Program Files\Python311`; venv and packages on D:) |
| GPU | NVIDIA GeForce RTX 4050 Laptop GPU, 6 GB (used by Ollama) · RAM 16 GB |
| Model (dev) | Ollama `qwen3:4b-instruct-2507-q4_K_M`, models in `D:\ollama\models` |
| Model (handoff default) | OpenRouter `qwen/qwen3-14b` |
| C: free space | 48.48 GB at the start; unchanged by the project |
| Database (dev) | `DATABASE_URL` is set in the developer's `.env`: Supabase project in **Mumbai** (`aws-0-ap-south-1`, since 4 Nov 2026; the earlier Tokyo project is no longer used). Comment it out with `#` to use local SQLite (`data\stillspace.db`) |

### How to start working (developer laptop)

Open three PowerShell windows:

1. **Terminal C (model server):** `$env:OLLAMA_MODELS = "D:\ollama\models"; ollama serve`
   - If you get "Only one usage of each socket address": `Get-Process ollama* | Stop-Process -Force`, then run it again. The tray app uses C:, so keep it out of the way (Windows Settings → Apps → Startup → Ollama → Off).
2. **Terminal A (app):** `cd D:\CreatED-cloud\stillspace` → `.\.venv\Scripts\Activate.ps1` → `uvicorn backend.main:app --reload`
3. **Terminal B (commands):** same `cd` + activate, for `git pull`, the database one-liners and scripts.

Browser: http://localhost:8000 (Ctrl+F5 after a `git pull`).

### Developer `.env` (not in git)
```
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen3:4b-instruct-2507-q4_K_M
CLASSIFIER_MODEL=
MOCK_MODE=false
LLM_TIMEOUT_SECONDS=120
STRATEGY_SET=strategies_4
INCLUDE_CHECKINS_IN_PROMPT=true
HISTORY_TURNS=6
APP_TIMEZONE=Asia/Kolkata
DEMO_MODE=true
FOLLOWUP_CONTACT=
DB_PATH=data/stillspace.db
```
Mock mode: set `LLM_API_KEY=` (empty) and restart.

---

## Phase log

### Phase 0 – Plan (4 Nov 2026) ✅
- **Built:** `implementation.md` following spec section 14.
- **Found:** the mockup file was missing from the repo (attached later); spec typo in the venv activation command (D-01).

### Phase 1 – Skeleton and config (4 Nov 2026) ✅
- **Built:** `requirements.txt` (+ `tzdata`, D-04), `.env.example`, `.gitignore`, `backend/config.py`, `backend/main.py`, `GET /api/config`, both strategy files.
- **Verified by the developer:** pip cache on D:, venv on D:, C: unchanged, 4 strategies, 8 with esconv8.
- **Problems hit and fixes:**
  - `pip cache dir` still showed C: → `setx` only applies to **new** terminal windows.
  - `pip install` timed out on a slow connection (~39 kB/s) → `pip install --timeout 120 --retries 10 -r requirements.txt`.
  - The first `pip install` hadn't run at all (`pip list` showed only pip/setuptools) → always check `pip list`.
  - The developer chose `D:\CreatED-cloud\stillspace` instead of `D:\Projects\stillspace` (D-20).

### Phase 2 – Frontend port (4 Nov 2026) ✅
- **Built:** `frontend/index.html`, `styles.css` (mockup CSS unchanged + a small additions block), `app.js` (mockup JS made readable, changes marked `CHANGED:`).
- **Verified:** by the developer on Windows, plus a dev-chat headless browser run (45/47; the 2 "failures" were test-script mistakes; computed styles identical to the mockup).
- **Fix after testing:** the sidebar tag "Participant code · no password" wrapped onto two lines → shortened to "No password needed".
- **Input from the developer:** three suggestions (prompt-based classifier first; independent keyword safety; finalise models), recorded as D-21, D-22 and D-23.

### Phase 3 – Database, participants, check-ins (4 Nov 2026) ✅
- **Built:** `backend/db.py`, `backend/checkins.py`, `routes/participants.py`, `routes/checkins.py`, frontend sign-in, routing, saving, demo buttons, Switch participant.
- **Verified:** dev chat: 17 API cases + 33 browser checks; checks 1–8 on a fresh copy at the developer's request.
- **Problem hit and fix:** the database one-liner failed with `SyntaxError` in PowerShell (it strips `\"`) → one-liners now use only single quotes (D-31).

### Phase 4 – LLM client, mock mode, basic chat (4 Nov 2026) ✅
- **Built:** `backend/llm.py`, `backend/mock.py`, `routes/chat.py`, `prompts/plain_system.txt`, chat wiring with typing indicator, Retry and a "Mock mode" tag.
- **Verified:**
  - Developer, check 2 (real model, Ollama `qwen3:4b-instruct-2507-q4_K_M`): coherent short replies, no `<think>` text, "AI reply" badge, and the third reply remembered "the meeting was the cause".
  - Dev chat: checks 1, 3, 4 and 5 (mock mode, wrong key → friendly error + Retry with 0 rows stored, messages table, new session), using a fake OpenAI-compatible server for the real-model path.
- **Problems hit and fixes (most of this phase's time):**
  1. `qwen/qwen3-8b` is **gone from OpenRouter** → handoff default `qwen/qwen3-14b`; the developer uses free Ollama (D-37, D-38).
  2. The existing Ollama (0.40.14) **saved models to C:** even with `OLLAMA_MODELS` set: the tray app started before `setx`, and the app may also have its own model-location setting → removed the C: copies (`gemma:2b`, `qwen3:4b`) and started the server by hand with `OLLAMA_MODELS` set. The log shows `OLLAMA_MODELS:D:\\ollama\\models`.
  3. "Only one usage of each socket address" → another Ollama was still running: `Get-Process ollama* | Stop-Process -Force`.
  4. `qwen3:4b` **always thinks** (ignores `--think=false`, `/no_think` and `reasoning_effort`) → switched to `qwen3:4b-instruct-2507-q4_K_M`; `llm.py` now sends `think:false` to Ollama and strips a lone `</think>` (D-39).
  5. Local models can be slow to start → `LLM_TIMEOUT_SECONDS` (D-36).
- **Observation:** replies are a bit generic, which is expected with the plain prompt. Strategy instructions arrive in Phase 7.

### Phase 5 – Safety layer (4 Nov 2026) ✅
- **Built:** `backend/safety.py` (normalise → match → fixed reply), `crisis_keywords.json` (36 phrases + 13 patterns, each with an id), `prompts/crisis_response.txt`, `eval/safety_prompts.csv` (30 rows), the pipeline's step 1 in `routes/chat.py`, the "Safety response" styling, helplines in the PHQ item-9 notice, and the risk indicator after a safety reply.
- **Design choice from the developer's Phase 2 suggestion:** safety never depends on the AI model. The keyword check runs first; on a match the AI is never called.
- **Verified by the dev chat:** 30/30 rows (direct + browser, mock mode), crisis replies with a wrong key and with a model server (0 model calls for crisis messages), the follow-up contact shown, 25/25 extra unseen crisis phrasings caught, and Phase 3/4 regressions still green.
- **Problems hit and fixes:**
  - Swapping `!` → `i` (look-alike) would have turned "die!" into "diei" and **missed** a crisis → `!` is never swapped. A good example of a fix that looks harmless but could weaken safety.
  - Python's `\b` word boundary does not work inside Devanagari words (vowel signs) → Devanagari phrases match as plain text.
  - My test script choked on the CSV's Windows line endings (needed for Excel) → parse CSVs with a real CSV reader.
- **Known false positive (kept on purpose):** "I love the movie suicide squad".
- **Checks 1–7:** all passed in the dev chat's run on a fresh copy, at the developer's request (model server standing in for Ollama).

### Phase 6 – Strategy classifier (4 Nov 2026) ✅
- **Built:** `backend/classifier.py`, `prompts/classifier.txt`, `mock_classify()` in `mock.py`, `eval/test_messages.csv` (30 rows, balanced), `scripts/eval_classifier.py`.
- **Design choice from the developer's Phase 2 suggestion:** prompt-based classification with Qwen first; a trained DistilBERT/DeBERTa classifier stays a stretch idea (D-21).
- **Verified by the dev chat:** 13 parser edge cases; evaluation in mock mode, against a fake model (retry and fallback paths) and with the ESConv-8 warning. Not yet verified: the real model's accuracy (developer, check 1).
- **Small fix:** the mock advice rule missed "tips" and "how should I" → more phrases added (mock score 80% → 93%; not a meaningful number, because the same person wrote the rules and the test set).
- **Accuracy with the real model (developer, check 1):** `qwen3:4b-instruct-2507-q4_K_M` → **27/30 = 90%**, 30/30 valid JSON, no preference bias (10/8/5/7). Misses: T18, T21, T23 (all expected Reassurance; the model chose Validation/Reflection). ~3.4 s per classification on the RTX 4050.
- **Not tuned on purpose (D-42):** the misses are kept for the student's Session 8 exercise. Confidence is always 0.95+, even when wrong.
- **`qwen3:8b` comparison (developer, stopped after 5 messages):** all fallbacks ("JSON not closed"), 35–51 s per message. It's a hybrid model that thinks by default, the `/no_think` switch never reached the classifier's single user message, and 8B doesn't fit fully in 6 GB of VRAM → **stay on `qwen3:4b-instruct` for everything**. Code fixed so `/no_think` also reaches single-message prompts (D-43). Remember `Remove-Item Env:CLASSIFIER_MODEL` after a one-off test.
- **Heads-up for Phase 7:** two model calls per message (classifier + reply) → expect roughly 6–9 s per reply with Ollama.

### Phase 7 – Prompt builder and strategy-aware replies (4 Nov 2026) ✅
- **Built:** `strategy_policy.py`, `prompt_builder.py`, `prompts/system.txt`, the full 7-step pipeline in `routes/chat.py`, `checkins.checkin_context()`, the explainability panel and strategy badges.
- **Verified by the dev chat:** policy 8/8, prompt builder 9/9 (privacy rule: no date of birth or raw PHQ answers, confirmed in every request the model server received), browser checks 1/2/3/5 in mock mode and against a fake model, classifier `risk: high` → Safety response; Phase 3/5 regressions green.
- **Found and fixed while testing:**
  - "I just want to sleep and never wake up" was **not** caught by the keywords → new rule `en-sleep-never-wake` (the safety set still gives 30/0).
  - The fallback reply showed a strategy badge ("Validation") although no strategy shaped it → it shows "Fallback reply" again.
  - My own quick one-liner said "20 mismatches" because Python read `x is not None != y` as a chained comparison. Always use the documented check command.
- **Expect** ~6–9 s per reply with Ollama now (two model calls); mock mode stays instant.
- **Developer's first run:** checks 1 and 2 good. In check 5 the **Reflection reply was identical to the Validation reply**: the same message was sent 4× in one conversation, so the model copied its own earlier reply from the history. Fix: a new session before each strategy (D-45). Lesson: when comparing strategies, use independent conversations (this matters for Phase 9 too).
- **Checks 1–7 (dev-chat run on a fresh copy, at the developer's request):** all passed, including the privacy scan of the printed prompt and of every request to the model, and fresh sessions sending no earlier history.

### Phase 8 – Reflection, summary, export (4 Nov 2026) ✅
- **Built:** `routes/sessions.py` (start/end/summary), reflection saved as a `post_session` check-in, a server-built summary page (time, messages, latest PHQ-9, strategy bars, reflection), `scripts/export_data.py` (4 CSVs for Excel).
- **Verified by the dev chat:** API cases + browser checks 1 and 2 + export (4 CSVs with BOM); Phase 3/7 regressions green.
- **Note:** `db.py` is 214 lines; it gets restructured in Phase 11 (Postgres).
- **Checks 1–4:** all passed in the dev chat's run on a fresh copy (mock mode), at the developer's request.

### Phase 9 – Evaluation kit (4 Nov 2026) ✅
- **Built:** `scripts/eval_responses.py`: A (plain prompt) vs B (full pipeline) per message and model, with no history or check-ins in either. Writes the full `responses_*.csv` plus a **shuffled blind rating sheet**; `--summarise` merges ratings back; the `ollama:` prefix for local models.
- **Decision:** the developer left the design open ("what holds up best"), so it's built for a fair, blind comparison (D-53). A second model can be added any time with `--models`.
- **Verified by the dev chat:** 10/20-row runs, A/B metadata, blind sheet, model switching, mock mode, crisis rows, the summarise round trip with an Excel-encoded file.
- **Checks 1–4:** all passed in the dev chat's run on a fresh copy, at the developer's request (model server on `localhost:11434` standing in for Ollama).

### Phase 11 – Deployment readiness: Supabase + online safety (4 Nov 2026) ✅
- **Built:** `db_connect.py` (SQLite or Postgres), schema files (Postgres with RLS), researcher-issued codes, age and guardian consent, session ownership checks, rate limits (40 per hour, 700 per day; never blocking safety), production lock-down, `create_codes.py`, `safety_report.py`, `delete_participant.py`, Postgres export, `docs/DEPLOYMENT.md` (Railway and Render, pre-launch checklist).
- **Found while building:** session ids are guessable numbers → every session/chat request now carries the code and the server checks ownership (D-55). Railway/Render put a proxy in front of the app → the sign-in limit reads `X-Forwarded-For`, otherwise all visitors would share one limit.
- **Verified by the dev chat:** 4 rounds: SQLite regression, the same suites on a real Postgres 16 server, all production safeguards, upgrading an old SQLite file and the online consent page in a browser. Not testable from the dev chat: the developer's own Supabase project and a real Railway/Render deploy.
- **Test-environment hiccup:** the throwaway Postgres server crashed when the sandbox reset folder permissions → moved it to Postgres's own home directory. Not an app issue.
- **Bug caught in the second test run (D-56):** `P001` could sign in online because local testing had already put it into the same Postgres/Supabase database. Fix: an `issued` flag; production accepts only codes made by `create_codes.py`. Codes made before the fix must be re-created.
- **Developer's run:** connected to their real Supabase project (`aws-0-ap-northeast-1` = **Tokyo**), all 4 tables with RLS on, 3 issued codes created. Advice: keep Tokyo as the test project; create the study project in Mumbai (`ap-south-1`) (K-10). **Later the same day:** the developer switched `DATABASE_URL` to a new Mumbai project; start-up created the tables, `create_codes.py --count 3` and `safety_report.py` ran against `aws-0-ap-south-1`. K-10 resolved. Those 3 codes were also pasted in chat, so they count as test codes.
- **Heads-up:** the developer's `.env` already has `DATABASE_URL`, so after `git pull` + `pip install -r requirements.txt` the local app writes to Supabase.

### Phase 10 – Part 1: handover docs + student starter (4 Nov 2026) 🔨 built, waiting for checks
- **Built:** `README.md`, **`flow.md`** (requested: users, sign-up/sign-in, journey, chat pipeline, safety, researcher side, data, FAQ), `docs/SETUP.md`, `docs/ARCHITECTURE.md`, `docs/SAFETY.md` (incl. what to do after a real disclosure), `docs/TROUBLESHOOTING.md` (every issue from this build), `student_starter/` (TODO stubs per session, safe placeholders, working safety).
- **Developer's question answered:** no accounts or passwords. Locally a new code = sign-up; online only researcher-issued codes work (no self sign-up).
- **Verified by the dev chat:** the starter runs in mock mode and with a model (safe placeholders, `[TODO Session N]` prints), safety 30/0 inside the starter, and swapping in the finished Session 4 + 7 functions gives `source=llm` and working memory.
- **Next:** the developer checks Part 1 (SETUP from a fresh folder, starter on port 8001, README timing) → then `mentoring.md` (Part 2).

### Plan change after Phase 7 (4 Nov 2026)
- The developer wants to deploy the app later so the student can share it. **Decision:** Supabase Postgres + online safety, as a new **Phase 11**, built after Phase 9 and before Phase 10 (D-46 to D-50).
- **Kept:** SQLite stays the default for local use and the student course.
- **Flagged:** do not share the current app online. Guessable codes would expose other participants' answers (K-08).
- **Developer's choices:** hosting on Railway or Render; ages 18+ and under-18 with guardian consent; limits of 40 per hour per participant and 700 per day; **no alert channel** (safety report script + review routine instead). Supabase needs only `DATABASE_URL` (Session pooler URI), and only when Phase 11 starts.

---

## Lessons for the mentor (collected so far)

1. **Windows first.** Most problems were Windows/PowerShell problems, not code problems: `setx` needs a new window, quotes get stripped, `Activate.ps1` may need `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
2. **Check that the install really happened.** Run `pip list` after `pip install`.
3. **Slow internet:** `--timeout 120 --retries 10` for pip.
4. **Model availability changes.** Always check the provider's list before a session (Phase 4 check 0).
5. **"Thinking" models** can make a chatbot slow or leak reasoning text. Use instruct models.
6. **Background apps can hold ports or ignore settings** (the Ollama tray app). When something "is already in use", look for a running copy.
7. **Mock mode is the safety net for teaching.** Every session can run with no internet and no key.
8. **Safety changes need a test set.** Every change to `crisis_keywords.json` or `safety.py` should be followed by the 30-row check (`30 rows, 0 mismatches`). Never add an exception for a false positive if it could hide a real crisis.
9. **A score is only as honest as its test set.** The mock classifier scores 93% because the same person wrote the rules and the test messages. Ask the student who wrote the labels, and whether the model has seen similar examples.
10. **Bigger isn't automatically better.** On a 6 GB GPU, `qwen3:8b` was 10× slower than the 4B instruct model and, while thinking was still on, produced no usable answers. Measure before switching models.
11. **Test design can fake a bug.** Sending the same message repeatedly in one chat made the model copy itself, which looked like "strategies don't work". Compare conditions in separate, fresh conversations.
