# Stillspace architecture

> How the pieces fit together, in plain language. For the user's point of view (sign-in, journey) see `flow.md`.

## 1. Frontend and backend

```
 Browser                                   One Python process (uvicorn)
┌──────────────────────────┐   fetch()    ┌──────────────────────────────────────────┐
│ frontend/index.html      │  JSON over   │ backend/main.py  (FastAPI)               │
│ frontend/styles.css      │ ───────────▶ │   /            → frontend/index.html     │
│ frontend/app.js          │ ◀─────────── │   /static/*    → frontend/ files         │
│  (the mockup's design)   │   /api/...   │   /api/...     → backend/routes/*.py     │
└──────────────────────────┘              │                     │                    │
                                          │   safety · classifier · policy · prompt  │
                                          │   llm / mock · checkins · db             │
                                          └───────────┬──────────────────┬───────────┘
                                                      │                  │
                                         SQLite file or Supabase    AI model (OpenRouter,
                                         (Postgres)                  Ollama) – or mock
```

- **Frontend** = what the browser shows. Plain HTML, CSS and JavaScript (no framework, no build step). It never talks to the AI or the database directly; it only calls `/api/...`. Every call goes through one helper, `api()` in `app.js`.
- **Backend** = the Python program. It serves the page, decides what's due, runs the safety check and the AI calls, and stores everything. API keys live only here (in `.env`), never in the browser.

## 2. The chat pipeline (`backend/routes/chat.py`)

```
message ─▶ 1 safety.find_crisis_match ──match──▶ fixed crisis reply (no AI) ─┐
              │ no match                                                     │
              ▼                                                              │
           limits (ratelimit.py) ──over──▶ friendly limit message            │
              │                                                              │
              ▼                                                              │
           2 classifier.classify ─▶ {strategy, emotion, intensity, stage, risk}
              │                                                              │
           3 risk == "high" ──yes──▶ fixed crisis reply ─────────────────────┤
              │ no                                                           │
           4 strategy_policy.choose_strategy(requested, classified, ...)     │
              │                                                              │
           5 prompt_builder.build_messages(strategy, meta, check-ins, history)
              │                                                              │
           6 llm.chat_completion(...)  or  mock.mock_reply(...)              │
              │                                                              │
           7 db.insert_message × 2 (user + assistant, all metadata) ◀────────┘
              │
              ▼
           JSON reply → app.js shows it with a badge and updates the side panel
```

## 3. Each file's job

### Backend (`backend/`)

| File | Job | Teaching session |
|---|---|---|
| `main.py` | Creates the FastAPI app, plugs in the routes, serves the frontend, start-up checks | 3 |
| `config.py` | Reads `.env` into plain variables; helplines; `is_mock_mode()`; `load_strategies()` | 3 |
| `routes/config_route.py` | `GET /api/config`: strategies, helplines, mock/demo mode, consent text | 3 |
| `llm.py` | `chat_completion()`: one OpenAI-compatible call; removes "thinking" text | 4 |
| `mock.py` | Offline replies and the keyword classifier for mock mode | 4 |
| `safety.py` | Crisis-word check (normalises spelling tricks), fixed crisis reply, PHQ item-9 rule | 5 |
| `strategy_policy.py` | `choose_strategy()`: safety > request > classifier > first strategy | 6 |
| `classifier.py` | `classify()`: one AI call at temperature 0 → JSON; robust parsing, retry, fallback | 7 |
| `prompt_builder.py` | `build_messages()`: system prompt + strategy + meta + check-ins + history | 9 |
| `routes/chat.py` | `POST /api/chat`: the 7-step pipeline above | 9–10 |
| `checkins.py` | PHQ-9 scoring and bands, what's due today, check-in context for the prompt | 11 |
| `db.py` | Small SQL helpers (participants, check-ins, sessions, messages, safety report) | 11 |
| `db_connect.py` | Opens SQLite or Postgres; creates tables; the two small SQL differences | 11 |
| `routes/participants.py` | Sign-in, status, preferences, demo date; online: issued codes + age consent | 11 |
| `routes/checkins.py` | `POST /api/checkins`: setup, daily (merged per day), PHQ-9, reflection | 11 |
| `routes/sessions.py` | Start, end and summary of a chat session (ownership checked) | 11 |
| `ratelimit.py` | Message and sign-in limits kept in memory | (online) |
| `auth.py` | Sign-in tokens: issue, check (`require_participant`), revoke | 11 |

### Data and prompts (`backend/data/`): editable without touching code

| File | What it holds |
|---|---|
| `strategies_4.json` / `strategies_esconv8.json` | Each strategy's name, description (for the classifier and UI), instruction (for the prompt) and example |
| `crisis_keywords.json` | Crisis phrases and patterns, each with an id |
| `prompts/system.txt` | The reply prompt with placeholders (`{strategy_name}`, `{emotion}`, …) |
| `prompts/plain_system.txt` | Prompt with no strategy (Phase 4 chat; condition A in evaluations) |
| `prompts/classifier.txt` | The classifier prompt (asks for JSON only) |
| `prompts/crisis_response.txt` | The fixed crisis reply |
| `consent.txt` | Study text for the online consent page |
| `schema_sqlite.sql` / `schema_postgres.sql` | Table definitions |

### Frontend (`frontend/`)
`index.html` (layout), `styles.css` (the mockup's CSS, unchanged, plus a marked "additions" block), `app.js` (the mockup's JavaScript, with every change marked `CHANGED:`).

### Scripts (`scripts/`)
`eval_classifier.py`, `eval_responses.py`, `export_data.py`, `create_codes.py`, `safety_report.py`, `delete_participant.py`. All run from the project folder: `python scripts/<name>.py`.

## 4. The database (spec section 9)

| Table | One row is… | Important columns |
|---|---|---|
| `participants` | a participant code | `code`, `dob`, `preferred_strategy`, `setup_done`, `demo_day_offset`, `age_group`, `guardian_consent`, `consent_at`, `issued` |
| `checkins` | one saved check-in | `type` (setup/daily/fortnightly/post_session), `answers_json` (skipped = key absent, never 0), `phq_total`/`phq_band` (only if all 9 answered), `item9_flag`, `local_date`, `session_id` |
| `sessions` | one conversation | `started_at`, `ended_at`, `chat_seconds` |
| `auth_tokens` | one active sign-in | `participant_id`, `token_hash` (SHA-256, never the token), `created_at`, `expires_at` |
| `messages` | one chat message | `role`, `text`, `requested_strategy`, `classified_strategy`, `used_strategy`, `meta_json` (emotion, intensity, stage, risk, …), `safety_flag`, `source` (llm/mock/safety/fallback), `model`, `latency_ms` |

Look inside: **DB Browser for SQLite** → open `data/stillspace.db` → *Browse Data*. Or export everything: `python scripts/export_data.py` (CSV files in `exports/`).

## 5. Main API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/config` | Settings the page needs |
| `POST /api/participants` | Sign in with `{code, …}` → **sign-in token** + status (local: a new code creates the participant). The only endpoint that takes the code |
| `GET /api/me/status` | What's due, latest PHQ-9, preference, saved answers |
| `PATCH /api/me` | Save preferred strategy / date of birth |
| `POST /api/checkins` | Save a check-in (server scores PHQ-9) |
| `POST /api/sessions` | Start a chat session |
| `POST /api/chat` | `{session_id, message, requested_strategy}` → reply + strategy + meta + safety |
| `POST /api/sessions/{id}/end` | Store end time |
| `GET /api/sessions/{id}/summary` | Summary page data |
| `POST /api/logout` | "Switch participant": the token stops working |
| `POST /api/demo/advance` | Move the demo date (local demo mode only) |

**Who is asking (sign-in tokens, D-60).** After sign-in, the browser sends `Authorization: Bearer <token>` with every request. `backend/auth.py` → `require_participant()` finds the participant **from the token**, so a request can only reach the data of the person who signed in. Session ids are also checked against that participant. Tokens expire after `SIGN_IN_HOURS` (default 12), are deleted on *Switch participant*, and only their SHA-256 hash is stored (table `auth_tokens`). A crisis message with an expired token still gets the fixed safety reply (not stored).

## 6. How to switch things (only `.env` changes)

| To… | Set |
|---|---|
| Use mock mode | `LLM_API_KEY=` (empty) or `MOCK_MODE=true` |
| Use OpenRouter | `LLM_BASE_URL=https://openrouter.ai/api/v1`, `LLM_API_KEY=sk-or-…`, `LLM_MODEL=qwen/qwen3-14b` |
| Use Ollama | `LLM_BASE_URL=http://localhost:11434/v1`, `LLM_API_KEY=ollama`, `LLM_MODEL=qwen3:4b-instruct-2507-q4_K_M` |
| Use a different classifier model | `CLASSIFIER_MODEL=…` (empty = same as `LLM_MODEL`) |
| Use the 8 ESConv strategies | `STRATEGY_SET=strategies_esconv8` |
| Leave check-ins out of the prompt | `INCLUDE_CHECKINS_IN_PROMPT=false` |
| Send more/less history | `HISTORY_TURNS=6` (number of earlier messages) |
| Use Supabase instead of SQLite | `DATABASE_URL=postgresql://…` (Session pooler URI) |
| Switch on the online safeguards | `APP_ENV=production` (+ `FOLLOWUP_CONTACT`, see `docs/DEPLOYMENT.md`) |

Restart uvicorn after changing `.env`.

## 7. Design choices worth knowing

- **No ORM, no framework beyond FastAPI**: plain SQL and plain functions, so a student can read everything.
- **All prompt text in `.txt` files**: change wording without touching Python.
- **Safety before AI**: the keyword check runs first and never needs the model.
- **Server is the source of truth**: PHQ-9 scores, what's due and the summary are computed by the server, not the browser.
- Every decision and its reason is in `decisions.md` (and numbered in `implementation.md`).
