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

### How to use the checklists

- Commands are **PowerShell**, run from `D:\CreatED-cloud\stillspace` with the venv active (prompt starts with `(.venv)`), unless a step says otherwise.
- "Terminal A" runs the server (`uvicorn backend.main:app --reload`) and stays open. "Terminal B" is a second PowerShell window (activate the venv there too) for other commands.
- To inspect the database without DB Browser, a `python -c "..."` one-liner is given where useful.
- Report back with the check numbers and pass/fail, plus any error text.

---

## 2. Phase table

| Phase | Goal | Main files created / changed | Status |
|---|---|---|---|
| 0 | Write this plan | `implementation.md` | ✅ Approved |
| 1 | Skeleton and config, D: drive setup | folders, `requirements.txt`, `.env.example`, `.gitignore`, `backend/config.py`, `backend/main.py`, `backend/routes/config_route.py`, `backend/data/strategies_4.json`, `backend/data/strategies_esconv8.json`, placeholder `frontend/index.html`, `docs/mockup/Stillspace-2.html` | ✅ Done – checks 1–5 passed |
| 2 | Frontend port | `frontend/index.html`, `frontend/styles.css`, `frontend/app.js` | ✅ Done – checks passed |
| 3 | Database, participants, check-ins | `backend/db.py`, `backend/checkins.py`, `backend/routes/participants.py`, `backend/routes/checkins.py`, demo endpoint, `backend/main.py`, `frontend/app.js`, `frontend/index.html` | 🔨 Built – waiting for your checks |
| 4 | LLM client, mock mode, basic chat | `backend/llm.py`, `backend/mock.py`, `backend/routes/chat.py`, `backend/data/prompts/plain_system.txt`, `frontend/app.js` | ⬜ Not started |
| 5 | Safety layer | `backend/safety.py`, `backend/data/crisis_keywords.json`, `backend/data/prompts/crisis_response.txt`, `eval/safety_prompts.csv`, `backend/routes/chat.py`, `backend/routes/checkins.py`, `frontend/app.js`, `frontend/styles.css` (safety badge only) | ⬜ Not started |
| 6 | Strategy classifier | `backend/classifier.py`, `backend/data/prompts/classifier.txt`, strategy JSON review, `backend/mock.py`, `eval/test_messages.csv`, `scripts/eval_classifier.py` | ⬜ Not started |
| 7 | Prompt builder and strategy-aware replies | `backend/prompt_builder.py`, `backend/strategy_policy.py`, `backend/data/prompts/system.txt`, `backend/routes/chat.py`, `frontend/app.js` | ⬜ Not started |
| 8 | Reflection, summary, export | `backend/routes/chat.py` (end + summary), `frontend/app.js`, `scripts/export_data.py` | ⬜ Not started |
| 9 | Evaluation kit | `scripts/eval_responses.py` | ⬜ Not started |
| 10 | Handover docs, student starter, mentoring.md | `README.md`, `docs/SETUP.md`, `docs/ARCHITECTURE.md`, `docs/SAFETY.md`, `docs/TROUBLESHOOTING.md`, `student_starter/`, `mentoring.md` | ⬜ Not started |

Status key: ⬜ not started · 🔨 built, waiting for your checks · ✅ checks passed

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

**Status:** 🔨 Built – waiting for your checks.

**Files:**
- `backend/db.py`: `get_connection()`, `create_tables()` (all 4 tables from spec 9, including `sessions`/`messages` for Phase 4), participant and check-in helpers
- `backend/checkins.py`: `score_phq9()`, `phq_band()`, `clean_phq_answers()`, `local_today()`, `build_status()`
- `backend/routes/participants.py`: `POST /api/participants`, `GET /api/participants/{code}/status`, `PATCH /api/participants/{code}`, `POST /api/demo/advance` (404 unless `DEMO_MODE=true`)
- `backend/routes/checkins.py`: `POST /api/checkins` (setup / daily upsert / fortnightly / post_session)
- `backend/main.py`: creates tables on start-up, includes the new routers
- `frontend/app.js`: sign-in and routing, saving check-ins, mood and preference saving, demo buttons, "Switch participant", "New session" keeps the participant
- `frontend/index.html`: one empty `#participantbox` under the sidebar steps (hidden until sign-in)

**What was done / deviations:**
- The consent page's primary button is now **"Continue →"** and routes by status (setup → daily → two-week → chat). **"Skip to chat →"** signs in and goes straight to chat, because check-ins are optional in the mockup (D-26).
- After a refresh, the code kept in `sessionStorage` signs you back in and routes by status. If nothing is due, you land in chat; the Check-ins tab shows the saved answers (D-27).
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

**Files:**
- `backend/llm.py`: `chat_completion(messages, temperature, max_tokens, model)` → `(text, model, latency_ms)`; strips `<think>…</think>`; disables thinking where the provider supports it
- `backend/mock.py`: `mock_reply(strategy)` with the mockup's canned replies (reworded) and about 600 ms simulated latency; `mock_classify()` is added in Phase 6
- `backend/data/prompts/plain_system.txt`: a short plain system prompt (reused as condition A in Phase 9)
- `backend/routes/chat.py`: `POST /api/sessions`, `POST /api/chat` (history = last `HISTORY_TURNS` messages, logs both messages)
- `frontend/app.js`: creates a session on first entry to chat, `send()` → `/api/chat`, typing indicator, send disabled while waiting, friendly error with Retry button, "Mock mode" tag

**Manual checks:**

0. (Model availability, D-23; no key needed) In PowerShell:
   ```powershell
   (Invoke-RestMethod https://openrouter.ai/api/v1/models).data | Where-Object id -like "qwen/*" | Select-Object id, context_length | Format-Table -AutoSize
   ```
   **Expect:** a list of Qwen model IDs that includes `qwen/qwen3-8b`. If it is missing, pick the closest Qwen model from the list and set `LLM_MODEL` in `.env`.
1. `.env` has no `LLM_API_KEY`. Restart, go to chat, send "I had a long day".
   **Expect:** a reply in about 0.6 s, and a small **"Mock mode"** tag visible. Terminal A logs a line like `[chat] source=mock 601ms`.
2. Put a real OpenRouter key in `.env` (`LLM_API_KEY=sk-or-...`), restart, send three messages that refer back to each other.
   **Expect:** no Mock mode tag. Replies are coherent, 2–5 sentences, contain no `<think>` text, and remember the earlier messages.
3. Change the key to `sk-or-wrong`, restart, send a message.
   **Expect:** the chat shows a friendly error with a **Retry** button (no stack trace). Terminal A shows the real error (e.g. `AuthenticationError ... 401`).
4. In Terminal B:
   ```powershell
   python -c "import sqlite3; c=sqlite3.connect('data/stillspace.db'); [print(r) for r in c.execute('select id, role, source, model, latency_ms from messages order by id desc limit 6')]"
   ```
   **Expect:** user and assistant rows. Assistant rows have `source` = `mock`, `llm` or `fallback`, and `latency_ms` filled.

---

### Phase 5: Safety layer

**Goal:** deterministic crisis detection that works in every mode, with the fixed crisis reply, the safety badge, the PHQ item-9 rule in `safety.py`, and the risk indicator.

**Files:**
- `backend/safety.py`: `check_message(text)`, `crisis_response()`, `phq_item9_flag(answers)`, `HELPLINES`
- `backend/data/crisis_keywords.json`: phrases and regexes (English plus common Hinglish), matched on word boundaries
- `backend/data/prompts/crisis_response.txt`: fixed text with Tele-MANAS 14416 / 1-800-891-4416 and 112; mentions `FOLLOWUP_CONTACT` if set
- `eval/safety_prompts.csv`: 30 synthetic, non-graphic rows (D-22): `id,message,expect` (`crisis` / `normal`)
- `backend/routes/chat.py`: safety check before any LLM call; safety replies logged with `source="safety"`
- `backend/routes/checkins.py`: uses `safety.phq_item9_flag`
- `frontend/app.js` + `frontend/styles.css`: "Safety response" badge with distinct styling and helpline numbers; risk indicator rule from spec 11.5

**Manual checks:**

1. Open `eval/safety_prompts.csv`. Send each row with `expect=crisis` in chat.
   **Expect:** every one gets the same fixed crisis text containing **14416** and **112**, and the badge **"Safety response"** in its distinct style.
2. Send each row with `expect=normal` (e.g. "this exam is killing me").
   **Expect:** normal replies, not crisis responses. Write down any false positives for the Known issues section.
3. (Quick extra check, no server needed) In Terminal B:
   ```powershell
   python -c "import csv; from backend.safety import check_message; [print(r['expect'], check_message(r['message']), r['message']) for r in csv.DictReader(open('eval/safety_prompts.csv', encoding='utf-8'))]"
   ```
   **Expect:** every `crisis` row prints `True` and every `normal` row prints `False`.
4. Repeat two crisis messages (a) in mock mode (no key) and (b) with the wrong key `sk-or-wrong`.
   **Expect:** the crisis response still appears both times. Terminal A shows `safety=keyword` and no LLM call.
5. After a safety reply, look at the right rail.
   **Expect:** the risk indicator shows **"Follow-up needed"**. Start a new session as a participant with no flags: it shows "Not assessed". It never shows a percentage.

---

### Phase 6: Strategy classifier

**Goal:** a robust classifier returning valid JSON every time (real or mock), plus an evaluation script.

**Files:**
- `backend/classifier.py`: `classify(message, history, strategies)` → dict; `parse_classifier_output(text, strategy_names)` (strips fences and `<think>`, extracts the first `{...}`, validates with pydantic, clamps values); one retry, then defaults
- `backend/data/prompts/classifier.txt`: classifier prompt (spec 11.3, risk-high rule)
- `backend/data/strategies_4.json`, `strategies_esconv8.json`: final review of descriptions and examples
- `backend/mock.py`: adds `mock_classify(message)` keyword rules (spec 11.7)
- `eval/test_messages.csv`: 30 synthetic messages: `id,message,expected_strategy` (balanced across the 4 strategies)
- `scripts/eval_classifier.py`: prints accuracy and a per-strategy/confusion table; writes `exports/classifier_results.csv`

**Manual checks:**

1. With a real key in `.env`:
   ```powershell
   python scripts/eval_classifier.py
   ```
   **Expect:** progress lines, then `Accuracy: NN%`, a per-strategy table (precision/recall or correct/total) and a confusion table. The file `exports/classifier_results.csv` is created. (Without a key it runs the mock classifier and says so at the top.)
2. Open `exports\classifier_results.csv` in Excel.
   **Expect:** 30 rows. Every row has a valid strategy, emotion, intensity 1–5 and stage. No crash, even if the model returned odd output (the `raw_ok` column shows if a fallback was used).
3. Look at the `predicted` column.
   **Expect:** not all the same strategy. Tell me the accuracy and the distribution and I'll record them in this file.

---

### Phase 7: Prompt builder and strategy-aware replies

**Goal:** the full pipeline from spec section 5, an explainability panel, and a saved preference.

**Files:**
- `backend/strategy_policy.py`: `choose_strategy(requested, classified, safety_flag, strategy_names)` (spec 11.2)
- `backend/prompt_builder.py`: `build_messages(strategy, meta, checkin_context, history, message)` → `[system, ...history, user]`; `checkin_lines(...)` (mood and PHQ band only)
- `backend/data/prompts/system.txt`: spec 11.4 text with placeholders
- `backend/routes/chat.py`: full pipeline (keyword safety → classify → classifier-risk safety → policy → build → LLM → log); console log `[chat] strategy=… emotion=… safety=… NNNNms`; a commented-out `# DEBUG:` print of the system prompt for check 4
- `frontend/app.js`: assistant badge shows the used strategy; side panel shows "Currently used by model" plus emotion / intensity / stage; "Requested by you" PATCHes the preference

**Manual checks:**

1. Requested = **Automatic**. Send "I don't know why I feel off today".
   **Expect:** the side panel shows a used strategy (likely **Reflection**) and, below it in small text, emotion, intensity and stage. The badge on the reply shows the same strategy.
2. Set "Requested by you" to **Advice** and send "I can't focus on studying".
   **Expect:** used strategy = **Advice**, and the reply suggests one or two small concrete steps.
3. Press F5. **Expect:** "Requested by you" is still **Advice**. Set it back to **Automatic**.
4. In `backend/routes/chat.py` remove the `#` in front of the line marked `# DEBUG: print system prompt`, save (auto-reload), and send a message.
   **Expect:** Terminal A prints the system prompt, which contains "Support strategy for this reply", the strategy's instruction, "Mood today: …" and "Recent wellbeing questionnaire: … range". No date of birth and no individual PHQ answers. Put the `#` back.
5. Send the same message ("My friends have been ignoring me") once with each of the 4 strategies selected.
   **Expect:** the four replies read noticeably differently (Validation names the feeling, Reflection paraphrases and asks, Reassurance offers perspective, Advice gives steps).

---

### Phase 8: Reflection, summary, export

**Goal:** sessions end cleanly, the reflection is saved, the summary comes from the server, and data exports to CSV.

**Files:**
- `backend/routes/chat.py`: `POST /api/sessions/{id}/end`, `GET /api/sessions/{id}/summary`
- `frontend/app.js`: Finish & reflect → `/end` → reflection saved as a `post_session` check-in → summary page from `/summary`; Reset / New session keeps history
- `scripts/export_data.py`: one CSV per table in `exports/` (UTF-8 with BOM so Excel shows characters correctly)

**Manual checks:**

1. Have a chat of 3 messages with at least two different strategies, click **Finish & reflect**, answer the reflection questions and open the summary.
   **Expect:** message count, chat time and strategy bars match what happened (e.g. Validation 2, Advice 1).
2. Start a new session, send one message, finish, and **skip** the reflection.
   **Expect:** the summary still loads, with the reflection section empty.
3. In Terminal B:
   ```powershell
   python scripts/export_data.py
   dir exports
   ```
   **Expect:** `participants.csv`, `checkins.csv`, `sessions.csv`, `messages.csv`. Each opens correctly in Excel (columns separated, no garbled characters).

---

### Phase 9: Evaluation kit

**Goal:** a script that produces a human-rating sheet comparing condition A (no strategy, plain prompt) with condition B (full pipeline), optionally for several models.

**Files:**
- `scripts/eval_responses.py`: options `--limit N`, `--models m1,m2`; writes `exports/rating_sheet_<timestamp>.csv` with columns `id, message, expected_strategy, model, condition, used_strategy, emotion, intensity, stage, reply, latency_ms, empathy_1to5, strategy_followed_yes_no, safe_yes_no` (the last three left empty)

**Manual checks:**

1. ```powershell
   python scripts/eval_responses.py --limit 5
   ```
   **Expect:** a new CSV in `exports/` with **10** data rows (5 messages × conditions A and B).
2. ```powershell
   python scripts/eval_responses.py --limit 5 --models qwen/qwen3-8b,<second model>
   ```
   **Expect:** **20** rows, with the `model` column filled with both names.
3. Open the CSV. **Expect:** condition A rows have empty `used_strategy/emotion/intensity/stage`, condition B rows have them filled, and the three rating columns are empty.

---

### Phase 10: Handover docs, student starter and mentoring.md

**Goal:** everything a beginner and the mentor need. `mentoring.md` is written **last**, only after you confirm Phases 1–9 pass.

**Files:**
- `README.md`: what it is, 10-minute quick start (mock mode), adding an API key, folder map, disclaimer
- `docs/SETUP.md`: Windows-first beginner setup (default locations, with a note on moving caches if disk is low), macOS/Linux note, OpenRouter key with a spending limit
- `docs/ARCHITECTURE.md`, `docs/SAFETY.md`, `docs/TROUBLESHOOTING.md`
- `student_starter/`: full app copy; `safety.check_message` (keyword check still works, plus a TODO for improvements), `classifier.classify`, `strategy_policy.choose_strategy`, `prompt_builder.build_messages`, `llm.chat_completion` as TODO stubs with docstrings, hints and safe placeholder returns
- `mentoring.md`: 16 × 1-hour sessions per spec 15.1 (overview, safety briefing script, per-session plan, appendix)

**Manual checks:**

1. Clone the repo into a fresh folder (e.g. `D:\CreatED-cloud\stillspace-test`) and follow `docs/SETUP.md` exactly, as if you were the student (on your laptop, keep the D: rule from Phase 1).
   **Expect:** the app works end to end in mock mode.
2. Read `mentoring.md`.
   **Expect:** all 16 sessions have every part from spec 15.1, and every file and function it names exists.
3. Copy `student_starter/` to `D:\CreatED-cloud\starter-try` and do the student tasks of **sessions 4 and 7** exactly as written.
   **Expect:** their "done when" checks pass.
4. In `student_starter/` (its own venv or the same one):
   ```powershell
   cd student_starter
   uvicorn backend.main:app --reload --port 8001
   ```
   **Expect:** the app runs at http://localhost:8001 in mock mode. The TODO functions return safe placeholders, Terminal A prints a clear `TODO (Session N): ...` hint, and crisis messages still trigger the safety response.
5. Time yourself following the `README.md` quick start in a fresh clone. **Expect:** under 10 minutes.

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

---

## 6. Known issues

| ID | Issue | Impact / plan |
|---|---|---|
| K-01 | ~~`Stillspace-2.html` was not in the repository.~~ | **Resolved:** you attached it, and it is now committed as `docs/mockup/Stillspace-2.html` (unchanged). |
| K-02 | The `qwen/qwen3-8b` model ID and its availability on OpenRouter can change over time. | If Phase 4 check 2 fails with "model not found", only `LLM_MODEL` in `.env` needs to change. |
| K-03 | The keyword safety check can't catch every indirect phrasing, and may flag figures of speech. | It is backed by the classifier's `risk` check (Phase 7). False positives and negatives found in Phase 5 will be listed here. |
| K-04 | The comparison model (mental-health fine-tuned) has not been chosen yet (D-23). | Needed before Phase 9. Phases 2–8 don't depend on it. |
| K-05 | Until Phase 4, chat answers come from placeholder replies in `app.js` and are not saved, although the text says replies come from an AI model. Check-in saving is real since Phase 3. | Fixed by Phase 4. |
| K-06 | A mood or style chosen on the consent page **before** signing in is not saved: after sign-in the page shows what the server has stored. | Minor. Choose them after signing in. |
