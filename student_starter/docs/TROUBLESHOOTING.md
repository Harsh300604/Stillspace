# Troubleshooting

> Find the message you see (Ctrl+F), then follow the fix. Most problems during the build were **Windows/PowerShell** problems, not code problems. When asking for help, paste the **error line**, never your API key or database connection string.

---

## Starting up

| You see | Why | Fix |
|---|---|---|
| `python` opens the Microsoft Store, or `'python' is not recognized` | Python isn't on PATH | Reinstall Python and tick **"Add python.exe to PATH"** on the first screen. Open a new terminal. |
| `running scripts is disabled on this system` when activating | PowerShell blocks scripts by default | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, answer `Y`, activate again. |
| The prompt doesn't start with `(.venv)` / `No module named 'fastapi'` / `'uvicorn' is not recognized` | The venv isn't active in this terminal | `.\.venv\Scripts\Activate.ps1` (macOS/Linux: `source .venv/bin/activate`). Needed in **every** new terminal. |
| `pip list` shows only `pip` and `setuptools` | `pip install` never ran (or failed) | `pip install -r requirements.txt` and check the last line says `Successfully installed`. |
| `Read timed out` / `ReadTimeoutError` during `pip install` | Slow or unstable internet | `pip install --timeout 120 --retries 10 -r requirements.txt` (repeat if needed; downloads are kept). |
| `No module named 'psycopg'` | Packages installed before Phase 11 | `pip install -r requirements.txt` again. |
| `Error loading ASGI app. Could not import module "backend.main"` | uvicorn started from the wrong folder | `cd` into the project folder (where `requirements.txt` is), then start again. |
| `[Errno 10048] ... only one usage of each socket address` / `address already in use` | Another app (or another uvicorn) uses port 8000 | Close the other terminal running uvicorn, or use another port: `uvicorn backend.main:app --reload --port 8001` and open http://localhost:8001. |
| `[startup] STOP: FOLLOWUP_CONTACT is empty` | `APP_ENV=production` requires a named follow-up adult | Set `FOLLOWUP_CONTACT=Name (role), email` in `.env`, or set `APP_ENV=local` for local use. |
| `FileNotFoundError: Strategy file not found` | Typo in `STRATEGY_SET` | Use `strategies_4` or `strategies_esconv8`. |
| `ZoneInfoNotFoundError: 'Asia/Kolkata'` | `tzdata` missing (Windows has no timezone database) | `pip install -r requirements.txt`. |

## Windows quirks

| You see | Why | Fix |
|---|---|---|
| `setx` worked but the new setting (e.g. `pip cache dir`) still shows the old value | `setx` only affects terminals opened **afterwards** | Close the terminal and open a **new** one (sometimes sign out and in again). |
| `python -c "..."` gives `SyntaxError: unterminated string literal` | Windows PowerShell removes `\"` inside a command | Use only **single quotes** inside the `"..."` (all commands in the docs are written that way). |
| Path errors with spaces (e.g. `C:\Users\My Name\...`) | Spaces split the path | Put the path in quotes: `cd "C:\Users\My Name\Documents\stillspace"`. |
| CSV opens in Excel with garbled text (`Ã©`) or all in one column | Encoding or separator | The app writes Excel-friendly UTF-8. If you edit and save a CSV in Excel, choose **CSV UTF-8 (Comma delimited)**. In Excel: *Data → From Text/CSV* lets you pick UTF-8. |
| **C: drive full** | Default locations are on C: | Keep the project on D:, then (once) `setx PIP_CACHE_DIR D:\cache\pip`, `setx HF_HOME D:\cache\hf`, `setx OLLAMA_MODELS D:\ollama\models`, open a new terminal, and before installing set `$env:TMP="D:\cache\tmp"; $env:TEMP="D:\cache\tmp"`. Check with `pip cache dir`. |

## In the browser

| You see | Why | Fix |
|---|---|---|
| Old page / changes don't show after `git pull` | Browser cache | **Ctrl+F5** (hard refresh). |
| "Stillspace could not start / Cannot reach the Stillspace server" | uvicorn isn't running | Start it again; click **Try again**. |
| Participant code refused locally | Only letters, digits and hyphens, 3–20 characters | E.g. `P001` (no spaces or symbols). |
| Code refused online ("This participant code is not valid") | Online, only codes from `create_codes.py` work | Use an issued code; create new ones if needed. Codes made before the Phase 11 fix must be re-created. |
| "Too many sign-in attempts" | 10 attempts per minute per IP | Wait a minute. |
| Signed out after closing the tab | The code is kept per tab only, on purpose | Type the code again. |
| Conversation gone after a refresh | A refresh starts a new chat session (messages stay in the database) | Known limitation (K-07). |

## The AI model

| You see | Why | Fix |
|---|---|---|
| "Mock mode" tag although you set a key | `LLM_API_KEY` is empty, `MOCK_MODE=true`, or the server wasn't restarted | Check `.env`, save, restart uvicorn; the start-up line should say `mock_mode=False`. |
| Yellow "The AI model could not be reached…" + Retry; terminal `AuthenticationError ... 401` | Wrong or deleted API key | Create a new key on OpenRouter, paste it into `.env`, restart. |
| Terminal `NotFoundError ... 404` / "model not found" | The model ID doesn't exist (any more) | Check available models (Phase 4 check 0 in `implementation.md`, or `docs/SETUP.md` §9) and update `LLM_MODEL`. `qwen/qwen3-8b` is no longer on OpenRouter; use `qwen/qwen3-14b`. With Ollama: `ollama list` and `ollama pull <model>`. |
| Terminal `RateLimitError ... 429` from the provider | Too many requests or no credit left | Wait, add credit, or check the key's limit on OpenRouter. |
| "You've reached the message limit for now…" in the chat | Stillspace's own limit (40/hour per participant, 700/day total) | Wait, or change `CHAT_LIMIT_PER_HOUR` / `DAILY_CHAT_LIMIT` in `.env` (local testing). Safety replies are never limited. |
| `APIConnectionError: Connection error` | No internet, or Ollama isn't running | Check internet; for Ollama start `ollama serve` (see below). |
| Replies are very slow, or show "Fallback reply" | The model "thinks" before answering and runs out of tokens (Qwen3 hybrid/thinking models) | Use an **instruct** model (e.g. `qwen3:4b-instruct-2507-q4_K_M` on Ollama). The app already asks models not to think and removes thinking text. |
| `<think>` text appears in a reply | A model ignored the "no thinking" setting | Shouldn't happen (`llm.strip_thinking` removes it); report it with the model name. |
| `[classifier] attempt 1 failed: no JSON object` / `JSON object is not closed`, then `fallback` | The model's answer wasn't valid JSON (often a thinking model hitting the 200-token limit) | The app retries once, then uses safe defaults. Use an instruct model; check `python scripts/eval_classifier.py` shows `source=llm`. |
| First reply takes 30+ seconds with Ollama | The model is loading into memory | Normal for the first message; `LLM_TIMEOUT_SECONDS=120` allows for it. |

### Ollama on Windows
| You see | Fix |
|---|---|
| Models download to **C:** even though `OLLAMA_MODELS` is set | The tray app started before the setting existed. Quit Ollama (tray icon → *Quit*, or `Get-Process ollama* \| Stop-Process -Force`) and start the server yourself: `$env:OLLAMA_MODELS = "D:\ollama\models"; ollama serve` (keep that terminal open). The log should show `OLLAMA_MODELS:D:\\ollama\\models`. Optionally turn off Ollama in *Settings → Apps → Startup*. |
| `bind: Only one usage of each socket address` when running `ollama serve` | Another Ollama is already running: `Get-Process ollama* \| Stop-Process -Force`, then `ollama serve` again. |
| `ollama run qwen3:4b ...` prints "Thinking..." even with `--think=false` | That tag is an always-thinking build. Use `qwen3:4b-instruct-2507-q4_K_M`. |

## Database

| You see | Why | Fix |
|---|---|---|
| Want a clean start | Old test data | Stop uvicorn, `Remove-Item data\stillspace.db`, start again (a new empty database is created). **Deletes all local data.** |
| DB Browser shows "database is locked" | The app is writing at the same moment | Close DB Browser's "Write Changes" / stop uvicorn while editing. Prefer read-only browsing. |
| `password authentication failed` (Supabase) | Wrong password in `DATABASE_URL` | Copy the Session pooler URI again and replace `[YOUR-PASSWORD]`. |
| `could not translate host name` / connection timeout (Supabase) | You copied the "Direct connection" string | Use Project → **Connect** → **Session pooler** URI. |
| SSL errors (Supabase) | SSL not requested | Add `?sslmode=require` at the end of `DATABASE_URL`. |
| The local app suddenly writes to Supabase | `DATABASE_URL` is set in `.env` | Put `#` in front of that line to go back to the local SQLite file. |

## Scripts

| You see | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'backend'` when running a script | Run it **from the project folder**: `python scripts/eval_classifier.py` (not from inside `scripts/`). |
| `eval_classifier.py` warns the test set expects strategies not in the set | The test set is labelled for `strategies_4`; set `STRATEGY_SET=strategies_4` for a fair score. |
| `--summarise` says the matching responses file is not found | Keep `responses_<time>.csv` and `rating_sheet_<time>_blind.csv` together in `exports/` with their original names. |
