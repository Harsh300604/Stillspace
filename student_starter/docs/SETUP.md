# Setting up Stillspace on your computer

> **For someone who has never used a terminal.** Windows first; macOS/Linux notes at the end.
> Takes about 30–45 minutes the first time (most of it downloads). Afterwards, starting the app takes one minute.
> Something goes wrong? Look up the message in `docs/TROUBLESHOOTING.md`.

You'll install four free programs, download the project, and start it in **mock mode** (no AI account needed). Adding a real AI model is the last, optional step.

---

## 1. Install the tools (once)

| Tool | Why | Where |
|---|---|---|
| **Python 3.11 or 3.12** | Runs the app | https://www.python.org/downloads/ |
| **VS Code** | Edits files and has a built-in terminal | https://code.visualstudio.com/ |
| **Git** | Downloads the project and its updates | https://git-scm.com/download/win |
| **DB Browser for SQLite** | Lets you look inside the database | https://sqlitebrowser.org/dl/ |

**Python, important:** on the first installer screen, **tick "Add python.exe to PATH"** before clicking *Install Now*. If you forget, uninstall and install again with the box ticked.

**Git:** the default options are fine (keep clicking *Next*).

**Check it worked.** Open **PowerShell** (Start menu → type "PowerShell" → open it) and type each line, pressing Enter after each:
```powershell
python --version
```
```powershell
git --version
```
✅ You see something like `Python 3.11.9` and `git version 2.x`. If Windows opens the Microsoft Store instead of showing a version, Python isn't on PATH: reinstall with the box ticked.

> **Low on disk space (C: drive almost full)?** You can keep everything on another drive (e.g. D:): put the project folder there (step 2), and before installing packages run `setx PIP_CACHE_DIR D:\cache\pip` once, then **open a new PowerShell window**. See the D: drive notes in `docs/TROUBLESHOOTING.md`.

## 2. Download the project

In PowerShell, go to the folder where you keep projects (e.g. Documents) and download:
```powershell
cd $HOME\Documents
```
```powershell
git clone https://github.com/harsh300604/stillspace.git
```
```powershell
cd stillspace
```
✅ `git clone` ends with `done`. (If it asks you to sign in, use the GitHub account that was given access. No Git? Download the ZIP from GitHub → *Code* → *Download ZIP*, unzip it, and `cd` into the folder.)

**Open it in VS Code:** type `code .` (with the dot), or start VS Code → *File* → *Open Folder…* → choose the `stillspace` folder. From now on you can use VS Code's own terminal: menu *Terminal* → *New Terminal*.

## 3. Create the virtual environment (once)

A virtual environment ("venv") is a private box of Python packages just for this project, so nothing clashes with other projects.

In the terminal, **inside the `stillspace` folder**:
```powershell
python -m venv .venv
```
```powershell
.\.venv\Scripts\Activate.ps1
```
✅ The line now starts with `(.venv)`. You need this **every time** you open a new terminal for the project.

**Red error about "running scripts is disabled"?** Run this once, answer `Y`, then activate again:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 4. Install the packages (once)

```powershell
pip install -r requirements.txt
```
✅ It ends with `Successfully installed ...`. Then check:
```powershell
pip list
```
✅ The list includes `fastapi`, `uvicorn`, `pydantic`, `openai`, `python-dotenv`, `tzdata`, `psycopg`.

**Slow internet / "Read timed out"?** Run it with more patience (you can repeat it; finished downloads are kept):
```powershell
pip install --timeout 120 --retries 10 -r requirements.txt
```

## 5. Create your settings file (once)

```powershell
Copy-Item .env.example .env
```
`.env` holds your settings (and later your API key). It is **never** uploaded to GitHub. Leave it as it is for now: an empty `LLM_API_KEY` means **mock mode**.

## 6. Start the app

```powershell
uvicorn backend.main:app --reload
```
✅ You see:
```
[startup] Stillspace 0.1.0 | env=local | strategies=strategies_4 | mock_mode=True | demo_mode=True | db=...\data\stillspace.db
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```
**Leave this terminal open**: closing it stops the app. Stop it any time with **Ctrl+C**.

## 7. Open it in the browser

Go to **http://localhost:8000**.
1. Type a participant code, e.g. `P001`, tick the box, click **Continue →**.
2. Do the setup, daily and two-week check-ins (all optional), or click **Skip to chat**.
3. Send a message. A "Mock mode" tag shows the replies are built-in examples.
4. Click **Finish & reflect** → answer or skip → see your **summary**.

✅ Everything works without internet. The database file appears at `data\stillspace.db`; open it in **DB Browser for SQLite** (*Open Database* → *Browse Data*) to see what was stored.

## 8. Every time after that (one minute)

```powershell
cd $HOME\Documents\stillspace
```
```powershell
.\.venv\Scripts\Activate.ps1
```
```powershell
uvicorn backend.main:app --reload
```
To get the latest version of the project first: `git pull`.

---

## 9. Optional: use a real AI model

### Option A: OpenRouter (hosted, small cost)
1. Create an account at https://openrouter.ai, add a small amount of credit (**Credits**).
2. **Keys** → *Create key* → **set a credit limit** (e.g. $2–5) so it can never cost more → copy the key (starts with `sk-or-`).
3. Open `.env` in VS Code and set:
   ```
   LLM_BASE_URL=https://openrouter.ai/api/v1
   LLM_API_KEY=sk-or-paste-your-key-here
   LLM_MODEL=qwen/qwen3-14b
   ```
4. Save, stop the app (Ctrl+C) and start it again. ✅ The start-up line says `mock_mode=False`; replies now come from Qwen (each takes a few seconds).

**Never share your key**: not in chats, screenshots or GitHub. If it leaks, delete it on OpenRouter and make a new one. Check the model still exists before a session:
```powershell
(Invoke-RestMethod https://openrouter.ai/api/v1/models).data | Where-Object id -like "qwen/*" | Select-Object id | Format-Table -AutoSize
```

### Option B: Ollama (free, runs on your computer)
Needs about 4 GB of free memory (a graphics card helps). Install from https://ollama.com/download, open a **new** terminal, then:
```powershell
ollama pull qwen3:4b-instruct-2507-q4_K_M
```
In `.env`:
```
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen3:4b-instruct-2507-q4_K_M
```
(`LLM_API_KEY` must not be empty, or the app switches to mock mode; Ollama ignores the value.) Use an **instruct** model: plain `qwen3:4b` "thinks" for a long time before every answer.

### Back to mock mode
Empty the key (`LLM_API_KEY=`), save, restart.

---

## macOS / Linux

Same steps, with these differences:

| Windows | macOS / Linux |
|---|---|
| Python from python.org, tick "Add to PATH" | `python3` (macOS: python.org installer or Homebrew `brew install python`; Ubuntu: `sudo apt install python3 python3-venv`) |
| `python -m venv .venv` | `python3 -m venv .venv` |
| `.\.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |
| `Copy-Item .env.example .env` | `cp .env.example .env` |
| `$HOME\Documents` | `~/Documents` |

Everything else (`pip install`, `uvicorn backend.main:app --reload`, http://localhost:8000) is identical.
