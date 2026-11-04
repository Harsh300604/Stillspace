# Deploying Stillspace online (Supabase + Railway or Render)

> **Read this first.** Sharing Stillspace with other people makes it a study with real participants, and some of them may be in distress. **Do not share any link until every item in the [pre-launch checklist](#5-pre-launch-checklist-do-not-share-the-link-before-this-is-complete) is done.** The code provides safeguards; the approvals, consent and follow-up are the research team's responsibility.

What runs where:

| Part | Service | What you need |
|---|---|---|
| Database | **Supabase** (Postgres) | One value: the **Session pooler connection string** |
| AI model | **OpenRouter** (paid credits) | An API key **with a spending limit** |
| The app (backend + web page) | **Railway** or **Render** | The GitHub repository and the environment variables below |

Your laptop setup does not change: with `DATABASE_URL` empty and `APP_ENV=local`, Stillspace still runs on SQLite + Ollama/mock mode, exactly as in the student course.

---

## 1. Supabase (database)

1. Go to https://supabase.com → **New project**. Choose a strong database password and save it in a password manager. Pick the region **closest to India** (e.g. *South Asia (Mumbai)* if offered).
2. When the project is ready: **Connect** (top bar) → **Session pooler** → copy the **URI**. It looks like:
   ```
   postgresql://postgres.abcdefghijkl:[YOUR-PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:5432/postgres
   ```
   Replace `[YOUR-PASSWORD]` with your password and add `?sslmode=require` at the end.
   - Use the **Session pooler** string: it works from Railway and Render (IPv4). The "Direct connection" may not.
   - **This string contains your password.** Put it only in `.env` (git-ignored) or in the host's variables. Never in code, chats or screenshots.
3. You do **not** need the anon key, the service-role key or the project URL. Stillspace talks to Postgres directly.
4. The tables are created automatically the first time the app starts with `DATABASE_URL` set. Row Level Security is switched on for all four tables, so Supabase's public Data API cannot read them. Only the app's own connection can.
5. Backups: check what your Supabase plan includes (Project → Database → Backups). Also run `python scripts/export_data.py` regularly and store the CSVs securely.

**Test from your laptop first** (venv active, in the project folder):
```powershell
pip install -r requirements.txt
```
Put the string in `.env` as `DATABASE_URL=...`, start uvicorn, and check that the start-up line says `db=postgres (aws-0-...pooler.supabase.com)`. In Supabase → **Table Editor** you should see `participants`, `checkins`, `sessions`, `messages`, each marked **RLS enabled**.

> While `DATABASE_URL` is set, your local app also writes to Supabase. To go back to local SQLite, put a `#` in front of the `DATABASE_URL` line and restart.

## 2. Participant codes

Online, only codes you create can sign in (`P001` and other made-up codes are refused):
```powershell
python scripts/create_codes.py --count 20
```
With `DATABASE_URL` set, the codes go straight into Supabase and are marked as **issued**. Codes you typed while testing locally (like `P001`) may also be in the database, but they never work online. Give each code to **one** person privately.

> Tip: use a **separate Supabase project** for local testing and keep the real one only for the study, so test data never mixes with participant data. The list is saved in `exports\issued_codes_<time>.csv`; keep it like a password list (who got which code is identifying information).

## 3. OpenRouter (AI model)

1. https://openrouter.ai → **Keys** → create a key and **set a credit limit** on it (e.g. a few dollars). Add credits under **Credits**.
2. Check the model is still listed (no key needed):
   ```powershell
   (Invoke-RestMethod https://openrouter.ai/api/v1/models).data | Where-Object id -like "qwen/*" | Select-Object id | Format-Table -AutoSize
   ```
   Default: `qwen/qwen3-14b`. If it's gone, pick another Qwen model and set `LLM_MODEL`.
3. In OpenRouter's **privacy settings**, turn off options that allow providers to train on or keep prompts, if available. Name the provider and its data policy in your consent text.

## 4. The app: Railway **or** Render

Both run the app without Docker. Use the branch you want to deploy (e.g. `main` after merging).

### Environment variables (same for both)

| Variable | Value |
|---|---|
| `APP_ENV` | `production` |
| `DATABASE_URL` | the Supabase Session pooler string (with `?sslmode=require`) |
| `LLM_BASE_URL` | `https://openrouter.ai/api/v1` |
| `LLM_API_KEY` | your OpenRouter key |
| `LLM_MODEL` | `qwen/qwen3-14b` |
| `CLASSIFIER_MODEL` | *(empty = same as `LLM_MODEL`)* |
| `LLM_TIMEOUT_SECONDS` | `60` |
| `FOLLOWUP_CONTACT` | **required**: name, role and how to reach them, e.g. `Ms Rao (study lead), rao@example.org` |
| `AGE_POLICY` | `18plus_or_guardian` (or `18plus_only`) |
| `CHAT_LIMIT_PER_HOUR` | `40` |
| `DAILY_CHAT_LIMIT` | `700` |
| `LOGIN_LIMIT_PER_MINUTE` | `10` |
| `SIGN_IN_HOURS` | `12` (how long a sign-in token stays valid) |
| `APP_TIMEZONE` | `Asia/Kolkata` |
| `STRATEGY_SET` | `strategies_4` |
| `INCLUDE_CHECKINS_IN_PROMPT` | `true` |
| `PYTHON_VERSION` | `3.11.9` (Render) |

If `FOLLOWUP_CONTACT` is missing, the app **refuses to start** and the log says why.

### Railway
1. https://railway.app → **New Project** → **Deploy from GitHub repo** → choose the repository and branch.
2. Service → **Settings** → **Custom Start Command**:
   ```
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```
3. **Variables** → add every variable from the table.
4. **Settings → Networking → Generate Domain** → you get an `https://…up.railway.app` link.
5. **Deployments → View logs**: look for `[startup] … env=production … demo_mode=False | db=postgres (…pooler.supabase.com)`.

### Render
1. https://render.com → **New** → **Web Service** → connect the repository and branch.
2. Runtime **Python 3**; Build command `pip install -r requirements.txt`; Start command:
   ```
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```
3. **Environment** → add every variable from the table (including `PYTHON_VERSION`).
4. Choose an instance type. Free instances sleep when idle (the first visit then takes ~1 minute); use a paid instance for a real study.
5. **Logs**: look for the same `[startup] … env=production …` line. Your link is `https://<name>.onrender.com`.

### After deploying
- Open the link on your phone: the consent page shows the study text and the age question.
- Sign in with one issued code, chat, send one synthetic crisis test message (e.g. from `eval/safety_prompts.csv`), and check the helplines appear.
- Run `python scripts/safety_report.py --days 1` on your laptop (with the same `DATABASE_URL`): the test flag is listed.
- Then delete the test participant: `python scripts/delete_participant.py <code>`.

---

## 5. Pre-launch checklist (do not share the link before this is complete)

| ✓ | Item | Notes |
|---|---|---|
| ☐ | **Ethics approval** from the supervising organisation for this online study | Spec section 16 |
| ☐ | **Consent text** in `backend/data/consent.txt` replaced with the **approved** wording (team, purpose, data stored, AI provider, retention period, withdrawal, contacts, helplines) | Redeploy after editing |
| ☐ | **Under-18 participants:** signed parent/guardian consent forms collected **before** giving them a code (the in-app tick only records the confirmation) | Or set `AGE_POLICY=18plus_only` |
| ☐ | **Named follow-up adult** agreed and set in `FOLLOWUP_CONTACT` | Knows what to do on a flag (docs/SAFETY.md) |
| ☐ | **Safety review routine** written down: **who** runs `python scripts/safety_report.py`, **how often** (daily suggested) and **how fast** they follow up | There is no automatic alert (D-51) |
| ☐ | **Privacy notice** and a **DPDP Act 2023** check (PHQ-9 and date of birth are health/personal data) | Supabase region noted |
| ☐ | **Retention period** decided, and a reminder set to delete data at the end (`delete_participant.py` per code, or delete the Supabase project) | |
| ☐ | **OpenRouter key** has a spending limit; provider data settings checked | |
| ☐ | `DEMO_MODE` absent or `false`, `APP_ENV=production` (start-up line shows `env=production`, `demo_mode=False`) | `/docs` returns 404 |
| ☐ | Test run done: sign-in with an issued code, chat, crisis test, safety report, test participant deleted | Section 4 "After deploying" |

## 6. Running the study

- **Every day (or as agreed):** `python scripts/safety_report.py --days 1`, then follow up on each flag as agreed with the follow-up adult. The report shows code, time and type only, never message text.
- **Withdrawal request:** `python scripts/delete_participant.py <code>`, and also delete that participant from any earlier exports.
- **Regular backup:** `python scripts/export_data.py` → store the CSVs securely (they contain participant data).
- **Costs:** check OpenRouter usage weekly. The limits (40 messages per participant per hour, 700 per day for the whole app) cap the worst case.
- **Limits reset when the app restarts** (they are kept in memory). That's fine for a small study on one instance.
- **End of the study:** export, then delete the data according to the retention plan, and remove the deployed service and the OpenRouter key.
