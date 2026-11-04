# Stillspace – Implementation Plan

> Source of truth: `Stillspace_Build_Specification.docx` (v1.1, 4 Nov 2026).
> This file follows section 14 of the spec. The dev chat writes code; **the developer runs every check**.
> The dev chat stops after Phase 0 (this file) and after every phase.

---

## 1. Overview

Stillspace is a local web chat app (research prototype, not therapy). For each user message the backend:

1. runs a **keyword safety check** (no LLM; crisis → fixed reply with Tele-MANAS 14416 / 112),
2. asks an LLM **classifier** for `{strategy, emotion, intensity, stage, risk, confidence, rationale}`,
3. runs a **second safety check** (`risk == "high"` → fixed reply),
4. picks the **used strategy** (safety wins, then the user's request, then the classifier),
5. **builds a prompt** (system text + strategy instruction + meta details + check-in context + history),
6. calls a **Qwen** model through an OpenAI-compatible API (or **mock mode** with no key),
7. **logs** everything to SQLite.

Around the chat there are check-ins (setup, daily mood, PHQ-9 every 14 days, post-session reflection), a session summary, CSV export and evaluation scripts. The frontend is the mentor's mockup `Stillspace-2.html`, split into 3 files and wired to the API. Only the changes listed in spec section 12 are made to it.

**Stack (spec section 6):** Python 3.10+, FastAPI + uvicorn, pydantic v2, `openai` SDK, python-dotenv, `sqlite3`, plain HTML/CSS/JS. No ORM, no npm, no extra frameworks.

**Storage (spec section 6.1):** everything lives on **D:**: the project (`D:\CreatED-cloud\stillspace`), `.venv`, pip cache, temp files, HF/Ollama caches, the DB and exports. The code only uses paths relative to the project root (`pathlib`), never hard-coded drive letters.

### Companion files (updated after every phase)

- **`memory.md`**: project journal: the current state of the dev setup, what each phase built, how it was verified, problems hit and their fixes, lessons for the mentor.
- **`decisions.md`**: the reasoning behind decisions, written for the mentor: grouped by topic, with alternatives and teaching notes. It uses the same D-IDs as the Decisions log below (this file keeps the short log the spec requires).

### How to use the checklists

- Commands are **PowerShell**, run from `D:\CreatED-cloud\stillspace` with the venv active (prompt starts with `(.venv)`), unless a step says otherwise.
- "Terminal A" runs the server (`uvicorn backend.main:app --reload`) and stays open. "Terminal B" is a second PowerShell window (activate the venv there too) for other commands.
- To inspect the database without DB Browser, a `python -c "..."` one-liner is given where useful.
- Report back with the check numbers and pass/fail, plus any error text.

---

## 2. Phase table

| Phase | Goal | Main files created / changed | Status |
|---|---|---|---|
| 0 | Write this plan | `implementation.md` (+ `memory.md`, `decisions.md` from Phase 4 on) | ✅ Approved |
| 1 | Skeleton and config, D: drive setup | folders, `requirements.txt`, `.env.example`, `.gitignore`, `backend/config.py`, `backend/main.py`, `backend/routes/config_route.py`, `backend/data/strategies_4.json`, `backend/data/strategies_esconv8.json`, placeholder `frontend/index.html`, `docs/mockup/Stillspace-2.html` | ✅ Done – checks 1–5 passed |
| 2 | Frontend port | `frontend/index.html`, `frontend/styles.css`, `frontend/app.js` | ✅ Done – checks passed |
| 3 | Database, participants, check-ins | `backend/db.py`, `backend/checkins.py`, `backend/routes/participants.py`, `backend/routes/checkins.py`, demo endpoint, `backend/main.py`, `frontend/app.js`, `frontend/index.html` | ✅ Done – checks passed |
| 4 | LLM client, mock mode, basic chat | `backend/llm.py`, `backend/mock.py`, `backend/routes/chat.py`, `backend/db.py`, `backend/main.py`, `backend/data/prompts/plain_system.txt`, `frontend/app.js`, `frontend/index.html`, `frontend/styles.css` | ✅ Done – checks passed |
| 5 | Safety layer | `backend/safety.py`, `backend/data/crisis_keywords.json`, `backend/data/prompts/crisis_response.txt`, `eval/safety_prompts.csv`, `backend/routes/chat.py`, `backend/checkins.py`, `frontend/app.js`, `frontend/styles.css`, `frontend/index.html` | ✅ Done – checks passed |
| 6 | Strategy classifier | `backend/classifier.py`, `backend/data/prompts/classifier.txt`, `backend/mock.py`, `eval/test_messages.csv`, `scripts/eval_classifier.py` | ✅ Done – checks passed (90%) |
| 7 | Prompt builder and strategy-aware replies | `backend/strategy_policy.py`, `backend/prompt_builder.py`, `backend/data/prompts/system.txt`, `backend/routes/chat.py`, `backend/checkins.py`, `backend/db.py`, `backend/data/crisis_keywords.json`, `frontend/app.js` | ✅ Done – checks passed |
| 8 | Reflection, summary, export | `backend/routes/sessions.py` (new), `backend/routes/chat.py`, `backend/db.py`, `backend/main.py`, `frontend/app.js`, `scripts/export_data.py` | ✅ Done – checks passed |
| 9 | Evaluation kit | `scripts/eval_responses.py` | ✅ Done – checks passed |
| 10 | Handover docs, student starter, mentoring.md | `README.md`, `flow.md` (new, your request), `docs/SETUP.md`, `docs/ARCHITECTURE.md`, `docs/SAFETY.md`, `docs/TROUBLESHOOTING.md`, `student_starter/`, `mentoring.md` (last) | ✅ Done – `mentoring.md` written; checks run in the dev chat (you asked not to do them) |
| 11 | Deployment readiness (Supabase + online safety) – **built after Phase 9, before Phase 10** | `backend/db_connect.py` (new), `backend/db.py`, `backend/data/schema_sqlite.sql`, `backend/data/schema_postgres.sql`, `backend/data/consent.txt`, `backend/config.py`, `backend/ratelimit.py`, `backend/main.py`, `backend/checkins.py`, `backend/routes/*`, `frontend/app.js`, `scripts/create_codes.py`, `scripts/safety_report.py`, `scripts/delete_participant.py`, `scripts/export_data.py`, `requirements.txt`, `.env.example`, `docs/DEPLOYMENT.md` | ✅ Done – checks passed |

Status key: ⬜ not started · 🔨 built, waiting for your checks · ✅ checks passed

**Merged into `main` (4 Nov 2026, PR #1).** The `git pull origin claude/gracious-euler-tlrs89` lines in the phase checks below are history; use `git pull origin main` from now on.

**After Phase 10 (4 Nov 2026):** user isolation with server-issued sign-in tokens (D-60). New `backend/auth.py` and `auth_tokens` table; endpoints `/api/me/status`, `PATCH /api/me`, `/api/logout`; the code is sent only at sign-in. Applied to `student_starter/` and all docs. ✅ Tested (30-check isolation test on SQLite, Postgres and the starter).

**Build order (D-46):** 8 → 9 → **11** → 10. Phase 11 (deployment) was added after the spec. It is built before Phase 10 so that the handover docs, `student_starter/` and `mentoring.md` (still written last, as the spec requires) describe the final code, including deployment.

---

## 3. Phases in detail

### Phase 1: Skeleton and config

**Status:** ✅ Done. All 5 checks passed on the dev laptop (4 Nov 2026): pip cache on `D:\cache\pip`, venv at `D:\CreatED-cloud\stillspace\.venv`, C: free space unchanged at 48.48 GB, `/api/config` shows 4 strategies and `mock_mode: true`, and switching to esconv8 shows 8.

**Setup notes from the test run:**
- `setx` only applies to terminals opened afterwards. `pip cache dir` showed C: until a brand-new PowerShell window was opened.
- On a slow connection, `pip install` timed out. This fixed it: `pip install --timeout 120 --retries 10 -r requirements.txt`. These notes go into docs/TROUBLESHOOTING.md in Phase 10.
- Python 3.11.9 is already installed at `C:\Program Files\Python311`, which is acceptable: only the venv and packages need to be on D:.

**Goal:** a runnable FastAPI app on D: that serves a placeholder page and `GET /api/config`, with every setting read from `.env`.

**Deviations / notes:**
- `requirements.txt` uses version ranges pinned to each package's current major version: fastapi `>=0.115,<1.0`, uvicorn `>=0.30,<1.0`, pydantic `>=2.7,<3.0`, openai `>=3.0,<4.0` (the current openai SDK major is 3), python-dotenv `>=1.0,<2.0`, plus the approved `tzdata` (D-04).
- The mockup was copied to `docs/mockup/Stillspace-2.html` in this phase (resolves K-01).
- On startup the server prints one `[startup] ...` line showing the strategy set, mock mode, demo mode and DB path, so a wrong `.env` is easy to spot.
- The dev chat only checked that the JSON files parse and the Python files compile. Nothing was run.

**Files:**
- `requirements.txt`: fastapi, uvicorn[standard], pydantic, openai, python-dotenv (pinned to their current major versions; see Decisions log D-04 about `tzdata`)
- `.env.example`: every key from spec section 8 with its default and a one-line comment
- `.gitignore`: `.env`, `.venv/`, `data/*.db`, `exports/`, `__pycache__/`
- `backend/__init__.py`, `backend/routes/__init__.py`: empty, so `uvicorn backend.main:app` imports cleanly
- `backend/config.py`: loads `.env`, exposes plain module-level settings, `is_mock_mode()`, `load_strategies()`, `HELPLINES`, `APP_VERSION`
- `backend/main.py`: creates the app, includes routes, serves `frontend/index.html` at `/` and `frontend/` at `/static`
- `backend/routes/config_route.py`: `GET /api/config`
- `backend/data/strategies_4.json` (spec section 11.1) and `backend/data/strategies_esconv8.json` (8 ESConv strategies)
- `frontend/index.html`: temporary placeholder page (replaced in Phase 2)
- Empty folders kept with `.gitkeep`: `data/`, `eval/`, `scripts/`, `docs/`, `backend/data/prompts/`

**`GET /api/config` response shape:**
```json
{
  "app_version": "0.1.0",
  "strategy_set": "strategies_4",
  "strategies": [{"name": "Validation", "description": "..."}, "..."],
  "helplines": [{"name": "Tele-MANAS", "number": "14416", "alt": "1-800-891-4416", "note": "free, 24x7"},
                {"name": "Emergency", "number": "112"}],
  "mock_mode": true,
  "demo_mode": true,
  "followup_contact": ""
}
```
The API key is **never** included.

**Manual checks:**

1. **D: drive setup (spec 6.1).** In PowerShell (any folder):
   ```powershell
   Get-PSDrive C        # write down the "Free" value
   mkdir D:\cache\pip, D:\cache\tmp, D:\cache\hf, D:\ollama\models
   setx PIP_CACHE_DIR D:\cache\pip
   setx HF_HOME D:\cache\hf
   setx OLLAMA_MODELS D:\ollama\models
   ```
   ("already exists" errors from `mkdir` are fine.) **Close the terminal and open a NEW one**, then:
   ```powershell
   pip cache dir
   echo $env:PIP_CACHE_DIR
   ```
   **Expect:** both print `D:\cache\pip`.

2. **Project, venv and install on D:.**
   ```powershell
   git clone https://github.com/harsh300604/stillspace.git D:\CreatED-cloud\stillspace
   cd D:\CreatED-cloud\stillspace
   git checkout claude/gracious-euler-tlrs89
   $env:TMP="D:\cache\tmp"; $env:TEMP="D:\cache\tmp"
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -c "import sys; print(sys.prefix)"
   pip install -r requirements.txt
   Get-PSDrive C
   ```
   (If you already cloned, skip the clone and run `git pull origin claude/gracious-euler-tlrs89`. If `Activate.ps1` is blocked, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and retry.)
   **Expect:** the prompt shows `(.venv)`. `sys.prefix` prints `D:\CreatED-cloud\stillspace\.venv`. pip ends with `Successfully installed ...` and no red errors. C: free space is about the same as in check 1 (a few MB difference is normal).

3. **Run the server.** In Terminal A (venv active, in `D:\CreatED-cloud\stillspace`):
   ```powershell
   Copy-Item .env.example .env
   uvicorn backend.main:app --reload
   ```
   **Expect:** `[startup] Stillspace 0.1.0 | strategies=strategies_4 | mock_mode=True | demo_mode=True | db=D:\CreatED-cloud\stillspace\data\stillspace.db`, then `Uvicorn running on http://127.0.0.1:8000` and `Application startup complete.` No tracebacks. Opening http://localhost:8000 shows the placeholder page "Stillspace backend is running".

4. **Config endpoint.** Open http://localhost:8000/api/config in the browser (or in Terminal B: `Invoke-RestMethod http://localhost:8000/api/config | ConvertTo-Json -Depth 5`).
   **Expect:** JSON with `"strategy_set": "strategies_4"`, a `strategies` list of exactly **4** (Validation, Reflection, Reassurance, Advice), each with a `description`, `"mock_mode": true`, `"demo_mode": true`, and helplines with 14416 and 112. No `api_key` field anywhere.

5. **Switch strategy set.** In `.env` set `STRATEGY_SET=strategies_esconv8`, save, then stop the server (Ctrl+C) and start it again. Reload `/api/config`.
   **Expect:** **8** strategies (Question, Restatement or Paraphrasing, Reflection of Feelings, Self-Disclosure, Affirmation and Reassurance, Providing Suggestions, Information, Others). Set it back to `strategies_4` and restart: 4 again.

---

### Phase 2: Frontend port

**Goal:** the mockup served by FastAPI, looking identical, with only the section 12 changes that don't need a database yet.

**Status:** ✅ Done. You passed checks 1–6 on Windows (4 Nov 2026).

**What was done / deviations:**
- `styles.css` is the mockup CSS **byte for byte**, plus a small block at the end marked "Stillspace additions": the footer disclaimer style, a desktop chat height 35 px shorter to make room for it, and a red hint colour for an invalid participant code.
- `index.html` is the mockup markup, laid out on separate lines for readability. `#view` is now a `<div>` inside `.center`, so the footer disclaimer (spec 16) sits under every step. The About dialog has a single accurate text (the mockup overwrote the dialog from JS; that overwrite was removed).
- `app.js` is the mockup JS, reformatted onto readable lines with every change marked `CHANGED:`. Not-yet-connected parts are marked `STUB (Phase N)`. New: the `api(path, options)` helper (JSON, friendly errors, `aria-busy` loading state), a `notify()` toast, start-up that loads `/api/config` first (with a friendly "could not start" box and Try again if the server is down), and participant-code validation stored in `sessionStorage` (wrapped in try/catch).
- Strategy lists (side panel, mobile panel, setup select, setup hint line, summary bars) are built from `/api/config`. Each option shows the strategy's description as a tooltip (spec 11.1 says descriptions are shown in the UI).
- Consent: both buttons stay **disabled** until the box is ticked **and** the code is valid. A hint line under the checkbox says what is missing. The code is stored upper-case.
- The chat header line and the consent text depend on `mock_mode` from `/api/config` (e.g. "Mock mode · replies are not from an AI model"). The full "Mock mode" tag comes in Phase 4.
- The preview-day card and the "preview day N" label only show when `demo_mode` is true (spec 12). They still work in the browser until Phase 3.
- **Kept for now** (to be changed in the phase that makes them true): the risk panel's "chat assessment not connected" line (Phase 5), "Reset demo" (Phase 3/8), and the mentor's provisional-wording notes ("Sample daily question · replace with your final wording").
- **Automated verification (at your request, 4 Nov 2026):** the dev chat ran the app on Linux with headless Chromium and scripted checks 1–6 (47 assertions). 45 passed. The 2 "failures" were mistakes in the test script, not the app: (1) the chat page is 982 px tall in a 900 px window, **identical to the mockup** (the side rail is a full screen tall below the 82 px header); (2) the one console error was the outage the test forced on purpose for check 6 (0 errors otherwise). Computed styles match the mockup exactly: colours, fonts, sidebar 245 px, rail 260 px, header 82 px, h1 size. Screenshots of welcome, chat, summary, dark mode and mobile were compared by eye.
- After that run, the sidebar tag was shortened from "Participant code · no password" to "No password needed" because it wrapped onto two lines, unlike the mockup's one-line tag.
- Your own manual run on Windows is still the deciding check.

**Reference:** `docs/mockup/Stillspace-2.html` (added in Phase 1).

**Files:**
- `frontend/index.html`: markup from the mockup; links `/static/styles.css` and `/static/app.js`
- `frontend/styles.css`: the mockup CSS, unchanged (plus the "Mock mode" tag in Phase 4 and the safety badge style in Phase 5)
- `frontend/app.js`: the mockup JS plus the `api(path, options)` helper; strategy lists built from `/api/config`; participant-code validation; consent routing stubbed (always goes to setup until Phase 3)
- Wording changes: text claiming "nothing is stored", "no AI is connected" or "scripted replies" is replaced with the accurate text from spec section 12, and the footer disclaimer from spec section 16 appears on every step

**Manual checks:**

Before you start: `git pull origin claude/gracious-euler-tlrs89`, make sure `.env` has `STRATEGY_SET=strategies_4`, start the server, and press **Ctrl+F5** in the browser (to skip any cached page).

1. Open http://localhost:8000 in one tab, and `D:\CreatED-cloud\stillspace\docs\mockup\Stillspace-2.html` (double-click it in Explorer) in another. Click through both: welcome, check-ins (all 3 tabs), chat (send a message), reflection, summary.
   **Expect:** same colours, fonts, sidebar steps and right panel. The only visible differences are the participant code field, the reworded texts and the one-line disclaimer under every step.
2. Toggle **◐ Theme**, press **A＋** a few times and **A−**, then narrow the window below 700 px (or press F12 → device toolbar → a phone).
   **Expect:** dark mode, text size and the mobile layout (☰ menu, collapsible "Risk · Support & mood" box) work exactly like the mockup.
3. On the welcome page, try: (a) nothing entered, (b) box ticked but no code, (c) code `ab`, (d) code `P 01!`, (e) box ticked and code `p001`.
   **Expect:** in (a)–(d) both buttons stay disabled and the hint line says what is missing. In (c) and (d) the hint is red ("letters and digits, 3–20 characters"). In (e) both buttons are enabled and continuing works. Press F5 afterwards: the code field shows `P001` (kept in sessionStorage, upper-cased).
4. In a second PowerShell window, in `D:\CreatED-cloud\stillspace`:
   ```powershell
   Select-String -Path frontend\* -Pattern "scripted","nothing is stored","not stored","no AI" -SimpleMatch
   ```
   **Expect:** no output. The disclaimer "Student research prototype. Not therapy, diagnosis or an emergency service. In an emergency call 112 or Tele-MANAS 14416." is visible under every step.
5. (Extra) Press F12 → Console and reload. **Expect:** no red errors. The side panel and setup dropdowns list the 4 strategies. Hovering over an option shows its description (in Chrome/Edge the tooltip may only appear on the closed dropdown). Switch `.env` to `strategies_esconv8`, restart and reload: 8 strategies appear in the dropdowns and the summary bars. Switch back.
6. (Extra) Stop the server (Ctrl+C) and reload the page. **Expect:** a friendly "Stillspace could not start" box with **Try again** (no blank page). Start the server again and click **Try again**: the welcome page appears.

---

### Phase 3: Database, participants, check-ins

**Goal:** participants, scheduling and check-ins are saved in SQLite, with PHQ-9 scored on the server and the frontend routing by status.

**Status:** ✅ Done (4 Nov 2026). The dev chat ran checks 1–8 on a fresh copy at your request: all passed, including the DB one-liners and `DEMO_MODE=false`. Check 3's one-liner was fixed for PowerShell (D-31).

**Files:**
- `backend/db.py`: `get_connection()`, `create_tables()` (all 4 tables from spec 9, including `sessions`/`messages` for Phase 4), participant and check-in helpers
- `backend/checkins.py`: `score_phq9()`, `phq_band()`, `clean_phq_answers()`, `local_today()`, `build_status()`
- `backend/routes/participants.py` *(endpoints later changed to `/api/me/status` and `PATCH /api/me` with sign-in tokens, D-60)*: `POST /api/participants`, `GET /api/participants/{code}/status`, `PATCH /api/participants/{code}`, `POST /api/demo/advance` (404 unless `DEMO_MODE=true`)
- `backend/routes/checkins.py`: `POST /api/checkins` (setup / daily upsert / fortnightly / post_session)
- `backend/main.py`: creates tables on start-up, includes the new routers
- `frontend/app.js`: sign-in and routing, saving check-ins, mood and preference saving, demo buttons, "Switch participant", "New session" keeps the participant
- `frontend/index.html`: one empty `#participantbox` under the sidebar steps (hidden until sign-in)

**What was done / deviations:**
- The consent page's primary button is now **"Continue →"** and routes by status (setup → daily → two-week → chat). **"Skip to chat →"** signs in and goes straight to chat, because check-ins are optional in the mockup (D-26).
- After a refresh, the code kept in `sessionStorage` *(now the sign-in token, D-60)* signs you back in and routes by status. If nothing is due, you land in chat; the Check-ins tab shows the saved answers (D-27).
- Check-in save buttons: the in-card buttons and the bottom button both save, then move to the next due tab (or to chat). Bottom-button labels are now "Save setup →", "Finish daily check-in →" and "Finish two-week check-in →" (the mockup's "Continue to setup/chat" labels no longer fit the new order).
- After a PHQ-9 save, a short toast shows the **server's** result ("Saved. PHQ-9 total 9 (mild)." or "…incomplete, so no total is stored.").
- The risk indicator shows "Follow-up needed" when the live PHQ form has item 9 > 0 **or** the latest saved PHQ-9 has `item9_flag=1` (spec 11.5). Safety replies are added in Phase 5.
- "＋ New session" / "Start new session" (was "Reset demo") keeps the participant and their check-ins and only clears the conversation. The new server session is created in Phase 4.
- "Signed in as P001 / Switch participant" appears under the sidebar steps. It is also visible in the ☰ menu on phones, where the mockup hides the sidebar info box.
- **Automated verification (dev chat, Linux + headless Chromium, throwaway DB):** 17 API cases (scoring, all 5 band boundaries, incomplete PHQ, invalid values, daily merge, demo offset, 404s, demo off) and 33 browser checks covering checks 1–5, refresh, mobile and console errors all passed. Your Windows run is still the deciding check.

**Manual checks:**

Before you start: `git pull origin claude/gracious-euler-tlrs89`, restart the server and press **Ctrl+F5**. If you tested with an older database, delete `data\stillspace.db` first (it is re-created on start-up). The demo buttons ("Next day", "14 days later") are on the **Session summary** page: from chat click **Finish & reflect → View summary**.

1. Open http://localhost:8000, enter code `P001`, tick the box, click **Continue →**.
   **Expect:** you land on the **Once at setup** tab and the sidebar shows "Signed in as P001". Enter a date of birth, choose a style, click **Save setup →** → you move to **Daily / at login**. Pick a mood, click **Finish daily check-in →** → you move to **Every two weeks**.
2. Answer all 9 PHQ items with **1 – Several days**, then click **Finish two-week check-in →**.
   **Expect:** the score shows **9 / 27** and "Mild symptom range" before saving. A toast says "Saved. PHQ-9 total 9 (mild)." and you land in chat. Press **F5**: you are still signed in, the mood and side-panel style are kept, and under **Check-ins → Every two weeks** your answers are still selected, with all three tabs showing "Done".
3. Go to **Finish & reflect → View summary → 14 days later**. On the two-week tab answer items 1–8 and leave item 9 unanswered, then click **Finish two-week check-in →**.
   **Expect:** the score box says "Incomplete · no severity result", and the toast says "…incomplete, so no total is stored". In a second terminal:
   ```powershell
   python -c "import sqlite3; c=sqlite3.connect('data/stillspace.db'); print(c.execute('select id, phq_total, phq_band, phq_complete from checkins where type=? order by id desc limit 1', ('fortnightly',)).fetchone())"
   ```
   **Expect:** something like `(5, None, None, 0)`.
4. Again **Finish & reflect → View summary → 14 days later**. Answer all 9 items, with item 9 = **1**, and save.
   **Expect:** as soon as item 9 is clicked, the follow-up notice ("A human follow-up matters here…") appears and the right-rail risk indicator shows **"Follow-up needed"**. It stays that way after saving and after F5.
5. Click **Switch participant** (sidebar), then sign in again as `P001` with **Continue →**.
   **Expect:** nothing is due, so you go straight to chat. **Finish & reflect → View summary → Next day** → the check-ins open with **Daily · Due** and "preview day N+1". Back on the summary, **14 days later** → **Every two weeks · Due**, with an empty form.
6. Open `data\stillspace.db` in DB Browser for SQLite → **Browse Data** (or run the one-liner below).
   ```powershell
   python -c "import sqlite3; c=sqlite3.connect('data/stillspace.db'); print(c.execute('select code, setup_done, dob, preferred_strategy, demo_day_offset from participants').fetchall()); [print(r) for r in c.execute('select id, type, answers_json, phq_total, phq_band, phq_complete, item9_flag, local_date from checkins')]"
   ```
   **Expect:** `participants` has P001 with `setup_done=1`, your date of birth and `demo_day_offset` > 0. `checkins` has setup, daily and fortnightly rows. Skipped questions are **missing** from `answers_json` (never stored as 0), the incomplete PHQ has `phq_total` empty and `phq_complete=0`, and the last PHQ has `item9_flag=1`.
7. (Extra) Set `DEMO_MODE=false` in `.env`, restart, reload. **Expect:** the summary page has no "Preview repeat visits" card, and the check-ins bar has no "preview day" text. Then:
   ```powershell
   Invoke-RestMethod -Method Post http://localhost:8000/api/demo/advance -ContentType application/json -Body '{"code":"P001","days":1}'
   ```
   **Expect:** a red error ending in `(404) Not Found`. Set `DEMO_MODE=true` again and restart.
8. (Extra) Change "Requested by you" in the side panel to **Advice**, then press F5. **Expect:** it still shows Advice (saved with PATCH, D-29).

---

### Phase 4: LLM client, mock mode, basic chat

**Goal:** chat works end to end with a plain (strategy-free) prompt, in mock mode and with a real key, with friendly errors.

**Status:** ✅ Done (4 Nov 2026). **Check 2 passed on your laptop** with Ollama `qwen3:4b-instruct-2507-q4_K_M`: coherent 2–5 sentence replies, no `<think>`, "AI reply" badge, and the 3rd reply named the meeting as the cause. Checks 1, 3, 4 and 5 were verified by the dev chat only (automated run); you chose to move on.

**Files:**
- `backend/llm.py`: `chat_completion(messages, temperature, max_tokens, model)` → `{"text", "model", "latency_ms"}`, `strip_thinking()`, `LLMError`. Thinking is switched off (D-15, D-33) and `<think>` text is always stripped.
- `backend/mock.py`: `mock_reply(strategy, turn)`. Two reworded canned replies per mockup strategy, about 600 ms delay, and a different reply each turn.
- `backend/data/prompts/plain_system.txt`: the plain prompt (also condition A in Phase 9, D-14)
- `backend/routes/chat.py`: `POST /api/sessions`, `POST /api/chat` (history = last `HISTORY_TURNS` messages, both messages stored, console log line)
- `backend/db.py`: `create_session`, `insert_message`, `recent_messages`, `count_messages`
- `backend/main.py`: includes the chat router
- `frontend/app.js`: a server session on first chat entry (and a new one after "New session"); `send()` calls `/api/chat`; typing indicator; send disabled while waiting; friendly error with **Retry**; reply badge
- `frontend/index.html` + `frontend/styles.css`: small **"Mock mode"** tag in the header tools; a `[hidden]` rule (the mockup's `.tag` style would otherwise override `hidden`); error-line style

**What was done / deviations:**
- Model **errors** (wrong key, unknown model, no internet) return HTTP 502 with a friendly message. The page shows it with a **Retry** button, the terminal prints the real error, and **nothing is stored**, so Retry doesn't duplicate messages. An **empty** model reply (e.g. all thinking) becomes a gentle fallback reply with `source="fallback"` (D-32).
- Until Phase 7 the reply badge shows where the reply came from ("Mock reply", "AI reply" or "Fallback reply"), and "Currently used by model" stays "Awaiting first reply" (D-34).
- `backend/db.py` is now about 185 lines, a little over the ~150 guideline, because all SQL stays in one file for the student. It can be split later if needed.
- **Automated verification (dev chat, Linux + headless Chromium):** 15 browser checks passed in three setups: mock mode; a **fake OpenAI-compatible server** standing in for a real key (it returned `<think>` text, which was stripped; history and `/no_think` reached the model; an empty reply became the fallback); and a wrong key (friendly error + Retry, 0 rows stored, real error in the terminal). A real OpenRouter call could not be tested from the dev chat's network, so **check 2 is yours alone**.

**Manual checks:**

Before you start: `git pull origin claude/gracious-euler-tlrs89`, restart the server, press **Ctrl+F5**.

0. (Model availability, D-23; no key needed) In PowerShell:
   ```powershell
   (Invoke-RestMethod https://openrouter.ai/api/v1/models).data | Where-Object id -like "qwen/*" | Select-Object id, context_length | Format-Table -AutoSize
   ```
   **Expect:** a list of Qwen model IDs that includes `qwen/qwen3-8b`. If it is missing, choose the closest Qwen model from the list and set `LLM_MODEL` in `.env`.
1. `.env` has `LLM_API_KEY=` (empty). Sign in, go to chat, send "I had a long day", then a second message.
   **Expect:** a small **Mock mode** tag next to A−/A＋/Theme. "Stillspace is typing…" shows and **Send** is disabled while waiting. A reply arrives in about 0.6 s with the badge **"Mock reply"**, and the second reply is different from the first. Terminal A shows `[chat] strategy=- safety=none source=mock model=mock 600ms`.
2. Create an OpenRouter key (https://openrouter.ai → Keys; set a small credit limit), put it in `.env` as `LLM_API_KEY=sk-or-...`, restart, reload. Send three messages that build on each other (e.g. "I had a long day" → "mostly because of a meeting" → "what did I say was the cause?").
   **Expect:** no Mock mode tag. Replies are coherent, 2–5 sentences, contain no `<think>` text, have the badge **"AI reply"**, and the third reply remembers the meeting. Terminal A shows `source=llm model=qwen/qwen3-8b NNNNms`.
3. Change the key to `LLM_API_KEY=sk-or-wrong`, restart, send a message.
   **Expect:** under your message a yellow line "The AI model could not be reached just now…" with a **Retry** button (no stack trace). Terminal A shows the real reason, e.g. `[chat] LLM error: AuthenticationError: Error code: 401 ...`. Put the real key back afterwards (or empty it for mock mode).
4. In a second terminal:
   ```powershell
   python -c "import sqlite3; c=sqlite3.connect('data/stillspace.db'); [print(r) for r in c.execute('select id, session_id, role, source, model, latency_ms from messages order by id desc limit 6')]"
   ```
   **Expect:** user rows (source `None`) and assistant rows with `source` `mock`, `llm` or `fallback`, a `model`, and `latency_ms` filled. There are no rows for the failed wrong-key attempt.
5. (Extra) Click **＋ New session** and send a message, then run the check-4 command again. **Expect:** the newest rows have a higher `session_id`.

**Ollama route (free, D-37): replaces the OpenRouter steps in checks 2 and 3**

- Setup (once): check `Get-PSDrive D` (needs ~3–6 GB free). Download **OllamaSetup.exe** from https://ollama.com/download and **save it to `D:\cache\tmp`**. Install it onto D: from PowerShell with `& "D:\cache\tmp\OllamaSetup.exe" /DIR="D:\ollama\app"`. Open a **new** terminal and confirm `echo $env:OLLAMA_MODELS` prints `D:\ollama\models`. Then run `ollama pull qwen3:8b` (≈5 GB; use `qwen3:4b` ≈2.5 GB if you have 8 GB RAM) and `ollama list`.
- Quick model test: `ollama run qwen3:8b "Say hello in one short sentence. /no_think"`. **Expect:** one sentence back (the first run can take a while as the model loads).
- **Your setup (D-39):** start the server in its own terminal with `$env:OLLAMA_MODELS = "D:\ollama\models"; ollama serve` (the tray app ignored the D: setting), then `ollama pull qwen3:4b-instruct-2507-q4_K_M`. `.env`: `LLM_BASE_URL=http://localhost:11434/v1`, `LLM_API_KEY=ollama`, `LLM_MODEL=qwen3:4b-instruct-2507-q4_K_M`. Restart uvicorn.
- **Check 2 (Ollama):** same three messages. **Expect:** no Mock mode tag, coherent 2–5 sentence replies with no `<think>` text, badge "AI reply", the third reply remembers the meeting, and Terminal A shows `source=llm model=qwen3:8b NNNNms` (several seconds is normal on a CPU).
- **Check 3 (Ollama):** Ollama ignores keys, so test a failure with a wrong model name instead: `LLM_MODEL=qwen3:doesnotexist`, restart, send a message. **Expect:** the friendly error with Retry, and Terminal A shows `[chat] LLM error: NotFoundError: ... model ... not found`. Set `LLM_MODEL=qwen3:8b` again.
- `Get-PSDrive C` before and after: C: free space should not drop by gigabytes.

---

### Phase 5: Safety layer

**Goal:** deterministic crisis detection that works in every mode, with the fixed crisis reply, the safety badge, the PHQ item-9 rule in `safety.py`, and the risk indicator.

**Status:** ✅ Done (4 Nov 2026). **Checks 1–7 all passed in the dev chat's run on a fresh copy (4 Nov 2026, at your request)**, with a model server standing in for Ollama: S01–S20 → safety reply 20/20 (0 model calls), N01–N10 → AI reply 10/10, `30 rows, 0 mismatches`, crisis reply in mock mode and with a broken model (`NotFoundError 404` in the log), risk indicator incl. the New-session and PHQ item-9 cases, DB rows with `matched_rule`, `FOLLOWUP_CONTACT` shown.

**Files:**
- `backend/safety.py`: `normalise()`, `variants()`, `find_crisis_match()` (returns the rule id), `check_message()` (True/False), `crisis_response()`, `phq_item9_flag()`, `HELPLINES`
- `backend/data/crisis_keywords.json`: 36 phrases + 13 regex patterns (English, romanised Hinglish, Devanagari), each with an `id`
- `backend/data/prompts/crisis_response.txt`: fixed reply with Tele-MANAS 14416 / 1-800-891-4416 and 112; `{followup_line}` is filled from `FOLLOWUP_CONTACT`
- `eval/safety_prompts.csv`: **30** synthetic, non-graphic rows (`id,message,expect,category`): 20 crisis (direct, indirect, self-harm, stretched letters, look-alike digits, s.e.p.a.r.a.t.e.d, curly apostrophe, danger, Hinglish, Devanagari, slang) and 10 tricky normal ones. Saved as UTF-8 with BOM so Excel shows Devanagari correctly.
- `backend/routes/chat.py`: step 1 of the pipeline. On a match, **no AI call**: the fixed reply is stored with `source="safety"`, `used_strategy="Safety"`, `safety_flag="keyword"` and `meta_json={"matched_rule": "<id>"}`.
- `backend/checkins.py`: PHQ item 9 now uses `safety.phq_item9_flag()` (D-30, same behaviour).
- `frontend/app.js` + `styles.css`: the safety reply has its own style (the mockup's follow-up colours), the badge says **"Safety response"**, and helplines are tap-to-call links. The risk indicator shows "Follow-up needed" after a safety reply in this session. The PHQ item-9 notice now also shows helplines (and the follow-up contact if set), as spec 11.5 requires.
- `frontend/index.html`: the About dialog says chat is checked for crisis words, and that the check can miss things.

**What was done / deviations:**
- **Normalisation before matching (D-22, D-40):** lower case; curly → straight apostrophes, then apostrophes removed (`can't` = `cant`); look-alike swaps inside words (`k1ll`, `$uicide`, `su1cide`) but **not** `!` (so "die!" still matches); dots/dashes between letters removed (`s.u.i.c.i.d.e`); stretched letters checked both ways (`dieee` → `die`, `killlll` → `kill`).
- English and Hinglish phrases match whole words only (spec: word boundaries). Devanagari phrases match as text, because Python's word boundary breaks on Devanagari vowel signs.
- A safety reply sets the session flag. "＋ New session" (or a refresh, which starts a new session) clears it; the latest PHQ item-9 rule still applies.
- **Automated verification (dev chat):** all 30 rows correct directly (`check_message`) and in the browser in mock mode (20/20 crisis with 14416 + 112 + "Safety response", 10/10 normal). Crisis replies also work with a **wrong key** (0–3 ms, no AI call) and with a model server (that server received **0** calls for the crisis message). `FOLLOWUP_CONTACT` appears in the crisis reply and the PHQ notice. 25 extra unseen crisis phrasings were all caught. 1 of 16 extra normal phrasings was flagged: **"I love the movie suicide squad"**, kept on purpose (K-03). Phases 3 and 4 regression checks still pass.

**Manual checks:**

Before you start: `git pull origin claude/gracious-euler-tlrs89`, keep Terminal C (`ollama serve`) running for check 3b, restart uvicorn, press **Ctrl+F5**.

1. Open `eval\safety_prompts.csv` (Excel or Notepad). In the chat, send every row with `expect` = **crisis** (S01–S20). Copy and paste them; you don't need to type them.
   **Expect:** each one gets the same fixed reply in a gold box with a dark-orange left border, the badge **"Safety response"**, and the line "Tele-MANAS: 14416 or 1-800-891-4416 (free, 24x7) · Emergency: 112". Terminal A shows `[chat] strategy=Safety safety=keyword rule=<id> source=safety` and **no** model call.
2. Send every row with `expect` = **normal** (N01–N10, e.g. "This exam is killing me").
   **Expect:** normal AI replies (badge "AI reply" or "Mock reply"), with no helplines. Note any row that wrongly gets the crisis reply.
3. Quick check without the browser (Terminal B):
   ```powershell
   python -c "import csv; from backend.safety import check_message; rows=list(csv.DictReader(open('eval/safety_prompts.csv', encoding='utf-8-sig'))); bad=[r for r in rows if check_message(r['message']) != (r['expect']=='crisis')]; print(len(rows), 'rows,', len(bad), 'mismatches'); [print('MISMATCH', r['id'], r['expect'], r['message']) for r in bad]"
   ```
   **Expect:** `30 rows, 0 mismatches`.
4. Repeat two crisis messages (e.g. S01 and S17) (a) in **mock mode** (`LLM_API_KEY=` empty, restart) and (b) with a **broken model** (`LLM_MODEL=qwen3:doesnotexist`, restart).
   **Expect:** the crisis reply appears instantly both times. In (b), a normal message afterwards shows the friendly error with Retry, proving the model really is broken. Put `.env` back afterwards.
5. After any safety reply, look at the right rail.
   **Expect:** the risk indicator shows **"Follow-up needed"** with "A message in this conversation needs a human follow-up…", and "Currently used by model" shows **Safety**. Click **＋ New session** (as a participant whose latest PHQ has item 9 = 0): it goes back to **"Not assessed"**. No percentage is ever shown.
6. (Extra) Database check:
   ```powershell
   python -c "import sqlite3; c=sqlite3.connect('data/stillspace.db'); [print(r) for r in c.execute('select id, role, used_strategy, safety_flag, source, meta_json from messages where safety_flag != ? order by id desc limit 4', ('none',))]"
   ```
   **Expect:** user and assistant rows with `Safety`, `keyword`, source `safety` (assistant) and `{"matched_rule": "..."}`.
7. (Extra) Set `FOLLOWUP_CONTACT=Ms Rao (study lead)` in `.env`, restart, send a crisis message, and answer PHQ item 9 with 1.
   **Expect:** "You can also contact Ms Rao (study lead)…" in the crisis reply, and "Follow-up contact for this study: Ms Rao (study lead)" in the PHQ notice. Clear it again afterwards.

---

### Phase 6: Strategy classifier

**Goal:** a robust classifier returning valid JSON every time (real or mock), plus an evaluation script.

**Status:** ✅ Done (4 Nov 2026). Checks 1–3 passed on your laptop; check 5 (qwen3:8b) was tried and rejected (D-43).

**Results with `qwen3:4b-instruct-2507-q4_K_M` (Ollama, RTX 4050):**

| Measure | Result |
|---|---|
| Accuracy | **27/30 = 90%** |
| Valid JSON | 30/30 (`source=llm` for every row; 0 retries, 0 fallbacks) |
| Per strategy (recall) | Validation 8/8 · Reflection 7/7 · Reassurance **5/8** · Advice 7/7 |
| Predicted counts (bias check) | Validation 10 · Reflection 8 · Reassurance 5 · Advice 7 (no preference bias) |
| Misses | T18 "What if I never find friends…" → Reflection; T21 "…I feel so far behind" → Validation; T23 "…everyone hates me now" → Validation |
| Speed | ~3.4 s per message (8.3 s for the first while the model loads) |
| Other | Confidence was 0.95–0.98 on every row, even the misses (not calibrated; don't rely on it). Risk was `low` on all 30 (no crisis wording in the set). |

**Comparison run with `qwen3:8b` (check 5, stopped after 5 messages):** every answer was cut off or missing ("JSON object is not closed" / "no JSON object"), so all 5 used the fallback defaults, at **35–51 s per message**. Cause: `qwen3:8b` is a *hybrid* model that thinks by default; the classifier's single user message never got `/no_think` (it was only added to system messages), and 8B does not fit fully into the 6 GB GPU. **Result: keep `qwen3:4b-instruct` for both classifier and replies.** Code fix D-43: `/no_think` now goes on the last message when there's no system message (hybrid Qwen3 only), which also matters for the handoff model `qwen/qwen3-14b`.

**Decision:** the prompt is **not** tuned for these 3 misses, because tuning on the test set would make the score meaningless. The misses become the Session 8 exercise ("improve descriptions") in mentoring.md (D-42).

**Files:**
- `backend/classifier.py`: `classify(message, history, strategies)` → `{strategy, emotion, intensity, stage, risk, confidence, rationale, source, latency_ms}`; `parse_classifier_output()` (removes thinking text and code fences, finds the first `{...}`, validates with pydantic, keeps values in range); `build_classifier_prompt()`; `fallback_result()`. Temperature 0, max 200 tokens, model `CLASSIFIER_MODEL`, one retry, then defaults.
- `backend/data/prompts/classifier.txt`: the classifier prompt (strategy names + descriptions, choosing hints, emotion/stage/risk rules incl. "unsure → high", history, new message, JSON-only answer).
- `backend/mock.py`: `mock_classify()` keyword rules (asks what to do → Advice; worry words → Reassurance; unclear or mixed → Reflection; else Validation), with fixed meta values. For the ESConv-8 set it uses the closest strategy name.
- `eval/test_messages.csv`: 30 synthetic messages labelled for **strategies_4** (8 Validation, 7 Reflection, 8 Reassurance, 7 Advice).
- `scripts/eval_classifier.py`: prints the accuracy, a per-strategy table (correct/expected, precision, recall), a confusion table, how often each strategy was predicted (preference-bias check) and how many fallbacks were used; writes `exports/classifier_results.csv`. Option `--limit N`.
- Strategy files reviewed: no wording change needed (D-07).

**What was done / deviations (D-41):**
- The classifier is **not yet used in the chat**. Phase 7 wires it in, together with the second safety check (`risk == "high"`).
- The whole classifier prompt is sent as **one user message** (not as a system message), so the model analyses it instead of chatting with it. Placeholders are filled with `.replace()` because the template contains JSON braces.
- Risk values other than none/low/high (e.g. "medium") are treated as **high**: safety first, following the spec's "when unsure, choose high". If parsing fails completely, the spec's fallback (`risk: "none"`, "classifier unavailable") is used; the keyword check still protects that path.
- **Automated verification (dev chat):** 13 odd-output cases for the parser (code fences, chatty text, `<think>`, lone `</think>`, out-of-range values, numbers as text, unknown names, missing fields, braces inside the rationale; no JSON, broken JSON and empty text all raise and trigger the retry); evaluation runs in mock mode (93%), against a fake model server (retry worked once; an always-broken answer fell back to the defaults and was reported; all 30 CSV rows valid), and with the ESConv-8 set (clear warning). **The mock score is not meaningful**, because the dev chat wrote both the mock rules and the test messages. Your model's score in check 1 is what counts.

**Manual checks:**

Before you start: `git pull origin claude/gracious-euler-tlrs89`. Terminal C (`ollama serve`) must be running, `.env` as in memory.md (`LLM_API_KEY=ollama`, `LLM_MODEL=qwen3:4b-instruct-2507-q4_K_M`, `STRATEGY_SET=strategies_4`). The server (Terminal A) does not need to run for this phase.

1. In Terminal B:
   ```powershell
   python scripts/eval_classifier.py
   ```
   **Expect:** a header line naming your model, 30 progress lines (`expected=... predicted=... OK/X (llm, NNNms)`), then `Accuracy: NN/30 = NN%`, a per-strategy table, a confusion table, the predicted-strategy counts, and `Saved 30 rows to ...\exports\classifier_results.csv`. It takes about a minute on your GPU.
2. Open `exports\classifier_results.csv` in Excel.
   **Expect:** 30 rows. Every row has a valid `predicted` strategy (one of the 4), an `emotion`, an `intensity` from 1 to 5 and a `stage`. The `source` column shows `llm` (or `fallback` if the model's answer was unusable, which the summary also reports). No crash.
3. Look at "How often each strategy was predicted".
   **Expect:** not all 30 the same (no `WARNING: every message got the same strategy`). **Tell me the accuracy line and these four counts**, and I'll record them here.
4. (Extra) Mock mode, for comparison: set `LLM_API_KEY=` and run `python scripts/eval_classifier.py --limit 5`. **Expect:** the header says `MOCK classifier`, with 5 rows in well under a second. Set the key back afterwards.
5. (Extra, optional) Pull the larger model (`ollama pull qwen3:8b`, ~5 GB on D:), run `$env:CLASSIFIER_MODEL="qwen3:8b"; python scripts/eval_classifier.py`, then `Remove-Item Env:CLASSIFIER_MODEL`. **Expect:** a second accuracy number to compare. (`qwen3:8b` is a hybrid model; `think:false` is sent automatically.)

---

### Phase 7: Prompt builder and strategy-aware replies

**Goal:** the full pipeline from spec section 5, an explainability panel, and a saved preference.

**Status:** ✅ Done (4 Nov 2026). **Your run (4 Nov 2026, qwen3:4b-instruct):** check 1 ✅ (Reflection; "confusion · intensity 3/5 · exploration"), check 2 ✅ (Advice with a concrete small step), check 5: Validation, Reassurance and Advice distinct, but **Reflection repeated the Validation reply word for word**, because the same message was sent repeatedly in one conversation and the model copied its previous reply from the history. Check 5 now says to start a new session before each strategy (D-45).
**Dev-chat run of checks 1–7 on a fresh copy (4 Nov 2026, at your request; model server standing in for Ollama):** all passed. Check 1 Reflection + "Emotion: sadness · intensity 4/5 · stage: exploration"; check 2 Advice + "Classifier suggested Validation; your request was used."; check 3 Advice kept after F5, Automatic kept after F5; check 4 printed prompt contains the strategy instruction, "- Mood today: Low" and "- Recent wellbeing questionnaire: moderate range", and the date of birth and raw PHQ answers appear neither in the log nor in any request to the model; check 5 with a new session each time: 4 matching badges, 4 different replies, and each request contained only `[system, user]` (no earlier history); check 6 with `INCLUDE_CHECKINS_IN_PROMPT=false`: no mood or questionnaire lines; check 7 DB rows with requested/classified/used filled.

**Files:**
- `backend/strategy_policy.py`: `choose_strategy(requested, classified, safety_flag, strategy_names)`, exactly spec 11.2 (safety → request → classifier → first strategy).
- `backend/prompt_builder.py`: `build_messages()` → `[system, ...history, user]`; `build_system_prompt()`; `checkin_lines()` (only "Mood today" and the PHQ **band**, and only when `INCLUDE_CHECKINS_IN_PROMPT=true` and the data exists).
- `backend/data/prompts/system.txt`: the spec 11.4 text with placeholders.
- `backend/routes/chat.py`: the full pipeline. (1) keyword safety → (2) classifier (with history) → (3) `risk == "high"` → fixed safety reply with `safety_flag="classifier"` → (4) strategy policy → (5) prompt builder with check-in context → (6) reply (model or mock reply for the used strategy) → (7) store both messages with requested/classified/used strategy and `meta_json`. Console line: `[chat] strategy=Advice (requested=Advice, classified=Validation) emotion=sadness safety=none source=llm 6400ms`. Contains the commented `# DEBUG: print system prompt` line for check 4.
- `backend/checkins.py`: `checkin_context()` returns only today's mood and the latest **complete** PHQ-9 band. `backend/db.py`: `get_participant_by_id()`.
- `backend/data/crisis_keywords.json`: new rule `en-sleep-never-wake` ("sleep and never wake up"), found while writing the tests.
- `frontend/app.js`: the explainability panel under "Currently used by model" (emotion · intensity · stage, plus "Classifier suggested X; your request was used." when your request overrode it). The reply badge shows the used strategy; safety and fallback replies keep their own badges.

**What was done / deviations (D-44):**
- `meta_json` stores emotion, intensity, stage, risk, confidence, rationale, `classifier_source` (llm/mock/fallback) and `classifier_ms`. `latency_ms` is the **total** time the person waited (classifier + reply).
- The classifier sees the same recent history as the reply model.
- A refresh starts a new chat session (D-27), so the summary counts only the current session. Earlier messages stay in the database (K-07).
- **Automated verification (dev chat):** strategy policy 8/8 cases; prompt builder 9/9 incl. the privacy rule; browser checks 1, 2, 3 and 5 in mock mode and against a fake model server; check 4 by inspecting what the model server received: strategy instruction, "Mood today: Low" and "moderate range" present, date of birth and raw PHQ answers **absent from every request**; classifier `risk: high` on an indirect message → Safety response + "Follow-up needed"; Phase 3 (33/33) and Phase 5 safety checks still pass. Expected changes: badges now show strategy names instead of "Mock reply"/"AI reply".

**Manual checks:**

Before you start: `git pull origin claude/gracious-euler-tlrs89`; Terminal C (`ollama serve`) running; restart uvicorn; **Ctrl+F5**. For check 4 you need a participant with today's mood and a complete PHQ-9 (e.g. sign in as a new code like `P010`, then complete setup, daily with mood "Low", and all 9 PHQ items). Expect about 6–9 s per reply with Ollama (two model calls).

1. With "Requested by you" = **Automatic**, send "I don't know why I feel off today".
   **Expect:** the reply badge shows a strategy (likely **Reflection**). The side panel shows it under "Currently used by model", and below it in small text "Emotion: … · intensity N/5 · stage: …". Terminal A: `[chat] strategy=Reflection (requested=Automatic, classified=Reflection) emotion=... safety=none source=llm ...ms`.
2. Set "Requested by you" to **Advice** and send "I can't focus on studying".
   **Expect:** badge and panel show **Advice**. The reply suggests one or two small concrete steps. If the classifier would have chosen something else, the panel adds "Classifier suggested …; your request was used."
3. Press **F5**. **Expect:** "Requested by you" still shows **Advice**. Set it back to **Automatic**.
4. In `backend\routes\chat.py` find the line ending in `# DEBUG: print system prompt` and remove the `# ` at its start (save; uvicorn reloads). Send a message.
   **Expect:** Terminal A prints the system prompt with "Support strategy for this reply: …", "How to apply it: …", "- Mood today: Low" and "- Recent wellbeing questionnaire: … range". **No** date of birth and no individual PHQ answers. Put the `# ` back afterwards (or run `git checkout backend/routes/chat.py`).
5. Send "My friends have been ignoring me" four times, with "Requested by you" set to **Validation**, **Reflection**, **Reassurance** and **Advice** in turn. **Click "＋ New session" before each one**, so the earlier reply in the history doesn't steer the model (D-45).
   **Expect:** the four badges match the four choices and the replies read noticeably differently (Validation names the feeling; Reflection paraphrases and asks; Reassurance offers perspective; Advice gives a small step).
6. (Extra) Set `INCLUDE_CHECKINS_IN_PROMPT=false`, restart and repeat check 4. **Expect:** no "Mood today" or "questionnaire" lines. Set it back to `true`.
7. (Extra) Database:
   ```powershell
   python -c "import sqlite3; c=sqlite3.connect('data/stillspace.db'); [print(r) for r in c.execute('select id, role, requested_strategy, classified_strategy, used_strategy, safety_flag, source from messages order by id desc limit 4')]"
   ```
   **Expect:** requested, classified and used strategy all filled (e.g. `('Advice', 'Validation', 'Advice', 'none', 'llm')`).

---

### Phase 8: Reflection, summary, export

**Goal:** sessions end cleanly, the reflection is saved, the summary comes from the server, and data exports to CSV.

**Status:** ✅ Done (4 Nov 2026). **Checks 1–4 all passed in the dev chat's run on a fresh copy (mock mode, 4 Nov 2026, at your request):** check 1 "Messages sent 3", server time 00:04, bars Validation 2 / Advice 1 matching the badges, reflection shown, PHQ "9 / 27 · Mild", log `session 1 ended after 4s`; check 2 "Reflection skipped."; check 3: 4 CSVs, each with the Excel marker, consistent columns and no garbled text; check 4: `(4, 'post_session', 1, '{"comfort": 7, "validation": 8, "useful": "Yes"}')` and `(5, 'post_session', 2, '{}')` from "Review reflection".

**Files:**
- `backend/routes/sessions.py` (new, D-52): `POST /api/sessions` (moved from chat.py), `POST /api/sessions/{id}/end` (stores `ended_at` and `chat_seconds` using the server clock, D-13), `GET /api/sessions/{id}/summary` → `message_count`, `reply_count`, `chat_seconds`, `strategy_counts` (incl. `Safety`), `requested_strategy`, `last_used_strategy`, `latest_phq`, `reflection`, `started_at`, `ended_at`.
- `backend/routes/chat.py`: now only `POST /api/chat` (135 lines).
- `backend/db.py`: `end_session()`, `used_strategy_counts()`, `last_message()`, `reflection_for_session()`.
- `frontend/app.js`: **Finish & reflect** → `/end` → reflection; **View summary** saves the answers as a `post_session` check-in with the `session_id`; **Skip for now** saves nothing; the summary page loads from `/summary` (with a loading line and a friendly error + Try again), showing the server's chat time, messages sent, the **latest saved PHQ-9** (mockup score box with its date), strategy bars, a "Safety responses: N" line if any, requested vs last used style, and the reflection answers (or "Reflection skipped.").
- `scripts/export_data.py`: one CSV per table in `exports/` (`participants`, `checkins`, `sessions`, `messages`), UTF-8 with BOM for Excel (D-17), with a privacy reminder.

**What was done / deviations (D-52):**
- Session endpoints moved to `routes/sessions.py` so `chat.py` stays near the ~150-line guideline (spec 7 listed them under chat.py).
- `chat_seconds` = from opening the chat to clicking Finish (server clock), so it can include pauses (e.g. a visit to the check-ins tab). Finishing again later updates it. A session that was never ended counts up to "now" in the summary.
- Strategy bars are shares of all **replies** in the session. A refresh starts a new session (K-07), so the summary shows the current session only.
- "Review reflection" → "View summary" saves the reflection again; the summary shows the latest one.
- Exports overwrite the previous files each run.
- `backend/db.py` is now 214 lines; it will be restructured in Phase 11 when Postgres support is added.
- **Automated verification (dev chat):** API: end, summary, post_session with session_id, 404s; browser: check 1 (3 messages → "Messages sent 3", server time 00:04, bars Validation 2 / Advice 1 matching the badges, reflection "comfortable 7/10 · understood 8/10 · helpful: Yes", latest PHQ "9 / 27 · Mild"), check 2 (skip → "Reflection skipped.", summary loads), Review reflection flow; check 3: 4 CSVs with BOM and headers. Phase 3 (33/33) and Phase 7 (9/9) regressions pass.

**Manual checks:**

Before you start: `git pull origin claude/gracious-euler-tlrs89`, restart uvicorn, **Ctrl+F5**. Mock mode is quickest for this phase (`LLM_API_KEY=` empty); Ollama works too.

1. Sign in, chat **3 messages** that lead to at least two different strategies (e.g. "I had a long day at school", "What should I do to relax tonight?", "My friends were mean to me"). Click **Finish & reflect**, answer the three reflection questions, click **View summary**.
   **Expect:** "Messages sent 3"; "Conversation time" roughly how long you chatted; the strategy bars match the badges you saw (e.g. Validation 2 replies, Advice 1 reply); "Your reflection: comfortable N/10 · understood N/10 · helpful: …"; the PHQ-9 box shows your latest saved PHQ-9 with its date. Terminal A: `[chat] session N ended after Ns`.
2. Click **Start new session**, send one message, click **Finish & reflect**, then **Skip for now**.
   **Expect:** the summary still loads: "Messages sent 1" and "Reflection skipped."
3. In Terminal B:
   ```powershell
   python scripts/export_data.py
   ```
   ```powershell
   dir exports
   ```
   **Expect:** `participants.csv`, `checkins.csv`, `sessions.csv`, `messages.csv` (plus `classifier_results.csv` from Phase 6), and the row counts printed. Open each in Excel: columns are separated correctly and text looks right (no `Ã©`-style garbling).
4. (Extra) Database check of the reflection link:
   ```powershell
   python -c "import sqlite3; c=sqlite3.connect('data/stillspace.db'); [print(r) for r in c.execute('select id, type, session_id, answers_json from checkins where type=? order by id desc limit 3', ('post_session',))]"
   ```
   **Expect:** rows with your `session_id` and answers like `{"comfort": 7, "validation": 8, "useful": "Yes"}`.

---

### Phase 9: Evaluation kit

**Goal:** a script that produces a human-rating sheet comparing condition A (no strategy, plain prompt) with condition B (full pipeline), optionally for several models.

**Status:** ✅ Done (4 Nov 2026). **Checks 1–4 all passed in the dev chat's run on a fresh copy (4 Nov 2026, at your request)**, with a model server on Ollama's own address (`localhost:11434`), so check 2's exact `ollama:qwen3:8b` command ran unchanged: check 1 → `= 10 rows` + both files; check 2 → 20 rows, model column `qwen3:4b-instruct-2507-q4_K_M` ×10 and `ollama:qwen3:8b` ×10 (the prefix is kept in the column, so you can see which provider was used); check 3 → A rows empty / B rows filled for strategy, emotion, intensity and stage, rating columns empty, Excel marker present, blind sheet shuffled (`BBAABABAAB`) without condition/model/strategy; check 4 → 6 rows rated and saved in Excel's Windows encoding, `--summarise` printed the per-condition table.

**Files:**
- `scripts/eval_responses.py`:
  - **A** = `prompts/plain_system.txt` + the message. **B** = classifier → strategy policy ("Automatic") → `prompt_builder` → reply, i.e. the chat pipeline. **Neither condition gets history or check-in context**, so the only difference is the strategy layer (D-45, D-53). The keyword safety check applies to both; a classifier `risk: high` in B gives the safety reply.
  - Options: `--limit N`, `--models m1,m2` (prefix **`ollama:`** = the local Ollama server; other names use the `.env` provider; the same model does the classifier and the reply), `--seed` (default 42), `--summarise <blind sheet>`.
  - Writes **two files** to `exports/`:
    - `responses_<time>.csv`: everything, for analysis: `item_id, id, message, strategy_to_check, model, condition (A_no_strategy / B_pipeline), classified_strategy, used_strategy, emotion, intensity, stage, risk, safety_flag, source, latency_ms, reply` + empty `empathy_1to5, strategy_followed_yes_no, safe_yes_no, notes`.
    - `rating_sheet_<time>_blind.csv`: the **same rows shuffled**, showing only `item_id, message, strategy_to_check, reply` + the empty rating columns, with **no condition, model or strategy**, so raters can't favour one condition.
  - `strategy_to_check` = the test set's expected strategy for **every** row, so "strategy followed" measures A and B with the same yardstick. B's own choice is kept in the full file.
  - `--summarise` joins a rated blind sheet with its responses file (by `item_id`) and prints per model × condition: number rated, mean empathy, % strategy followed, % safe. It reads files re-saved by Excel (UTF-8 or Windows encoding).
  - Model errors become a visible `[ERROR: …]` row (`source=error`) instead of a crash; mock mode works offline.

**What was done / deviations (D-53):** blind shuffled sheet + summarise mode are additions beyond the spec (which asks for one CSV with empty rating columns; that file is `responses_<time>.csv`). **Automated verification (dev chat):** check 1 → 10 rows + blind sheet; check 2 → 20 rows (5 per model × condition), model column filled; check 3 → A rows have no strategy metadata, B rows do, and B replies used their strategy; the blind sheet hides condition/model/strategy and is shuffled; `ollama:` switches to Ollama and the next model switches back; mock mode; a crisis message gets the safety reply in both conditions; `--summarise` round trip with an Excel-encoded (cp1252) sheet.

**Manual checks:**

Before you start: `git pull origin claude/gracious-euler-tlrs89`; Terminal C (`ollama serve`) running; `.env` with your Ollama model. The app server is not needed. Expect about 10 s per message with Ollama (A = 1 call, B = 2 calls).

1. ```powershell
   python scripts/eval_responses.py --limit 5
   ```
   **Expect:** `Reply evaluation | 5 messages x 1 model(s) x 2 conditions = 10 rows`, 10 progress lines (`T01 A - llm …`, `T01 B Validation llm …`), then `Saved 10 rows:` naming `exports/responses_<time>.csv` and `exports/rating_sheet_<time>_blind.csv`.
2. Run with two models. If you kept `qwen3:8b`, use it as the second (it's slow, about 1–2 min per message; 5 messages is fine):
   ```powershell
   python scripts/eval_responses.py --limit 5 --models qwen3:4b-instruct-2507-q4_K_M,ollama:qwen3:8b
   ```
   **Expect:** `= 20 rows`; the new `responses_…csv` has 20 rows with the `model` column filled with both names. (No second model installed? Use `--models qwen3:4b-instruct-2507-q4_K_M,ollama:qwen3:4b-instruct-2507-q4_K_M` just to see the doubling, or skip this check.)
3. Open the `responses_…csv` from check 1 in Excel.
   **Expect:** rows with condition `A_no_strategy` have empty `classified_strategy, used_strategy, emotion, intensity, stage`; rows with `B_pipeline` have them filled; the four rating columns are empty. Then open the `rating_sheet_…_blind.csv`: shuffled rows **without** condition, model or strategy columns.
4. (Extra) Try the rating workflow: in the blind sheet, fill `empathy_1to5` (1–5), `strategy_followed_yes_no` and `safe_yes_no` (yes/no) for a few rows, save it as CSV, then:
   ```powershell
   python scripts/eval_responses.py --summarise exports\rating_sheet_<time>_blind.csv
   ```
   **Expect:** a table with one line per model and condition: rated count, mean empathy, % followed, % safe.

---

### Phase 10: Handover docs, student starter and mentoring.md

**Goal:** everything a beginner and the mentor need. `mentoring.md` is written **last**, only after you confirm the docs and the starter work (spec 14), so it matches the final code.

**Status:** ✅ **Done (4 Nov 2026).** Part 1 (docs + `student_starter/`) and Part 2 (`mentoring.md`) are built. You said the checks are not your task (you only develop), so the dev chat ran them all on a fresh clone (results below). The mentor should still do check 1 once on Windows before session 2 (K-11).

**Part 2: files:**
- `mentoring.md` (~1,300 lines): course overview (learning outcomes, session map, installs before session 2, how online sessions run, catch-up plan, how to give the student only the starter as a zip), the **safety briefing script** for session 1, all **16 sessions** with every part from spec 15.1 (goal, mentor prep, time plan, concepts with an analogy and questions, hands-on steps naming exact starter files/functions/TODOs with hints before answers, done-when with expected output, common errors, answer-key location, homework, next-session preview), and the appendix (glossary, presentation rubric, final demo checklist, answer-key map, real bugs from the build as teaching stories).
- `student_starter/docs/`: copies of `SETUP.md`, `SAFETY.md`, `TROUBLESHOOTING.md`, `ARCHITECTURE.md`, so a student who only gets the starter zip has them (D-59). The starter README points to them.
- `backend/safety.py` + starter copy: new rule joins spaced single letters (`d i e` → `die`), found while writing Session 5 (D-58). `docs/SAFETY.md` lists it.
- `.env.example` (both): the Ollama comment now names the instruct model instead of `qwen3:8b`.

**Dev-chat results (fresh clone of the branch, Linux sandbox):**
- Check 1/5: clone + venv + `pip install` + `.env` took 13 s (fast network; on a home connection expect a few minutes, well under 10). Finished app on 8000 and starter on 8001 start in mock mode.
- Check 2: script check, all 34 file paths and 31 functions named in `mentoring.md` exist; all 16 sessions have every spec 15.1 part.
- Check 3: finished Session 4/6/7/9 functions copied into a starter copy with a fake model server: `eval_classifier.py --limit 5` → `(llm, …ms)` rows + accuracy; policy one-liner → `Advice Reflection Validation Safety`; prompt has the strategy, meta and mood with no `{…}` left; the reply call carries the history (memory works); requested Advice → badge Advice.
- Check 4: starter in the browser: mock tag, placeholder badge Validation, crisis row → Safety response with 14416 and Follow-up needed; safety test 30/0 in both folders.

**Part 1: files:**
- `README.md`: what it is, the 10-minute mock-mode quick start, real model (OpenRouter or Ollama), folder map, documentation index, privacy paragraph, disclaimer.
- `flow.md` (**new, at your request**): who uses the app; local vs online mode; **sign-up and sign-in** (no accounts: local = any new code creates a participant; online = only researcher-issued codes); the participant journey with the API call and table behind each step; the 7-step chat pipeline; safety; researcher scripts; where data goes; FAQ. Mermaid diagrams (GitHub shows them as pictures).
- `docs/SETUP.md`: Windows-first beginner setup (Python with "Add to PATH", VS Code, Git, DB Browser; clone; venv; execution policy; pip with timeouts; `.env`; run; browser; every-day routine), optional OpenRouter (with a spending limit) or Ollama (instruct model), a low-disk/D: note, a macOS/Linux table.
- `docs/ARCHITECTURE.md`: frontend vs backend, the pipeline diagram, every file's job with its teaching session, data/prompt files, tables, endpoints, how to switch model / strategy set / database / production, design choices.
- `docs/SAFETY.md`: ground rules (synthetic only, approvals), the 5 safety layers, what the keyword check catches, known limits (incl. the kept false positive), the safety test, **what to do if a real disclosure happens**, online safeguards, data and privacy.
- `docs/TROUBLESHOOTING.md`: every problem met during the build and more (startup, Windows quirks, browser, AI model, Ollama on Windows, database/Supabase, scripts), each with the fix.
- `student_starter/`: the full app (own `README.md`, `.gitignore`, `data/`) where these are **TODO stubs with step-by-step docstrings, hints and safe placeholders**:

  | Session | Stub | Placeholder until written |
  |---|---|---|
  | 4 | `llm.chat_completion()` | returns a reply saying it's a TODO (no model called) |
  | 4 + 9 | `prompt_builder.build_messages()` | plain prompt + new message (no memory, no strategy) |
  | 6 | `strategy_policy.choose_strategy()` | `"Safety"` line already there (never removed); otherwise the first strategy |
  | 7 | `classifier.classify()` + `parse_classifier_output()` + `prompts/classifier.txt` (skeleton with TODOs) | mock rules in mock mode; otherwise default values |
  | 9 | `prompt_builder.build_system_prompt()` | the plain prompt |
  | 5 | `safety.check_message()` | **fully working** (keyword safety stays on, spec 15), with an optional TODO to study and improve it |

  Every placeholder prints `[TODO Session N] …` in the terminal. Helpers like `strip_thinking`, `extract_json_object`, `clean_risk`, `checkin_lines` stay written, so each session fits in the hour (D-57).

**Automated verification (dev chat):** the starter's safety test → `30 rows, 0 mismatches`; in mock mode on port 8001: check-ins, PHQ, chat, **crisis → Safety response**, reflection, summary, no page errors; with a model configured: placeholders stay safe (TODO reply text, `[TODO Session 4]` / `[TODO Session 7]` printed once each, `eval_classifier.py` runs with `fallback`); **after swapping in the finished functions for Sessions 4 and 7**: `eval_classifier.py` shows `source=llm` on every row, chat replies come from the model, and the 2nd message sends `[system, user, assistant, user]` (memory).

**Manual checks** (spec 14; checks 2 and 3 run after Part 2):

1. Follow `docs/SETUP.md` in a **fresh folder** as if you were the student (on your laptop keep it on D:, e.g. `git clone https://github.com/harsh300604/stillspace.git D:\CreatED-cloud\stillspace-test`, then `git checkout claude/gracious-euler-tlrs89`), without using knowledge from the build. **Expect:** it works end to end in mock mode. Note any step that was unclear.
2. *(after `mentoring.md`)* Read `mentoring.md`. **Expect:** all 16 sessions have every part from spec 15.1, and every file and function it names exists.
3. *(after `mentoring.md`)* Copy `student_starter\` to e.g. `D:\CreatED-cloud\starter-try` and do the student tasks of **sessions 4 and 7** exactly as written. **Expect:** their "done when" checks pass.
4. In `student_starter\` (its own venv, or reuse the main one):
   ```powershell
   cd student_starter
   ```
   ```powershell
   Copy-Item .env.example .env
   ```
   ```powershell
   uvicorn backend.main:app --reload --port 8001
   ```
   **Expect:** http://localhost:8001 runs in mock mode; chat replies use "Validation" whatever you request (TODO); a crisis message (S01) gets the **Safety response**; with a model in `.env` the reply says it's a Session 4 TODO and the terminal prints `[TODO Session 4] …`. Safety test in that folder: `30 rows, 0 mismatches`.
5. Time yourself following the `README.md` quick start in a fresh clone. **Expect:** under 10 minutes.
6. (Extra) Read `flow.md`. **Expect:** the sign-up/sign-in answers and the diagrams match what you saw while testing.

---

### Phase 11: Deployment readiness (Supabase + online safety)

> **Added after the spec, at the developer's request (4 Nov 2026).** The spec's prototype is local-only (sections 3 and 16). Sharing the app with other people turns it into a study with real participants. **The legal and ethical approvals in the `docs/DEPLOYMENT.md` checklist are your responsibility and must be in place before any link is shared.**

**Goal:** the same app runs (a) locally on SQLite exactly as before (student course, offline, mock mode), or (b) online for a small, approved group, with Supabase Postgres, researcher-issued codes, rate limits, a safety report, consent and an age check, and no demo or debug endpoints.

**Status:** ✅ Done (4 Nov 2026). **Your run (4 Nov 2026):** check 2 ✅ on your real Supabase project: `db.describe()` → `postgres (aws-0-ap-northeast-1.pooler.supabase.com)`, all 4 tables `rowsecurity: True`; `create_codes.py --count 3` wrote 3 issued codes. Region is **Tokyo** (see K-10). You confirmed checks 3–7 done. Check 8 (a real Railway/Render deployment) and check 9 (the pre-launch checklist) happen when you go live.

**What was built (D-46 to D-55):**

| Area | Built |
|---|---|
| Database | `backend/db_connect.py` (new): SQLite when `DATABASE_URL` is empty, **Postgres (Supabase)** when set; `run()` swaps `?` → `%s`, `insert()` returns the new id (`lastrowid` / `RETURNING id`); `describe()` for the start-up line (never prints the password). Tables in `backend/data/schema_sqlite.sql` / `schema_postgres.sql` (Postgres: **RLS enabled on all 4 tables, no policies**). Older SQLite files get the new columns automatically. `db.py` keeps only query helpers (173 lines). New package `psycopg[binary]` (D-47). |
| Sign-in | `APP_ENV=production` → **only codes made by `scripts/create_codes.py` (marked `issued=1`, D-56)** (e.g. `SS-RVAN-E3PK`, 8 random characters, no look-alike letters); unknown or malformed codes get the same message; codes may now contain hyphens. **10 sign-ins per minute per IP** (real IP from `X-Forwarded-For` behind Railway/Render). |
| Age and consent | Online consent page shows `backend/data/consent.txt` (with `{followup_contact}` filled in) and the age question: **18 or older**, or **under 18** + guardian tick (`AGE_POLICY=18plus_or_guardian`; `18plus_only` hides the second option). Stored as `age_group`, `guardian_consent`, `consent_at`. |
| Session ownership (D-55; since D-60 the participant comes from the sign-in token, not a `code` in the request) | `POST /api/chat` (body `code`), `POST /api/sessions/{id}/end` (body `{code}`) and `GET /api/sessions/{id}/summary?code=…` check that the session belongs to that code; otherwise 404. Session ids are simple numbers, so this stops guessing. |
| Limits | `backend/ratelimit.py`: **40 messages per participant per hour, 700 per day for the whole app** (rolling 24 h); the friendly limit message includes the helplines. **Applied after the keyword safety check: a crisis message is never blocked.** |
| Locked down | `DEMO_MODE` forced off in production; `/docs`, `/redoc`, `/openapi.json` off; start-up **refuses** to run without `FOLLOWUP_CONTACT` (or with an invalid `AGE_POLICY`) and **warns** about mock mode or SQLite. |
| Researcher scripts | `create_codes.py --count N`, `safety_report.py --days N / --since DATE` (code, time, type, rule id; no message text), `delete_participant.py CODE` (asks first; `--yes` to skip), `export_data.py` (now SQLite or Postgres). |
| Docs | `docs/DEPLOYMENT.md`: Supabase, codes, OpenRouter, **Railway and Render**, env-variable table, post-deploy test, **pre-launch checklist**, running-the-study routine. |

**Automated verification (dev chat), 4 rounds:**
- **A. SQLite regression:** Phase 3 33/33, Phase 7 9/9, Phase 8 9/9, Phase 5 13/14 (the 1 is the known Phase 7 badge-name change).
- **B. Same suites on a real Postgres 16 server:** Phase 3 33/33, Phase 7 9/9, Phase 8 9/9, Phase 5 13/14; all 4 tables show RLS enabled; PHQ rows correct (incomplete = empty total); export and safety report read from Postgres.
- **C. Production safeguards on Postgres:** start-up STOP without `FOLLOWUP_CONTACT`; mock-mode warning; 3 codes created; `P001` refused (403), bad format (400, same text), no age answer (400), under 18 without guardian (403), under 18 + guardian OK, lower-case code OK; consent stored; `/docs`, `/openapi.json`, demo → 404; another participant's code on someone's session → 404 for summary and chat; with `CHAT_LIMIT_PER_HOUR=3`, messages 1–3 OK, the 4th → 429, **a crisis message after the limit still got the Safety reply with 14416 and 112**; sign-ins 1–10 → 403, the 11th → 429, another IP still allowed; safety report listed the flag; delete asked first, then removed 8 messages, 1 session, 1 participant.
- **D. Upgrade + browser:** an old SQLite file gained the 3 new columns with its data kept (and a second start-up was fine); the online consent page in Chromium 14/14 (study text, issued-code placeholder, "saved securely", age question with guardian tick, P001 refused, issued code signs in, chat, end, reflection, summary, no demo card, no page errors).
- **Not tested from the dev chat:** your real Supabase project and a real Railway/Render deployment (no access to your accounts). That's checks 2 and 8 below.
- **Bug found and fixed in the second run (D-56):** in production, `P001` could still sign in, because it already existed in the database from local testing (production only refused codes that didn't exist). Your Supabase database gets such codes too while you test locally with `DATABASE_URL` set. **Fix:** codes made by `create_codes.py` are marked `issued=1`, and production accepts **only issued codes**. Older databases get the `issued` column automatically on start-up. Re-tested: `P001` refused, a code made before the fix refused, a new issued code signs in; checks 4–7, the 14 browser checks and the SQLite regressions pass again.

**Manual checks:**

Before you start: `git pull origin claude/gracious-euler-tlrs89`, then **`pip install -r requirements.txt`** (new package `psycopg`). **Note: your `.env` already has `DATABASE_URL`, so from now on your local app writes to Supabase.** To use local SQLite instead, put `#` in front of that line.

1. **Local regression (SQLite):** put `#` in front of `DATABASE_URL` in `.env`, keep `APP_ENV=local` (or leave it out), restart. **Expect:** start-up line `env=local … db=D:\CreatED-cloud\stillspace\data\stillspace.db`; sign in as `P001`, chat, finish and summary work as before. (Your existing database gets the 3 new columns automatically.)
2. **Supabase from your laptop:** remove the `#` again (the URI should be the **Session pooler** one, ending in `?sslmode=require`), restart. **Expect:** `db=postgres (aws-0-….pooler.supabase.com)` and no error. In Supabase → **Table Editor**: `participants`, `checkins`, `sessions`, `messages`, each marked **RLS enabled**. Sign in as `P001`, chat once; the rows appear in the Table Editor.
3. **Codes + production sign-in:** run `python scripts/create_codes.py --count 3` (codes made **before** this update are not marked as issued, so create new ones), then set `APP_ENV=production` and `FOLLOWUP_CONTACT=Your Name (role), email` in `.env`, restart. **Expect:** the start-up line shows `env=production … demo_mode=False`. On the consent page: the study text and age question appear; `P001` is refused ("This participant code is not valid…"); one of the new codes signs in after answering the age question ("I am under 18" also needs the guardian tick).
4. **Chat limit:** add `CHAT_LIMIT_PER_HOUR=3`, restart, sign in with a code, send 4 normal messages. **Expect:** the 4th shows "You've reached the message limit for now…" with Retry; then send a crisis test message (e.g. S01 from `eval/safety_prompts.csv`): the **Safety response still appears**. Set the limit back to 40.
5. **Safety report:** `python scripts/safety_report.py --days 1`. **Expect:** your test flag listed with code, time, type `keyword` and the rule id, and **no message text**.
6. **Locked down:** open http://localhost:8000/docs. **Expect:** `{"detail":"Not Found"}`. The summary page has no "Preview repeat visits" card.
7. **Withdrawal + export:** `python scripts/delete_participant.py <one test code>`, type `yes`. **Expect:** "Deleted … messages, … checkins, … sessions, 1 participants". Then `python scripts/export_data.py`: "Exporting postgres (…)" and 4 CSVs.
8. **Deploy** to Railway or Render following `docs/DEPLOYMENT.md` section 4. **Expect:** the log shows `[startup] … env=production … db=postgres (…)`; the `https://` link works on your phone; a code signs in, chat (OpenRouter) and the crisis reply work; the test flag appears in the safety report.
9. **Pre-launch checklist** (`docs/DEPLOYMENT.md` section 5): every item ticked **before** the link is shared.

After testing, set `APP_ENV=local` (or remove it) and decide whether your local `.env` keeps `DATABASE_URL` (Supabase) or uses SQLite.

---

## 4. Planned module headers (spec section 13)

Every core module starts with `# mentoring.md: Session N - <topic>`. Planned mapping (finalised in Phase 10):

| File | Session |
|---|---|
| `backend/main.py`, `backend/config.py`, `backend/routes/config_route.py` | 3 – How the app talks |
| `backend/llm.py`, `backend/mock.py` | 4 – First LLM call and memory |
| `backend/safety.py` | 5 – Safety layer |
| `backend/strategy_policy.py` | 6 – Strategies and policy |
| `backend/classifier.py` | 7 – Classifier prompt |
| `scripts/eval_classifier.py` | 8 – Testing the classifier |
| `backend/prompt_builder.py`, `backend/routes/chat.py` | 9 – Prompt builder |
| `backend/checkins.py`, `backend/db.py`, `backend/routes/checkins.py`, `backend/routes/participants.py`, `scripts/export_data.py` | 11 – Check-ins and data ethics |
| `scripts/eval_responses.py` | 13 – Evaluation design |

---

## 5. Decisions log

Things the spec leaves open or gets slightly wrong. In each case I picked the simplest option. Tell me if you want any changed.

| ID | Decision | Why |
|---|---|---|
| D-01 | The venv activation command is `.\.venv\Scripts\Activate.ps1` (the spec shows `.\\venv\...`, a typo). | The spec creates the venv as `.venv`. |
| D-02 | The project gets onto D: with `git clone ... D:\CreatED-cloud\stillspace` and then checking out branch `claude/gracious-euler-tlrs89`. | The spec runs `cd D:\CreatED-cloud\stillspace` without saying how the folder is created. |
| D-03 | `$env:TMP`/`$env:TEMP` are set per terminal (as the spec shows) **before** `python -m venv`, so venv creation also uses D:. | Keeps temp files off C: during install. |
| D-04 | **Approved:** add `tzdata` to `requirements.txt` (a sixth package, about 350 KB, maintained by the Python core team). | On Windows, Python has no built-in timezone database, so `ZoneInfo("Asia/Kolkata")` crashes without it. The spec says "only" 5 packages, but `APP_TIMEZONE` can't work on Windows without this. The alternative is a hard-coded +05:30 offset, which would ignore `APP_TIMEZONE`. |
| D-05 | Empty `backend/__init__.py` and `backend/routes/__init__.py` are added. | So `uvicorn backend.main:app` and `from backend.safety import ...` work the same on every OS. |
| D-06 | Helpline data lives in `backend/config.py` as `HELPLINES` (Phase 1); `safety.py` re-uses it from Phase 5. | `/api/config` needs helplines in Phase 1, before `safety.py` exists. There is one source, so the numbers can't drift apart. |
| D-07 | Both strategy JSON files are written in full in Phase 1 (Phase 1 check 5 needs 8 strategies). Phase 6 only reviews or refines their wording. | Order of work. |
| D-08 | `app_version` = `"0.1.0"`, as a constant in `config.py`. | The spec asks for an app version but gives no value. |
| D-09 | Participant codes: letters and digits only, 3–20 characters, stored **upper-case** (so `p001` and `P001` are the same person). | Avoids duplicate participants from typing differences. |
| D-10 | One "turn" in `HISTORY_TURNS` = one message (user or assistant). The default 6 = the last 3 exchanges. | The spec doesn't define "turn". This keeps prompts short and cheap. |
| D-11 | The daily check-in is an upsert per local date: a second save the same day **merges** the new answers into today's row (so the sidebar mood doesn't wipe other daily answers). | Spec 11.6 says the sidebar mood and the daily question write the same row. |
| D-12 | "Today" = current date in `APP_TIMEZONE` + `demo_day_offset` days. Fortnightly is due when today − local_date of the last fortnightly check-in ≥ 14 days. Incomplete PHQ-9 saves still count as a fortnightly check-in. | The spec says "the last" fortnightly, without excluding incomplete ones. |
| D-13 | `chat_seconds` = `ended_at − started_at`, computed by the server in `/end`. | One source of truth, with no trust in the browser clock. |
| D-14 | Phase 4 uses `prompts/plain_system.txt` (no strategy). Phase 9 re-uses the same file as **condition A**. | All prompt text stays in `.txt` files, and condition A is exactly what "no strategy" means. |
| D-15 | Thinking is turned off by sending `extra_body={"reasoning": {"enabled": false}}` when the base URL is OpenRouter. `<think>…</think>` is always stripped as well. | Spec section 8. Other providers ignore or don't need the flag. |
| D-16 | Phase 7 check 4 uses a commented-out `# DEBUG:` print line in `routes/chat.py`, instead of a new `.env` key. | The spec says "add print or log output". No new config is needed. |
| D-17 | Export CSVs and eval CSVs are written as UTF-8 with BOM (`utf-8-sig`). | Excel on Windows otherwise garbles non-ASCII characters (e.g. Hinglish, curly quotes). |
| D-18 | The mockup is also kept as `docs/mockup/Stillspace-2.html` (unchanged). | Needed for the Phase 2 side-by-side check and the final "design matches" acceptance check. |
| D-19 | Extra checks marked "(Extra)" or "(Quick extra check)" are added to some phases. The spec's numbered checks are all kept. | Faster verification. You can skip them. |
| D-20 | The project folder is `D:\CreatED-cloud\stillspace`, not `D:\Projects\stillspace` (your choice). Caches stay in `D:\cache\...` and `D:\ollama\models`. | Still on D:. The code only uses paths relative to the project root, so nothing else changes. |
| D-21 | **Classifier = Qwen with a prompt** (your suggestion 1, and also the spec). Training a separate DistilBERT/DeBERTa classifier is a **stretch idea only**. It is documented in `docs/ARCHITECTURE.md` and as optional extension work in `mentoring.md` (Phase 10), and no code is written for it. | Spec section 3 puts training a separate classifier out of scope. The 30-row `eval/test_messages.csv` is far too small to train on. A real attempt would use the strategy-labelled ESConv dataset and reuse `scripts/eval_classifier.py` to compare. |
| D-22 | **Safety is strengthened, never weakened** (your suggestion 2). The spec already runs a deterministic keyword/regex check **before** any LLM call (the LLM is never called on a match) and the classifier's `risk` only adds a second net. Phase 5 adds: (a) text normalisation before matching (lower-case, curly→straight apostrophes, collapsed spaces, stretched letters like `dieee`→`die`, simple digit/symbol swaps like `k1ll`); (b) English, romanised Hinglish **and** Devanagari phrases; (c) `eval/safety_prompts.csv` grows from 15 to **30** synthetic, non-graphic rows (20 crisis incl. indirect, Hinglish and misspelled; 10 tricky normal ones such as "this exam is killing me"); (d) every keyword hit is logged with the matched pattern ID so false positives can be reviewed. | Extra protection, at no cost to the mock or offline modes. The fixed crisis reply with Tele-MANAS 14416 / 1-800-891-4416 and 112 is unchanged. |
| D-23 | **Model choice is still open** (your suggestion 3). The default stays `qwen/qwen3-8b` via OpenRouter (spec section 4) until you confirm availability with the command in Phase 4 check 0. The spec doesn't name a **mental-health fine-tuned** model. Community fine-tunes are usually published as weights on Hugging Face, not on OpenRouter, so the likely route is **Ollama** on the dev laptop (models on `D:\ollama\models`). If the two models are on different providers, Phase 9's `--models` will accept a provider prefix (e.g. `ollama:<model>`). This is decided when you name the model. | No model is assumed without your confirmation. Only `.env` and the `--models` argument change. |
| D-24 | `GET /status` (and the other participant/check-in responses) return a few **extra** fields beyond spec 10: `code`, `local_date`, `demo_day_offset`, and `answers` (setup answers, today's daily answers, and the current fortnight's PHQ/extra answers). | Phase 3 check 2 needs saved answers to reappear after a refresh, and the preview label needs the demo date. The spec's fields are all present and unchanged. |
| D-25 | `POST /api/checkins` returns `{"checkin": <stored row>, "status": <fresh status>}`. | The page updates its Due/Done labels from the server's answer without a second request. |
| D-26 | The consent page's primary button became "Continue →" (routes by status); "Skip to chat →" stays. | Spec 12 asks for routing on continue; the mockup keeps check-ins optional. |
| D-27 | A refresh signs the person back in and routes by status, instead of returning to the exact screen they were on. | Simplest reliable behaviour; nothing is lost because answers are stored. |
| D-28 | Pressing a daily Finish button always stores a row, even with every question skipped. Picking a sidebar mood also stores today's daily row, so daily becomes "Done". | Mockup: "completion is an explicit action". Spec 11.6: the sidebar mood and the daily question write the same check-in. |
| D-29 | Saving "Requested by you" (PATCH) is wired now rather than in Phase 7. Phase 7 check 3 still tests it. | It shares code with the setup preference built in this phase. |
| D-30 | The PHQ item-9 rule lives in `checkins.score_phq9()` for now. Phase 5 moves it into `safety.phq_item9_flag()` as planned, without changing behaviour. | Phase 3 needs it before `safety.py` exists. |
| D-31 | `python -c "..."` one-liners in this file only use **single quotes** inside. Values go in as `?` parameters. | Windows PowerShell 5.1 removes embedded `\"` quotes before passing them to Python, which caused a `SyntaxError` in Phase 3 check 3. This will be noted in docs/TROUBLESHOOTING.md (Phase 10). |
| D-32 | LLM **errors** → HTTP 502 + friendly message + Retry, nothing stored. **Empty** output → fallback reply (`source="fallback"`). | Spec 5 step 8 says "on error or empty output, return a gentle fallback message", but Phase 4 check 3 expects a friendly error with Retry on a wrong key. Retry is more useful for errors; the fallback covers empty replies. Safety replies (Phase 5) happen before the LLM call, so this never affects them. |
| D-33 | For Qwen3 models, `llm.py` adds `/no_think` to the end of the system message, besides OpenRouter's `reasoning.enabled=false`. | Qwen3's documented switch, which works on any provider, including Ollama. It saves tokens and latency. |
| D-34 | Until Phase 7 the reply badge shows the source ("Mock reply" / "AI reply" / "Fallback reply"). | There is no strategy yet; the badge still tells you which path answered. |
| D-35 | The "Mock mode" tag sits in the header tools, so it is visible on every step. | Spec 11.7 asks for a small tag; the header is always visible, also on mobile. |
| D-36 | New `.env` key **`LLM_TIMEOUT_SECONDS`** (default 120; it was a fixed 30 s in `llm.py`). | A local model on a laptop CPU (Ollama) can need more than 30 s, especially for the first reply while it loads. |
| D-37 | **Zero-cost model route (your requirement, 4 Nov 2026): Ollama on the dev laptop.** App installed with `/DIR=D:\ollama\app`, models in `D:\ollama\models` (Phase 1 `OLLAMA_MODELS`). `.env`: `LLM_BASE_URL=http://localhost:11434/v1`, `LLM_API_KEY=ollama` (any non-empty text, because empty = mock mode), `LLM_MODEL=qwen3:8b` (the spec's model) or `qwen3:4b` on low-RAM laptops. OpenRouter stays documented as the paid option. | No API costs, and chat text never leaves the laptop (better for DPDP). Same OpenAI-compatible code path, so only `.env` changes. The fine-tuned comparison model (D-23) can run the same way. |
| D-38 | **Two model setups, same code.** Dev/testing (you): Ollama `qwen3:8b`, free (D-37). **Handoff (student and mentor): OpenRouter with credits**, default `LLM_MODEL=qwen/qwen3-14b` in `.env.example` and `config.py`. `docs/SETUP.md` (Phase 10) will default to OpenRouter with a spending limit and mention Ollama as a free alternative. For the Phase 9 evaluation the student uses one model consistently and names it in the report. | Spec 2 and 15: hosted API, no GPU needed on the student's laptop. `qwen/qwen3-8b` is gone from OpenRouter; `qwen3-14b` is the same family, cheap (about $0.12 / $0.24 per 1M tokens), and its thinking can be switched off. |
| D-39 | **Thinking control, tested on your Ollama 0.40.14 (4 Nov 2026).** `ollama run --think=false` and the `/no_think` text were ignored by the `qwen3:4b` tag. Over the API, `think: false` moved the thinking into a separate `reasoning` field (reply clean, but still slow and token-hungry). `reasoning_effort: "none"` put the thinking **into** the reply, ending in `</think>` with no opening tag. **So:** (a) `llm.py` sends `{"think": false}` to Ollama URLs (`11434`/`ollama`), `{"reasoning": {"enabled": false}}` to OpenRouter, and nothing to other providers; (b) `strip_thinking()` also removes text before a lone `</think>`; (c) use a Qwen3 **instruct** tag on Ollama (`qwen3:4b-instruct-2507-q4_K_M`), because the plain `qwen3:4b` tag is an always-thinking build. | Prevents thinking text from reaching a user with any model, and avoids empty "Fallback reply" answers caused by thinking using up the 300-token limit. |
| D-40 | Safety details: (a) normalisation as described in Phase 5 (apostrophes removed; look-alike digits swapped inside words only; `!` never swapped; separators between letters removed; stretched letters checked both ways); (b) Devanagari phrases match as plain text; (c) the crisis user message is stored with `used_strategy="Safety"` and the matched rule id in `meta_json`; (d) the PHQ item-9 notice now shows the helplines and the follow-up contact; (e) the session safety flag resets on New session or refresh. | (a)–(b) catch common spelling tricks without false negatives; (c) makes false alarms reviewable; (d) spec 11.5 / section 4 table; (e) spec 11.5 says "in this session". |
| D-41 | Classifier details: the whole prompt goes as one **user** message; placeholders are filled with `.replace()`; temperature 0, max 200 tokens; one retry, then the spec's defaults; risk values other than none/low/high → **high**; strategy names matched case-insensitively (unknown → first in the file); history shown as `User:` / `Stillspace:` lines; `eval_classifier.py` adds the project folder to `sys.path` so `python scripts/eval_classifier.py` works; the test set is labelled for strategies_4 (the script warns otherwise); mock rules map to the closest ESConv-8 name. Wired into the chat in Phase 7. | Robust JSON from small models; safety-first on unclear risk; works with the exact command in the spec. |
| D-42 | The classifier prompt and strategy descriptions are **not** tuned after the first real run (90%), and the self-reported `confidence` is not used for decisions. | Tuning on the 30 test messages would overfit them (the score would stop meaning anything). The 3 Reassurance misses are kept as a ready-made student exercise (Session 8). Confidence was 0.95+ even when wrong. |
| D-43 | `/no_think` is added only for **hybrid** Qwen3 models (name contains `qwen3` but not `instruct` or `thinking`): on the system message if there is one, otherwise on the last message. **Dev model stays `qwen3:4b-instruct-2507-q4_K_M` for classifier and replies.** | The `qwen3:8b` comparison failed: it thought until the 200-token limit (cut-off JSON → fallback) and took 35–51 s per message on the 6 GB GPU. The classifier sends one user message, so the old system-only switch never reached it. The handoff model `qwen/qwen3-14b` is hybrid too. |
| D-44 | Phase 7 pipeline details: the classifier gets the same history as the reply; `meta_json` = classifier meta + `classifier_source` + `classifier_ms`; `latency_ms` = total wait; check-in context = today's mood + latest **complete** PHQ band only; a classifier `risk: high` gives the fixed reply with `safety_flag="classifier"` and keeps the classifier's strategy in `classified_strategy`; the panel explains when a request overrode the classifier; fallback replies keep the "Fallback reply" badge; new keyword rule `en-sleep-never-wake`. | Spec 5, 10, 11.2, 11.4 and 12; honest badges (a fallback text was not shaped by any strategy); the extra keyword rule closes a gap found while testing. |
| D-45 | Phase 7 check 5 is run with **a new session before each strategy**. No code change. | In your first run the identical message sent 4× in one conversation made the 4B model copy its previous reply for Reflection: history outweighed the new strategy instruction. That's a test-design issue (real users rarely repeat the exact message), but worth knowing for the Phase 9 evaluation: compare strategies on independent conversations. |
| D-46 | **Deployment added as Phase 11** (Supabase + online safety), built **after Phase 9 and before Phase 10**, so the final docs, `student_starter/` and `mentoring.md` describe the finished code. The local SQLite setup stays the default for the student course. | Your plan to deploy and share the app (4 Nov 2026). Keeps the spec's local prototype and offline teaching intact. |
| D-47 | **Supabase Postgres** when `DATABASE_URL` is set; adds the package `psycopg[binary]` (a second deviation from the spec's package list, after `tzdata`). RLS on, with no policies, so Supabase's public Data API can't read the tables. | Hosts wipe local files on redeploy, so SQLite can't hold data online. Supabase was chosen over Neon for its dashboard, regions and room to add real logins later. RLS closes Supabase's public-API exposure. |
| D-48 | **Online access = researcher-issued random codes only** (no passwords or email, in line with spec section 3), with sign-in attempts slowed after failures. | Guessable codes like `P001` would let anyone read another participant's status (incl. date of birth) online (K-08). |
| D-49 | **Rate limits in memory**: **40 messages per participant per hour, 700 per day in total** (your numbers), 10 sign-ins per IP per minute; **the safety reply is never limited**. | Protects the OpenRouter budget and blocks abuse without a new framework. |
| D-50 | **Hosting: Railway or Render** (both documented, no Docker). **Ages: 18+ and under-18 with guardian consent** (your choice): an age question at consent; under-18 needs an extra guardian-consent tick; stored as `age_group`, `guardian_consent`, `consent_at`; signed guardian forms are collected outside the app (checklist). | Spec section 16 requires guardian consent for under-18s; a tick only records the confirmation, the real consent is the signed form. |
| D-51 | **No safety alert channel** (your choice). Instead `scripts/safety_report.py` (code, time and flag type; no message text) plus a required written review routine in the deployment checklist. | Simpler and no third-party chat service; the trade-off is slower follow-up, so the review routine must be agreed before launch. The participant still gets the helplines instantly. |
| D-52 | Session endpoints in a new `routes/sessions.py`; `chat_seconds` = chat opened → Finish (server clock, may include pauses; updated if finished again); summary bars = share of replies; summary shows the **latest saved PHQ-9** from the server; "View summary" saves the reflection (even with skipped answers, like D-28), "Skip for now" saves nothing; exports overwrite. | Keeps `chat.py` near ~150 lines; one server-side source of truth for the summary (spec 12); consistent "completion is explicit" rule. |
| D-53 | `eval_responses.py` design: no history and no check-in context in either condition; the same model does classifier and reply in B; keyword safety in both; `strategy_to_check` = the expected strategy for all rows; **a shuffled blind rating sheet** (no condition/model/strategy) alongside the full file, linked by `item_id`, with a fixed seed; `--summarise` merges ratings back; the `ollama:` prefix for local models; errors become visible rows. | The fairest simple comparison (only the strategy layer differs), and blind rating avoids rater bias, which a student report can defend. Extra models can be added any time with `--models`. |
| D-54 | Phase 11 implementation details: connection code split into `backend/db_connect.py` (keeps `db.py` short); schemas moved to `backend/data/schema_*.sql`; participant codes may contain hyphens (issued format `SS-XXXX-XXXX`, alphabet without 0/O/1/I/L); sign-in limit uses the first `X-Forwarded-For` address; daily limit is a rolling 24 hours; production start-up **stops** on missing `FOLLOWUP_CONTACT` or invalid `AGE_POLICY`, **warns** on mock mode or SQLite (so production mode can be tested on a laptop). | Short, readable files; correct behaviour behind Railway/Render's proxy; safe defaults that still allow local testing. |
| D-55 | **Session endpoints check ownership:** `POST /api/chat` now needs `code` in the body, `POST /api/sessions/{id}/end` needs `{code}`, `GET /api/sessions/{id}/summary` needs `?code=`. A session that doesn't belong to the code gives 404. Applies locally too. | Session ids are 1, 2, 3…; without this, anyone online could read or use another person's session. A small change to the spec's API contract (section 10). |
| D-56 | **Production accepts only issued codes**: new column `participants.issued` (1 = made by `create_codes.py`); `P001`-style codes created during local testing stay in the database but are refused online. Added to both schemas (Postgres via `ADD COLUMN IF NOT EXISTS`, SQLite via the start-up upgrade). | Found in the second Phase 11 test run: local testing with `DATABASE_URL` set writes guessable codes into the same Supabase database. |
| D-57 | **Student starter design:** stubs for the 5 spec functions **plus** `parse_classifier_output()`, `build_system_prompt()` and a classifier-prompt skeleton (Session 7 is "write the classifier prompt and JSON parsing"); `build_messages()` has a Session 4 TODO (history = memory) and a Session 9 TODO (strategy prompt); helper functions stay written so each session fits one hour; `choose_strategy()` keeps the `"Safety"` line; `check_message()` stays fully working; placeholders print `[TODO Session N]`; the starter runs on port 8001 with its own `.gitignore` (so its database is never committed). **`flow.md` added** at your request. | Matches the 16-session map; safety never missing (spec 15); student and finished app can run side by side. |
| D-58 | **Spaced-letter safety rule:** `normalise()` joins three or more single letters separated by spaces (`d i e`, `k i l l`). Added to the finished app and the starter. | Found while writing Session 5: "I want to d i e" was not caught. It strengthens the check only; the 30-row test still passes and ordinary text like "Plan A B C" is unaffected. Used as a teaching story. |
| D-59 | **The student gets only `student_starter/` (as a zip), with its own copies of SETUP, SAFETY, TROUBLESHOOTING and ARCHITECTURE in `student_starter/docs/`.** | The repo holds the finished app (the answer key) next to the starter; a zip keeps the answers out of reach, and the docs travel with it. |
| D-60 | **Sign-in tokens for user isolation** (your decision, 4 Nov 2026). The code is sent once to `POST /api/participants`, which returns a random token (`secrets.token_urlsafe(32)`). Every other endpoint reads `Authorization: Bearer <token>` and takes the participant **from the token** (`backend/auth.py` → `require_participant`). Code-in-URL routes replaced: `GET /api/me/status`, `PATCH /api/me`; `code` removed from the chat, check-in, session and demo bodies; new `POST /api/logout`. Tokens expire after `SIGN_IN_HOURS` (12), are deleted on sign-out and withdrawal, and are stored only as SHA-256 hashes (new table `auth_tokens`, RLS on). Logs show `participant #id`, not codes. **Safety exception:** a crisis message with an expired token still gets the fixed reply (not stored). Same change in `student_starter/`. | Before, the code was the credential on every request: it appeared in URLs and logs, and only sign-in was rate-limited, so other endpoints could be used to try codes. A server-issued, expiring session token is standard practice (OWASP session management) and a reasonable safeguard under the DPDP Act 2023. Verified: 30-check isolation test on SQLite, Postgres and the starter; production mode; earlier UI suites (33/33, 9/9). Deviation from the spec's API contract (section 10), which had the code in paths and bodies. |
| D-61 | **Online access stays invite-only** (issued codes, no public sign-up), now explained in `docs/DEPLOYMENT.md` §2, `handoff.md`, `README.md`, `flow.md`, with the full code process (create, allocate privately, hand out, lost code, withdrawal) and what a public version would need. | Developer asked why everyone can't use it. It is a supervised study: consent and guardian consent first, follow-up on safety flags, withdrawal, ethics approval and cost control all need known participants. Laptop testing uses `APP_ENV=local`. |

---

## 6. Known issues

| ID | Issue | Impact / plan |
|---|---|---|
| K-01 | ~~`Stillspace-2.html` was not in the repository.~~ | **Resolved:** you attached it, and it is now committed as `docs/mockup/Stillspace-2.html` (unchanged). |
| K-02 | **Happened (Phase 4 check 0, 4 Nov 2026):** `qwen/qwen3-8b` is no longer listed on OpenRouter. The nearest paid options are `qwen/qwen3-14b` ($0.12 / $0.24 per 1M tokens) and `qwen/qwen3.5-9b`. | The handoff default is now `qwen/qwen3-14b` (D-38). The dev laptop uses local Ollama `qwen3:8b` (D-37). Re-run Phase 4 check 0 just before handoff. |
| K-03 | The keyword check can't catch every indirect phrasing, and can flag harmless text. **Known false positive:** "I love the movie suicide squad" (rule `en-suicide`), kept on purpose, because a false alarm is safer than a missed crisis. Figures of speech in the test set ("killing me", "dying to", "dead tired") are **not** flagged. | Backed by the classifier's `risk` check (Phase 7). Add more false positives or negatives here as you find them. |
| K-04 | The comparison model (mental-health fine-tuned) has not been chosen yet (D-23). | Needed before Phase 9. Phases 2–8 don't depend on it. |
| K-05 | ~~Chat answers came from placeholders in `app.js`.~~ | **Resolved in Phase 4:** replies come from `/api/chat` (mock or LLM) and are stored. |
| K-06 | A mood or style chosen on the consent page **before** signing in is not saved: after sign-in the page shows what the server has stored. | Minor. Choose them after signing in. |
| K-07 | A page refresh starts a new chat session, so the conversation disappears from the screen and the summary counts only the current session. All messages are still stored in the database. | Acceptable for the prototype (D-27). Could restore the last session's messages later if wanted. |
| K-08 | ~~Guessable codes, open demo endpoints and `/docs` online.~~ | **Resolved in Phase 11:** production accepts only issued random codes, session endpoints check ownership (D-55), and demo and `/docs` are off. Still: don't share the link before the `docs/DEPLOYMENT.md` checklist is complete. |
| K-09 | Rate limits live in memory: they reset when the app restarts and are counted per server process. | Fine for one small Railway/Render instance (D-49). A shared store would be needed if you ever run several instances. |
| K-10 | ~~Your Supabase project was in **Tokyo** (`ap-northeast-1`), not Mumbai.~~ | **Resolved (4 Nov 2026):** you moved `DATABASE_URL` to a new project in **Mumbai** (`aws-0-ap-south-1`); tables and RLS were created on first start, `create_codes.py` and `safety_report.py` work there. Still to do: delete the old Tokyo project (or keep it test-only), name Mumbai as the storage location in `consent.txt`, and treat the 3 codes shown in the dev chat as test codes (remove them with `delete_participant.py` and issue fresh ones before the study). |
| K-11 | The beginner setup (`docs/SETUP.md`) was verified on Linux in the dev chat, not on a Windows laptop. | The mentor follows `docs/SETUP.md` once on Windows (or with the student in session 2, using `docs/TROUBLESHOOTING.md`). |
| K-12 | The participant code is still the only secret needed to sign in (no password or PIN, by spec design). Anyone who learns a code can sign in as that person. | Hand codes out privately; tokens protect everything after sign-in (D-60). A PIN could be added later if the ethics board asks for it. |
