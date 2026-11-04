# Stillspace: Project Memory

> **What this is:** a running journal of the build. After every phase it records what was built, how it was verified, what went wrong and how it was fixed, and the current state of the developer's setup.
> **Why:** so the developer (and later the mentor) can pick the project up again without re-reading the whole conversation, and so the problems we hit become teaching material.
> **Related files:** `implementation.md` (plan + checks + short decisions log) · `decisions.md` (the reasoning behind decisions, for the mentor).
> **Updated:** at the end of every phase.

---

## Current state (keep this section up to date)

| Item | Value |
|---|---|
| Last completed phase | **Phase 4** – LLM client, mock mode, basic chat |
| Next phase | Phase 5 – Safety layer |
| Branch | `claude/gracious-euler-tlrs89` (repo `harsh300604/stillspace`) |
| Project folder (dev laptop) | `D:\CreatED-cloud\stillspace` |
| Python | 3.11.9 (installed at `C:\Program Files\Python311`; venv and packages on D:) |
| GPU | NVIDIA GeForce RTX 4050 Laptop GPU, 6 GB (used by Ollama) · RAM 16 GB |
| Model (dev) | Ollama `qwen3:4b-instruct-2507-q4_K_M`, models in `D:\ollama\models` |
| Model (handoff default) | OpenRouter `qwen/qwen3-14b` |
| C: free space | 48.48 GB at the start; unchanged by the project |

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

---

## Lessons for the mentor (collected so far)

1. **Windows first.** Most problems were Windows/PowerShell problems, not code problems: `setx` needs a new window, quotes get stripped, `Activate.ps1` may need `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
2. **Check that the install really happened.** Run `pip list` after `pip install`.
3. **Slow internet:** `--timeout 120 --retries 10` for pip.
4. **Model availability changes.** Always check the provider's list before a session (Phase 4 check 0).
5. **"Thinking" models** can make a chatbot slow or leak reasoning text. Use instruct models.
6. **Background apps can hold ports or ignore settings** (the Ollama tray app). When something "is already in use", look for a running copy.
7. **Mock mode is the safety net for teaching.** Every session can run with no internet and no key.
