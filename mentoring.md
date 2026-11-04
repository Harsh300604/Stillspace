# Stillspace: mentoring plan (16 sessions × 1 hour, online)

> **For the mentor** (the developer who built and tested the reference app). You will guide **one student** in building the Python "brain" of Stillspace, starting from `student_starter/`, over **16 one-hour online sessions**.
> **The finished app is your answer key:** the main project folder (`backend/`, `scripts/`, …). The student never needs it.
> **Read first:** `docs/SAFETY.md` (fully), `flow.md`, `docs/ARCHITECTURE.md`. Keep `docs/TROUBLESHOOTING.md` open during every session.

---

## Contents

- [Part A: Course overview](#part-a-course-overview)
  - [Learning outcomes](#learning-outcomes) · [Session map](#session-map) · [Before session 2](#before-session-2-what-the-student-installs) · [How online sessions run](#how-online-sessions-run) · [Catch-up plan](#catch-up-plan) · [Giving the student the starter](#giving-the-student-the-starter-not-the-answer-key)
- [Part B: Safety briefing script (session 1)](#part-b-safety-briefing-script-session-1)
- [Part C: The 16 sessions](#part-c-the-16-sessions)
  - [1](#session-1--project-ethics-safety) · [2](#session-2--setup) · [3](#session-3--how-the-app-talks) · [4](#session-4--first-llm-call-and-memory) · [5](#session-5--safety-layer) · [6](#session-6--strategies-and-policy) · [7](#session-7--classifier-prompt) · [8](#session-8--testing-the-classifier) · [9](#session-9--prompt-builder) · [10](#session-10--explainability) · [11](#session-11--check-ins-and-data-ethics) · [12](#session-12--using-check-in-context) · [13](#session-13--evaluation-design) · [14](#session-14--rating-and-comparison) · [15](#session-15--results-and-presentation) · [16](#session-16--final-demo--buffer)
- [Appendix](#appendix): [Glossary](#a1-glossary) · [Presentation rubric](#a2-rubric-for-the-final-presentation) · [Final demo checklist](#a3-final-demo-checklist) · [Answer-key map](#a4-answer-key-map) · [Real bugs from the build](#a5-real-bugs-from-the-build-teaching-stories)

---

# Part A: Course overview

## What the student builds

Stillspace is a chat app: a person writes how they feel, and the app answers supportively. Before every reply it **chooses a support strategy** (Validation, Reflection, Reassurance or Advice), reads **meta details** (emotion, intensity, stage, risk) and builds a detailed prompt for a **Qwen** model. A **keyword safety check** runs first and answers crisis messages with helplines, without any AI.

The student **does not** rebuild the web page, database or check-ins. Those are finished in `student_starter/`, and the student learns to read them. The student **writes the five brain pieces**:

| Piece | File → function | Session |
|---|---|---|
| The model call | `backend/llm.py` → `chat_completion()` | 4 |
| Conversation memory | `backend/prompt_builder.py` → `build_messages()` | 4 |
| Safety check (already works; studied and tested) | `backend/safety.py` → `check_message()` | 5 |
| Strategy policy | `backend/strategy_policy.py` → `choose_strategy()` | 6 |
| Classifier | `backend/classifier.py` → `classify()`, `parse_classifier_output()` and `backend/data/prompts/classifier.txt` | 7 |
| Strategy-aware prompt | `backend/prompt_builder.py` → `build_system_prompt()`, `build_messages()` | 9 |

Every core file starts with a header like `# mentoring.md: Session 7 - Classifier prompt`, so the code and this plan line up.

## Learning outcomes

By the end, the student can:
1. **Explain** how a web app works: browser (frontend) ↔ JSON API ↔ Python server (backend) ↔ database and AI model.
2. **Call a large language model** through an OpenAI-compatible API, send conversation history, and handle errors without crashing.
3. **Design a safety-first pipeline**: deterministic checks before AI, fixed crisis replies, and why false negatives are worse than false positives.
4. **Write a classifier prompt** that returns structured JSON, and parse a messy model answer safely.
5. **Build a prompt from parts** (instruction + strategy + meta + context + history) and see how each part changes the reply.
6. **Measure, not guess**: accuracy, a confusion table, preference bias, a blind A/B rating study.
7. **Handle health data responsibly**: what is stored, what is sent to the AI, consent, DPDP Act 2023.
8. **Present** a technical project honestly, with its results *and* limitations.

## Session map

| # | Theme | Student does | Mode |
|---|---|---|---|
| 1 | Project, ethics, safety | Tours the finished app (mentor's screen) in mock mode; learns the 4 strategies, the disclaimer and the safety rules | Mentor's laptop, mock |
| 2 | Setup | Checks the installs; creates the venv; runs `student_starter/` in mock mode | Mock |
| 3 | How the app talks | Frontend vs backend; reads `main.py` and `/api/config`; edits a strategy description and sees it in the UI | Mock |
| 4 | First LLM call and memory | Writes `llm.chat_completion`, adds an API key, sends conversation history | **Real model** |
| 5 | Safety layer | Reads the keyword safety check, runs the safety test set, discusses false positives and negatives | Mock |
| 6 | Strategies and policy | Reads the strategy file, writes `choose_strategy`; the requested strategy works | Mock |
| 7 | Classifier prompt | Writes the classifier prompt and the JSON parsing in `classify` | **Real model** |
| 8 | Testing the classifier | Runs `eval_classifier.py`, reads accuracy, improves descriptions | Real |
| 9 | Prompt builder | Writes `build_system_prompt` and finishes `build_messages` (strategy + meta) | Mock, then real |
| 10 | Explainability | Compares replies across strategies using the side panel | Real |
| 11 | Check-ins and data ethics | Learns how PHQ-9 is scored and stored; explores the database | Mock |
| 12 | Using check-in context | Toggles `INCLUDE_CHECKINS_IN_PROMPT` and compares replies | Real |
| 13 | Evaluation design | Runs `eval_responses.py`; learns the rating criteria | Real |
| 14 | Rating and comparison | Rates replies blind; compares with vs without strategies (and models if time) | Offline (CSV) |
| 15 | Results and presentation | Summarises results and limitations; prepares demo and slides or poster | — |
| 16 | Final demo / buffer | Final demo; catch-up if earlier sessions overran | Real (mock as backup) |

**"Real model"** means OpenRouter with a key (Option A in `docs/SETUP.md` §9) or Ollama on the student's laptop (Option B). Every session also works in **mock mode** as a fallback when the internet or the key fails; then the "done when" checks that need a real model move to homework.

## Before session 2: what the student installs

Send this list after session 1. The student installs at home (about 30 minutes, mostly downloads); session 2 checks it and continues.

| Tool | Notes |
|---|---|
| **Python 3.11 or 3.12** (python.org) | Tick **"Add python.exe to PATH"** on the first screen. Check: `python --version` |
| **VS Code** (code.visualstudio.com) | Then install the **Python** extension (Extensions icon → search "Python" → Microsoft) |
| **Git** (git-scm.com) | Default options. Check: `git --version` |
| **DB Browser for SQLite** (sqlitebrowser.org) | Needed from session 11 |
| **Zoom / Google Meet** with screen sharing | Test screen sharing once |

Laptop minimum: 8 GB RAM, a modern browser, internet. **No GPU needed.**

**The AI model (decide before session 4):**
- **Hosted (recommended for most students):** you, the mentor, create an **OpenRouter key with a spending limit of $2–5** for the student (OpenRouter → *Keys* → *Create key* → credit limit). The whole course uses well under $1 with `qwen/qwen3-14b`. Send the key privately (not in a group chat), and delete it after session 16.
- **Free, local:** if the student's laptop has 16 GB RAM (a GPU helps), Ollama with `qwen3:4b-instruct-2507-q4_K_M` works (`docs/SETUP.md` §9 Option B). Download the model (~2.5 GB) at home before session 4.

## How online sessions run

- **The student shares their screen and types. You guide.** Don't take remote control except in an emergency; people learn by typing.
- **Ask before you tell.** Every session lists questions to ask and **hints in order**. Give one hint, wait, then the next. Show the answer only when the student is stuck for more than ~5 minutes on one step, and then have them type it, not paste it.
- **One terminal rule:** the app runs in terminal A (`uvicorn ... --port 8001`); commands run in terminal B (venv active in both). Most "it doesn't work" moments are the wrong terminal or an inactive venv.
- **Lab notebook:** the student keeps `notes.md` in the starter folder. At the end of each session they write 3 lines: *what I built, what surprised me, one question*. These notes become the presentation in session 15.
- **Commit at the end of each session** (optional, if the student uses Git): `git add -A` then `git commit -m "Session N"`. A good habit, and an easy way back if something breaks.
- **Default time plan:** 10 min recap and concept · 35 min hands-on · 10 min check · 5 min wrap-up. Each session gives its own plan.
- **Before every session (5 min):** run the finished app on your laptop in the same mode, and for real-model sessions check the model still exists:
  ```powershell
  (Invoke-RestMethod https://openrouter.ai/api/v1/models).data | Where-Object id -like "qwen/*" | Select-Object id | Format-Table -AutoSize
  ```
  (`qwen/qwen3-8b` disappeared during the build; models change.)

## Catch-up plan

Sessions overrun; that's normal. In order of preference:
1. **Move the "done when" check to the start of the next session** (5 min) instead of rushing it.
2. **Give the answer for the remaining steps** of a TODO and have the student type it while explaining each line back to you. Understanding matters more than writing every line alone.
3. **Merge light sessions:** 10 + 12 (both "compare replies" sessions) fit into one hour; 14's rating can be homework.
4. **Session 16 is the buffer**: up to 30 minutes of it can finish an earlier session; the demo needs 30 minutes.
5. **Never skip:** the safety briefing (1), the safety test (5), and the safety parts of 7 (the risk rule) and 11 (data ethics).

If the student falls a whole session behind, copy the finished function from the answer key into their starter **together**, read it line by line, and carry on. The next session must start from working code.

## Giving the student the starter (not the answer key)

The repository contains the finished app next to `student_starter/`. Give the student **only the starter**, so the answers aren't one folder away. On your laptop (PowerShell, in the project folder):
```powershell
Compress-Archive -Path student_starter\* -DestinationPath D:\CreatED-cloud\stillspace_starter.zip -Force
```
Check the zip contains `.env.example` and `docs\` (SETUP, SAFETY, TROUBLESHOOTING, ARCHITECTURE copies), and **no** `.env`, `.venv\` or `data\*.db` (`student_starter\.gitignore` already keeps them out of Git, but a zip copies everything). Send the zip; the student unzips it into e.g. `Documents\stillspace_starter`. Everything in this plan says "the starter folder" for that folder.

---

# Part B: Safety briefing script (session 1)

> Read this aloud (or in your own words, keeping every point). About 10 minutes. Ask the student to repeat the three rules back at the end.

**1. What Stillspace is, and isn't**
"Stillspace is a research and learning prototype. It's a chat app that tries to answer supportively, and it shows *why* it answered the way it did. It is **not therapy, not a diagnosis tool, and not an emergency service**. A language model can sound caring and still be wrong, miss danger, or say something unhelpful. That's exactly why we build a safety layer that doesn't depend on the AI, and why we test it."

**2. Rule one: never use your own real problems as test input**
"We'll test the app a lot. Always use the **prepared messages** in `eval/`, which I wrote, or made-up role-play. Please never type in something you are really going through, and never ask a friend to. Two reasons: the app is not built to help a real person, and test data ends up in files that we read, export and discuss. You also never have to write crisis messages yourself; the test set already has them."

**3. Rule two: if something real comes up, we stop**
"If at any point *you* feel low, or something in our work brings up something real for you or someone you know, tell me. We stop the session, no explanation needed, and the project can wait. If you or anyone is in immediate danger, call **112**. **Tele-MANAS 14416** (or 1-800-891-4416) is free, 24×7, and in many Indian languages. You can also talk to a parent, teacher or school counsellor. I'd rather pause a hundred sessions than miss one real moment."

**4. Rule three: never weaken safety to make something work**
"Some code in this project protects people: the keyword check in `safety.py`, the `Safety` line in `choose_strategy`, the risk rule in the classifier. If a test fails, we fix the cause; we never delete or loosen a safety rule to get it green. If you're unsure whether a change touches safety, ask."

**5. What happens if a real disclosure happens in a session** (tell the student what *you* will do)
"If someone shares something real, I will stop the session, listen, share the helplines, call 112 if anyone is in danger, and involve a trusted adult, a parent or guardian for you, and the supervisor. I won't promise to keep it secret if someone may be at risk. That's the safeguarding procedure, and it's in `docs/SAFETY.md` section 5."

**6. Real participants need approvals**
"Using this with real people, even friends, needs ethics approval, consent (guardian consent under 18), a named adult who follows up on safety flags, and a privacy notice. PHQ-9 answers and dates of birth are health and personal data under India's DPDP Act 2023. In this course we only use made-up conversations."

**Close:** "Can you tell me the three rules in your own words?" (own problems never; something real → stop and tell; never weaken safety.)

> **Mentor:** if a real disclosure ever happens (from the student or anyone), follow `docs/SAFETY.md` §5 exactly, inform the supervisor the same day, and look after yourself too.

---

# Part C: The 16 sessions

Each session has the same parts: **Goal** · **Mentor prep** · **Time plan** · **Concepts** (analogy + questions) · **Hands-on** (steps, hints before answers) · **Done when** · **Common errors** · **Answer key** · **Homework** · **Next time**.

All paths are relative to the **starter folder** (student) or the **project folder** (mentor's answer key). All commands are PowerShell, with the venv active, run from the starter folder.

---

## Session 1 – Project, ethics, safety

**Goal:** the student understands what Stillspace does, why the strategy layer exists, and the safety rules.
**Student has at the end:** a mental picture of the app, the three safety rules, and the install list for session 2.

**Mentor prep**
- Start the **finished app** on your laptop in **mock mode** (comment out `LLM_API_KEY` in `.env`, or set `MOCK_MODE=true`; comment out `DATABASE_URL` so you use a throwaway local SQLite file). `uvicorn backend.main:app --reload`, open http://localhost:8000.
- Have `docs/SAFETY.md` and `backend/data/strategies_4.json` open.
- Prepare the install list (Part A) to send afterwards.

**Time plan**
| Min | What |
|---|---|
| 0–10 | Introductions; what the student hopes to learn; the course in one slide (session map) |
| 10–20 | **Safety briefing** (Part B) |
| 20–45 | Tour of the finished app (you share your screen; the student tells you what to click) |
| 45–55 | The 4 strategies and why a strategy layer exists |
| 55–60 | Install list for session 2; questions |

**Concepts**
- **Support strategies.** People who support others use different moves: acknowledging feelings (*Validation*), mirroring back what they hear (*Reflection*), giving hope or perspective (*Reassurance*), suggesting steps (*Advice*). The research behind this project (ESConv dataset; Kang et al., ACL 2024) found that language models on their own over-use a few strategies. Choosing the strategy *first* and telling the model makes replies more varied and explainable.
- **Analogy:** a good friend first *decides* whether you need a hug or a plan, *then* talks. Stillspace makes that decision visible.
- **Questions to ask:**
  1. "When a friend is upset, how do you decide whether to listen or give advice?"
  2. "Why might it matter that the app *shows* which strategy it used?"
  3. "Who could be harmed if a chatbot like this gets it wrong?"

**Hands-on (the tour, on your screen)**
1. **Consent page:** read the disclaimer in the footer together ("Student research prototype. Not therapy…").
2. Sign in as `P001`. **Setup check-in** (date of birth, preferred strategy), **daily mood**, **PHQ-9** (explain it's a standard screening questionnaire, not a diagnosis). Click **Preview repeat visits → Next day / 14 days later** to show the schedules.
3. **Chat:** send a few test messages from `eval/test_messages.csv` (e.g. T01 grief, a "what should I do" message). Point at the **badge** under each reply and the **right panel**: *Requested by you*, emotion · intensity · stage.
4. Set **Requested by you → Advice** and send another message: the badge changes. "Your choice beats the app's guess."
5. **Safety:** paste a `crisis` row from `eval/safety_prompts.csv` (e.g. S01). The gold **Safety response** box appears with tap-to-call numbers; the risk indicator says **Follow-up needed**. Show the terminal line `[chat] strategy=Safety safety=keyword rule=...`. "No AI was involved in that reply."
6. **Finish & reflect** → **Summary**.

**Done when:** the student can explain, in their own words, (a) what happens between typing a message and seeing a reply, roughly, (b) the four strategies, (c) the three safety rules.

**Common issues**
- Student asks to try their own message → steer to the test files ("rule one").
- Questions about real use with friends → "needs approvals; see rule six."

**Answer key:** `flow.md` (the user journey and the chat pipeline); `docs/SAFETY.md`.

**Homework (15–20 min):** install the tools from the list (Part A). Read the first page of `README.md` in the starter zip. Start `notes.md` with the three safety rules in your own words.

**Next time:** your own copy of the app running on your laptop.

---

## Session 2 – Setup

**Goal:** the starter runs on the student's laptop in mock mode.
**Student has at the end:** the starter folder, a working venv, the app at http://localhost:8001, and a first look at the folder.

**Mentor prep**
- Send the starter zip (Part A, "Giving the student the starter") before the session.
- Open `docs/SETUP.md` and `docs/TROUBLESHOOTING.md` (you'll use them live).
- Mock mode; no key needed.

**Time plan**
| Min | What |
|---|---|
| 0–10 | Check installs: `python --version`, `git --version`, VS Code opens |
| 10–40 | Unzip, venv, packages, `.env`, start the app |
| 40–50 | Click through the app in mock mode; send one message |
| 50–60 | Folder tour in VS Code; terminal A / terminal B; wrap-up |

**Concepts**
- **Terminal, folder, command.** The terminal is a text way to tell the computer what to do; you always run commands "inside" a folder.
- **Virtual environment (venv)**. **Analogy:** a separate pencil case for each subject. The project's packages go in its own case, so nothing clashes with other projects.
- **`.env`**: a private settings file (later: the API key). It is never shared or uploaded.
- **Questions to ask:**
  1. "Why would two projects need different package versions?"
  2. "Why must the API key never go into the code or GitHub?"
  3. "What does `localhost` mean?"

**Hands-on**
1. Unzip the starter into `Documents\stillspace_starter`. In VS Code: *File → Open Folder…* → that folder. Open a terminal (*Terminal → New Terminal*).
2. Create and activate the venv:
   ```powershell
   python -m venv .venv
   ```
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   *Hint 1:* the prompt must start with `(.venv)`. *Hint 2:* red "running scripts is disabled" → `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, answer `Y`, activate again.
3. Install the packages and check:
   ```powershell
   pip install -r requirements.txt
   ```
   ```powershell
   pip list
   ```
   *Hint:* slow internet → `pip install --timeout 120 --retries 10 -r requirements.txt`.
4. Settings file: `Copy-Item .env.example .env`. Open `.env` and read it together. Point out `LLM_API_KEY=` is empty → **mock mode**.
5. Start the app (this is **terminal A**; leave it running):
   ```powershell
   uvicorn backend.main:app --reload --port 8001
   ```
6. Open http://localhost:8001, sign in as `S001`, skip to chat, send a message. Show the **Mock mode** tag.
7. Open a **second terminal** (terminal B: *Terminal → New Terminal*, then activate the venv). Run the safety test (copy it from the starter's `README.md`, "Useful commands").
8. Folder tour: `frontend/` (the page), `backend/` (Python), `backend/data/` (strategies, prompts, keywords), `eval/` (test sets), `scripts/`, `data/` (the database appears here).

**Done when**
- Terminal A shows `[startup] Stillspace ... | mock_mode=True ...` and `Uvicorn running on http://127.0.0.1:8001`.
- The chat answers in mock mode; the badge says **Validation** (that's a placeholder until session 6, which is fine).
- Terminal B prints `30 rows, 0 mismatches`.

**Common errors**
| Error | Fix |
|---|---|
| `python` opens the Microsoft Store | Reinstall Python with "Add to PATH" ticked; new terminal |
| `No module named 'fastapi'` / `uvicorn` not recognized | venv not active in this terminal |
| `Could not import module "backend.main"` | Not in the starter folder (`cd` to the folder with `requirements.txt`) |
| Port 8001 in use | Another uvicorn running; close it or use `--port 8002` |

**Answer key:** `docs/SETUP.md` (same steps), `student_starter/README.md`.

**Homework (15 min):** stop and start the app twice on your own (venv → uvicorn). Write in `notes.md`: what does `mock_mode=True` mean?

**Next time:** how the browser and Python talk to each other, and your first change.

---

## Session 3 – How the app talks

**Goal:** the student understands frontend vs backend and the JSON API, and makes a first change that shows up in the UI.
**Student has at the end:** an edited strategy description visible in the browser; they can read an API response.

**Mentor prep**
- Open in the reference app: `backend/main.py`, `backend/config.py`, `backend/routes/config_route.py`, `frontend/app.js` (search for `async function api`), `docs/ARCHITECTURE.md` §1.
- Mock mode.

**Time plan**
| Min | What |
|---|---|
| 0–10 | Recap; the restaurant analogy |
| 10–25 | Read `main.py` and `config_route.py` together |
| 25–40 | Look at `/api/config` in the browser and in DevTools |
| 40–50 | Edit a strategy description; see it in the UI |
| 50–60 | Check; wrap-up |

**Concepts**
- **Frontend** (HTML/CSS/JS in the browser) vs **backend** (Python on your computer). They talk through **endpoints** like `/api/config` that return **JSON**.
- **Analogy:** a restaurant. The **frontend is the dining room** (what you see), the **API is the waiter** (takes an order, brings back a plate), the **backend is the kitchen** (does the work), the **database is the pantry**. Diners never walk into the kitchen; the browser never sees the API key.
- **Questions to ask:**
  1. "Why does the browser ask the server for the strategy list instead of having it written in `app.js`?"
  2. "Why is the API key *not* in the `/api/config` answer?"
  3. "What is the difference between `/` and `/api/config`?"

**Hands-on**
1. Open `backend/main.py`. Find: where the app is created (`FastAPI(...)`), where routes are plugged in (`include_router`), where the page is served (`/` and `/static`). *Question:* "Which file answers `/api/config`?"
2. Open `backend/routes/config_route.py` → `get_config()`. Read the dictionary it returns. Note the comment about the API key and the strategy instructions staying on the server.
3. In the browser, open **http://localhost:8001/api/config**. Find `strategies`, `helplines`, `mock_mode`. (Chrome/Edge show a "Pretty-print" tick box.)
4. Open DevTools (**F12**) → **Network** tab → reload the app page → click `config`. Show *Headers* (GET) and *Response*. *Then* send a chat message and find the `chat` request (POST) and its JSON body: `session_id`, `message`, `requested_strategy`. Under *Request Headers* find `Authorization: Bearer …`: the **sign-in token**. *Question:* "The body has no participant code. How does the server know whose chat this is?" (From the token: `backend/auth.py` → `require_participant()`. The code is sent only once, at sign-in, so nobody can ask for someone else's data by changing a code.)
5. Open `frontend/app.js`, search `async function api`. "Every call to the server goes through this one helper."
6. **First change:** open `backend/data/strategies_4.json`. Change the `description` of **Reassurance** (e.g. add "Use when the user fears the worst."). Save.
   *Hint 1:* JSON needs double quotes and commas between items. *Hint 2:* if the app shows "could not start", a comma or quote is missing; VS Code underlines the error in red.
7. Reload http://localhost:8001/api/config: the new text is there. In the app (**Ctrl+F5**), hover over **Reassurance** in the *Requested by you* list: the tooltip shows the new description.
8. Open `backend/config.py` → `load_strategies()`. "Where does `STRATEGY_SET` come from?" (`.env`.)

**Done when:** `/api/config` and the tooltip show the student's edited description, and the student can explain the path *browser → `api()` → `/api/config` → `get_config()` → `load_strategies()` → JSON file*.

**Common errors**
| Error | Fix |
|---|---|
| Page shows "Stillspace could not start" after the edit | JSON syntax error; undo the change (Ctrl+Z) and retry |
| Change doesn't show | Hard refresh **Ctrl+F5** |
| `FileNotFoundError: Strategy file not found` | `STRATEGY_SET` misspelt in `.env` |

**Answer key:** `docs/ARCHITECTURE.md` §1, §3, §5; `backend/routes/config_route.py`.

**Homework (15 min):** in DevTools, find which endpoint is called when you sign in, and what it returns. Write it in `notes.md`. Undo or keep your description change: keep it short and clear, because the classifier will read it in session 7.

**Next time:** the real AI model. Mentor sends the OpenRouter key privately (or the student pulls the Ollama model).

---

## Session 4 – First LLM call and memory

**Goal:** the student writes the function that calls the AI model and gives it memory.
**Student has at the end:** real AI replies in the chat; the model remembers earlier messages.

**Mentor prep**
- The student's API key ready (OpenRouter with a limit), or Ollama with `qwen3:4b-instruct-2507-q4_K_M` pulled on their laptop. Check the model ID exists (Part A command).
- Answer key open: `backend/llm.py` → `chat_completion()`, `backend/prompt_builder.py` → `build_messages()`.
- Know what the placeholder looks like: the chat says "(Placeholder reply: llm.chat_completion is still a TODO for Session 4…)" and terminal A prints `[TODO Session 4] ...`.

**Time plan**
| Min | What |
|---|---|
| 0–10 | Recap; what an LLM API call is (tokens, messages, temperature) |
| 10–15 | Put the key in `.env`; restart; see the placeholder |
| 15–40 | Write `chat_completion()` |
| 40–50 | Memory: finish the Session 4 TODO in `build_messages()` |
| 50–60 | Done-when checks; wrap-up |

**Concepts**
- **LLM API call.** You send a list of **messages** (`system` = instructions, `user` = what the person said, `assistant` = earlier replies) and get text back. **Tokens** are word pieces; `max_tokens` caps the reply length (and cost). **Temperature** = how creative/random (0 = always the same).
- **The model has no memory.** Every call starts fresh. "Memory" means *we* send the earlier messages again each time.
- **Analogy:** a phone call with someone who forgets everything when they hang up. To continue the conversation you read them the transcript first. `HISTORY_TURNS=6` = how many earlier lines you read out.
- **Questions to ask:**
  1. "If the model forgets everything, how does ChatGPT seem to remember?"
  2. "What could go wrong when calling a server on the internet?" (no internet, wrong key, model removed, slow)
  3. "Why send only the last 6 messages, not all of them?" (cost, speed, the model's context limit)

**Hands-on**
1. Edit `.env` (OpenRouter):
   ```
   LLM_BASE_URL=https://openrouter.ai/api/v1
   LLM_API_KEY=sk-or-...
   LLM_MODEL=qwen/qwen3-14b
   ```
   or (Ollama): `LLM_BASE_URL=http://localhost:11434/v1`, `LLM_API_KEY=ollama`, `LLM_MODEL=qwen3:4b-instruct-2507-q4_K_M`. Save, restart uvicorn (Ctrl+C, then the up arrow). Start-up line: `mock_mode=False`. Send a message → the placeholder text appears.
2. Open `backend/llm.py`, scroll to `chat_completion()`. Read the docstring steps together. Read the helpers above it first: `_make_client()`, `_thinking_off()`, `strip_thinking()`. "Why remove `<think>` text?" (Qwen3 models can "think out loud"; that text isn't meant for the user.)
3. The student writes the 7 steps, replacing the placeholder lines (`print(...)` and `return {...}`).
   - *Hint 1 (step 1):* `model = model or config.LLM_MODEL`
   - *Hint 2 (steps 3 and 5):* `started = time.perf_counter()` … `int((time.perf_counter() - started) * 1000)`
   - *Hint 3 (step 4):* the `create(...)` call is in the docstring; wrap it in `try:` / `except OpenAIError as error:`.
   - *Hint 4 (step 6):* `text = response.choices[0].message.content or ""`
4. Save (uvicorn reloads by itself). Send a message → a real reply. Terminal A: `[chat] strategy=Validation ... source=llm ...`.
5. **Memory test, before the fix:** send "My name is Asha and I have a maths test on Friday." then "What day is my test?" The model doesn't know.
6. Open `backend/prompt_builder.py` → `build_messages()`. The Session 4 TODO: put the history between the system message and the new message.
   - *Hint 1:* the result should look like `[system, *history, user]`.
   - *Hint 2:* `history` is already a list of `{"role", "content"}` dictionaries.
   - Leave the Session 9 TODO for later.
7. Click **＋ New session** and repeat the memory test: now it knows.
8. Error handling: change one letter of the key in `.env`, restart, send → a yellow "The AI model could not be reached…" box, and terminal A shows `AuthenticationError`. The app didn't crash. Put the key back.

**Done when**
- Real replies; terminal A shows `source=llm` and a latency in ms.
- The model answers "What day is my test?" correctly in a new session.
- A wrong key gives the friendly yellow message, not a crash.

**Common errors**
| Error | Fix |
|---|---|
| Still the placeholder text | File not saved, or the placeholder `return` is still above the new code |
| `mock_mode=True` after adding the key | `.env` not saved or server not restarted |
| `NotFoundError ... 404` | Model ID wrong or removed; check the model list |
| `AuthenticationError ... 401` | Key typo; no quotes or spaces around the key |
| `APIConnectionError` with Ollama | `ollama serve` not running |
| Reply cut off / "Fallback reply" / very slow | A "thinking" model; use an instruct model (D-39) |
| `NameError: name 'model' is not defined` | Step 1 missing |

**Answer key:** `backend/llm.py` → `chat_completion()`; `backend/prompt_builder.py` → `build_messages()` (the history line).

**Homework (15 min):** in `notes.md`, explain in 3 sentences why the model "forgets" and how we fixed it. Optional: change `HISTORY_TURNS=2` in `.env`, restart, and test how quickly it forgets. Set it back to 6.

**Next time:** the safety layer, the most important part, and how we test it.

---

## Session 5 – Safety layer

**Goal:** the student understands the keyword safety check, runs the safety test set, and can explain false positives and false negatives.
**Student has at the end:** the safety test passing, a written list of the check's limits, and (optionally) one new *normal* test idea checked.

**Mentor prep**
- Re-read `docs/SAFETY.md` §2–4 and Part B.
- Open: `backend/safety.py` (`normalise`, `variants`, `load_rules`, `find_crisis_match`, `check_message`), `backend/data/crisis_keywords.json`, `eval/safety_prompts.csv`, `backend/data/prompts/crisis_response.txt`, `scripts/safety_report.py`.
- Mock mode is fine (the safety check never needs the model). **The student never writes crisis messages; use the prepared rows only.**

**Time plan**
| Min | What |
|---|---|
| 0–10 | Recap; why safety runs before AI; the smoke-alarm analogy |
| 10–30 | Read `safety.py` and `crisis_keywords.json` together |
| 30–45 | Run the safety test; try the `crisis` rows in the app; safety report |
| 45–55 | Discussion: false positives vs false negatives; limits |
| 55–60 | Wrap-up; reminder of rule three |

**Concepts**
- **Deterministic vs AI.** A keyword check always gives the same answer for the same text, works offline, and can be tested exactly. An AI is a second net, not the first.
- **False positive** = alarm without a crisis ("I love the movie *suicide* squad" gets the crisis reply). **False negative** = a real crisis missed. For safety, a false negative is much worse, so the project *keeps* known false positives.
- **Analogy:** a **smoke alarm**. It sometimes goes off when you burn toast (false positive), and that's annoying but fine. An alarm that stays silent in a real fire (false negative) is a disaster. You never remove the battery because of the toast.
- **Questions to ask:**
  1. "Why doesn't the crisis reply come from the AI model?"
  2. "Which is worse here, a false alarm or a missed message? Why?"
  3. "How might someone accidentally (or on purpose) write a crisis message the check misses?"

**Hands-on**
1. Open `backend/safety.py`. Read the header comment. Then `normalise()`: what does each line do? Try it in terminal B:
   ```powershell
   python -c "from backend.safety import normalise; print(normalise('I CAN’T take this, s.u.i.c.i.d.e, k1ll'))"
   ```
   ✅ Expected: `i cant take this, suicide, kill`
2. `variants()`: why two versions for stretched letters? (`dieee` → `die`, but `killlll` → `kill` needs two l's.)
3. Open `backend/data/crisis_keywords.json`: **phrases** (plain text, matched as whole words) and **patterns** (regular expressions), each with an **id**. Note the Hinglish and Devanagari entries. "Why does every rule have an id?" (So a flag can be reviewed: which rule fired, without storing the message in the report.)
4. `find_crisis_match()` and `check_message()`: read them; they already work. "This is the only brain function that works from day one. Why?" (Safety must never be missing.)
5. Run the safety test in terminal B (command in the starter's `README.md`). ✅ `30 rows, 0 mismatches`. Open `eval/safety_prompts.csv`: 20 `crisis` rows (direct, indirect, spelling tricks, Hinglish, Devanagari) and 10 `normal` rows (figures of speech like "This exam is killing me").
6. In the app, paste rows S01 and S08 (any two `crisis` rows): the **Safety response** box, tap-to-call numbers, risk indicator **Follow-up needed**. Terminal A: `[chat] strategy=Safety safety=keyword rule=en-kill-myself ...`. Then paste N01: an ordinary reply.
7. Safety report (what the follow-up adult would run online):
   ```powershell
   python scripts/safety_report.py --days 1
   ```
   It lists code, time, flag type and rule id, **never the message text**. "Why not the text?" (privacy; the follow-up adult needs to know *who* and *when*, not to read the conversation.)
8. **Optional exercise (normal side only):** the student thinks of a figure of speech that should *not* trigger, e.g. "I nearly died laughing", and checks it:
   ```powershell
   python -c "from backend.safety import find_crisis_match; print(find_crisis_match('I nearly died laughing'))"
   ```
   ✅ `None`. Discuss: what if it *had* triggered? (Keep it: a false positive is acceptable; never add an exception that could hide a real crisis.)

**Discussion: three real stories from building this check** (see Appendix A5)
- **The `!` bug.** An early version swapped look-alike characters, including `!` → `i`. That turned "die!" into "diei", and a crisis message would have been **missed**. A change that looked harmless weakened safety, and only the test set caught it. Lesson: run the test after *every* safety change.
- **Devanagari and word boundaries.** `\b` ("whole word") doesn't work for Hindi script, so those phrases are matched as plain text.
- **Spaced letters.** While this teaching plan was being written, the developer noticed "d i e" (letters separated by spaces) was not caught. A rule now joins three or more single letters. Ask: "What other tricks could slip through?" (Write them in `notes.md`; the classifier's risk rule in session 7 is the second net.)

**Done when**
- `30 rows, 0 mismatches`.
- The student can explain, without notes: why safety runs before AI; one false positive and one possible false negative; why we never "fix" a false positive by removing a rule.

**Common errors**
| Error | Fix |
|---|---|
| `SyntaxError: unterminated string literal` in the `python -c` command | PowerShell strips `\"`; use the command exactly as written (single quotes inside) |
| `ModuleNotFoundError: No module named 'backend'` | Run from the starter folder, not inside `backend/` |
| A change to `crisis_keywords.json` doesn't show in the app | Rules are loaded once; restart uvicorn (the test one-liner always reads the file fresh) |

**Answer key:** `backend/safety.py` (identical in the starter, apart from the optional TODO); `docs/SAFETY.md`.

**Homework (15 min):** in `notes.md`, write a short paragraph: "Three limits of the keyword check, and why the app still uses it." Read the 4 strategies in `backend/data/strategies_4.json`: description vs instruction.

**Next time:** choosing which strategy to use.

---

## Session 6 – Strategies and policy

**Goal:** the student understands the strategy file and writes `choose_strategy()`.
**Student has at the end:** the user's requested strategy works; with "Automatic" the classifier's suggestion is used.

**Mentor prep**
- Open: `backend/data/strategies_4.json`, `backend/data/strategies_esconv8.json`, `backend/strategy_policy.py`, and in `backend/routes/chat.py` the line with `strategy_policy.choose_strategy(`.
- Mock mode is enough (the mock classifier gives suggestions too). Real mode also works.

**Time plan**
| Min | What |
|---|---|
| 0–10 | Recap; what a "policy" is |
| 10–25 | Read the strategy files |
| 25–45 | Write `choose_strategy()` |
| 45–55 | Test in the app; try the 8-strategy set |
| 55–60 | Wrap-up |

**Concepts**
- **A strategy file** has, per strategy: `name`, `description` (*when* to use it: for the classifier and the UI tooltip), `instruction` (*how* to do it: for the reply prompt), `example`.
- **A policy** is a small set of rules that decides between inputs. Order matters: **safety > user's request > classifier > first strategy**.
- **Analogy:** a **GPS**. It suggests a route (the classifier), but if you say "take the highway" (the request) it follows you. And if a road is closed (safety), nothing else matters.
- **Questions to ask:**
  1. "Why should the user's choice beat the classifier's?"
  2. "Why store both the requested and the used strategy?" (research: how often do they differ?)
  3. "What should happen if the classifier invents a strategy name that doesn't exist?"

**Hands-on**
1. Open `backend/data/strategies_4.json`. Read **Validation** and **Advice**: compare `description` and `instruction`. "Which part does the browser see?" (Only name and description, from session 3.)
2. Peek at `strategies_esconv8.json`: 8 strategies from the ESConv research dataset (Question, Restatement or Paraphrasing, …).
3. Before writing code, send a message with **Requested by you → Advice**: the badge still says **Validation** (the placeholder always returns the first strategy).
4. Open `backend/strategy_policy.py` → `choose_strategy()`. Rule 1 (safety) is done. **Never remove that line.** The student writes rules 2–4 below it, replacing the placeholder `return`.
   - *Hint 1:* rule 2 needs three conditions: `requested` is not `None`, is not `"Automatic"`, and is `in strategy_names`.
   - *Hint 2:* `if requested and requested != "Automatic" and requested in strategy_names: return requested`
   - *Hint 3:* rule 3 is the same idea for `classified`; rule 4 is `return strategy_names[0]`.
5. Test in the app (uvicorn reloads by itself):
   - **Advice** requested → badge **Advice**.
   - **Automatic**, message "What should I do about my exam stress? Any tips?" → badge **Advice** (mock classifier) and terminal A shows `requested=Automatic, classified=Advice`.
   - **Automatic**, message T01 (grief) → **Validation**.
6. Quick check from terminal B:
   ```powershell
   python -c "from backend.strategy_policy import choose_strategy as c; n=['Validation','Reflection','Reassurance','Advice']; print(c('Advice','Validation','none',n), c('Automatic','Reflection','none',n), c(None,'Made-up','none',n), c('Advice','Advice','keyword',n))"
   ```
   ✅ Expected: `Advice Reflection Validation Safety`
7. Optional: set `STRATEGY_SET=strategies_esconv8` in `.env`, restart, look at the *Requested by you* list (8 options). Set it back to `strategies_4` (the test sets in `eval/` are labelled for the 4-strategy set).

**Done when:** choosing **Advice** makes the badge say **Advice**, and the one-liner prints `Advice Reflection Validation Safety`.

**Common errors**
| Error | Fix |
|---|---|
| Badge still Validation | The placeholder `return strategy_names[0]` is still *above* the new rules |
| One-liner prints `Safety` for the first case | Rule order wrong, or `safety_flag` checked with `==` instead of `!=` |
| Requested strategy ignored after restarting | The select remembers per participant; pick it again |

**Answer key:** `backend/strategy_policy.py` → `choose_strategy()`.

**Homework (15 min):** in `notes.md`, write one realistic message for each of the 4 strategies (everyday stress only, e.g. exams, friends, sport) and which strategy you'd choose. You'll compare with the classifier in session 8.

**Next time:** teaching the model to pick the strategy itself, the classifier.

---

## Session 7 – Classifier prompt

**Goal:** the student writes the classifier prompt and makes the model's JSON answer safe to use.
**Student has at the end:** a working classifier: the side panel shows emotion, intensity and stage chosen by the model; the eval script shows `(llm, ...ms)` on every row.

**Mentor prep**
- **Real model needed** (key or Ollama). Check the model ID.
- Open the answer key: `backend/data/prompts/classifier.txt`, `backend/classifier.py` → `classify()`, `parse_classifier_output()`.
- Know the placeholder: terminal A prints `[TODO Session 7] classifier.classify is not written yet - using default values`.

**Time plan**
| Min | What |
|---|---|
| 0–10 | Recap; what a classifier is; JSON |
| 10–25 | Write the two TODOs in `classifier.txt` |
| 25–40 | Write `parse_classifier_output()` |
| 40–50 | Write `classify()` (with one retry) |
| 50–60 | Done-when checks; wrap-up |

**Concepts**
- **Classifier** = something that puts an input into one of a few boxes. Here a second, short AI call at **temperature 0** reads the message and answers in **JSON**: strategy, emotion, intensity, stage, risk, confidence, rationale.
- **JSON** = a strict text format for data (`{"strategy": "Advice", "intensity": 3}`). Models sometimes add chatter or code fences, or invent values, so we **never trust the answer blindly**: extract, check, clamp, fall back.
- **Safety first in the risk rule:** anything about self-harm or wanting to die, even indirect, is `"high"`; **when unsure, choose high**. Unclear values like "medium" count as high (`clean_risk`).
- **Analogy:** a **triage nurse** at a hospital: a quick look and a form with fixed boxes *before* the doctor (the reply model) sees you. If the nurse writes something unreadable, the hospital uses safe defaults, never a guess.
- **Questions to ask:**
  1. "Why temperature 0 for the classifier but 0.7 for replies?"
  2. "What could a model write that breaks `json.loads`?"
  3. "If the model says risk is 'maybe', what should the app do?"

**Hands-on**
1. Open `backend/data/prompts/classifier.txt`. Read it top to bottom. Point out `{strategy_list}`, `{emotions}`, `{history}`, `{message}`: `build_classifier_prompt()` in `classifier.py` fills them.
2. **TODO 1 (strategy guidance):** replace the first TODO with 3–5 short lines. Let the student write their own first.
   - *Hint 1:* one line per strategy: what *kind of message* fits it?
   - *Hint 2:* e.g. "Choose Advice only when the user asks what to do or wants steps."
   - *Hint 3:* add a tie-breaker, e.g. "If the user mainly needs to feel heard, choose Validation."
3. **TODO 2 (risk rule):** replace the second TODO with the risk line.
   - *Hint 1:* three values: none, low, high. Which messages must always be high?
   - *Hint 2:* "When unsure, choose high."
   - Compare with the answer key's wording afterwards.
4. Open `backend/classifier.py`. Read the helpers that already exist: `extract_json_object()`, `clean_risk()`, `clamp()`, `fallback_result()`, `ClassifierResult`. Try the extractor:
   ```powershell
   python -c "import json; from backend.classifier import extract_json_object as e; print(e('Sure! Here you go: ' + json.dumps({'strategy': 'Advice'}) + ' Hope that helps!'))"
   ```
   ✅ Expected: `{'strategy': 'Advice'}`, the chatter around it is gone. (`json.dumps` is used so PowerShell never sees a double quote inside the command; it also removes code fences like ` ```json `.)
5. **`parse_classifier_output()`** (7 steps in its docstring). Replace the `raise ValueError(...)` line.
   - *Hint 1 (step 2):* `lookup = {n.lower(): n for n in strategy_names}` then `lookup.get(str(raw.get("strategy", "")).strip().lower(), strategy_names[0])`
   - *Hint 2 (step 3):* `emotion = str(raw.get("emotion", "")).lower()` then `if emotion not in EMOTIONS: emotion = "neutral"`
   - *Hint 3 (step 7):* `return ClassifierResult(strategy=..., emotion=..., ...).model_dump()`
6. Test the parser offline in terminal B:
   ```powershell
   python -c "import json; from backend.classifier import parse_classifier_output as p; print(p('Here: ' + json.dumps({'strategy':'advice','emotion':'Stress','intensity':9,'stage':'action','risk':'medium','confidence':2,'rationale':'asks for tips'}), ['Validation','Reflection','Reassurance','Advice']))"
   ```
   ✅ Expected: `{'strategy': 'Advice', 'emotion': 'stress', 'intensity': 5, 'stage': 'action', 'risk': 'high', 'confidence': 1.0, 'rationale': 'asks for tips'}`: the case is fixed, intensity is clamped to 5, "medium" risk became **high**, and confidence is clamped to 1.0.
7. **`classify()`** (steps in its docstring). Keep the mock branch; replace the placeholder `else:` part with the two attempts.
   - *Hint 1:* `for attempt in (1, 2):` with `try:` / `except (llm.LLMError, ValueError) as error:` and `print(f"[classifier] attempt {attempt} failed: {error}")`.
   - *Hint 2:* on success, set `result, source = parsed, "llm"` and `break`.
   - *Hint 3:* before the loop: `result, source = fallback_result(names), "fallback"`, so failure needs no extra code.
8. In the app, **Automatic**: send T01, then "What should I do about my exam? Any tips?" The side panel shows emotion · intensity · stage from the model; terminal A shows `classified=...` with no `[TODO Session 7]` line.

**Done when**
- `python scripts/eval_classifier.py --limit 5` prints rows ending in `(llm, ...ms)` and an accuracy line (`Accuracy: x/5 = ...`). The full run is session 8.
- The parser one-liner gives the expected values above.

**Common errors**
| Error | Fix |
|---|---|
| `[classifier] attempt 1 failed: no JSON object` / `JSON object is not closed` | The model "thought" and ran out of tokens; use an instruct model. Check the last line of `classifier.txt` still asks for ONLY the JSON |
| Every message gets the same strategy | Guidance lines too vague, or descriptions too similar; session 8 measures this |
| `ValidationError` from pydantic | A field has the wrong type; check `round(...)` for intensity and `float` for confidence |
| Every eval row ends in `(fallback, ...)` | `chat_completion` raising (check the key) or `parse_classifier_output` still raising the TODO error |
| `KeyError` in `build_classifier_prompt` | A placeholder like `{message}` was deleted from `classifier.txt` |

**Answer key:** `backend/data/prompts/classifier.txt`; `backend/classifier.py` → `parse_classifier_output()`, `classify()`.

**Homework (15 min):** in `notes.md`: why does the app use a *second* AI call for classification instead of asking the reply model to choose? (Hints: testable on its own, temperature 0, JSON, explainable.)

**Next time:** measuring how good the classifier really is.

---

## Session 8 – Testing the classifier

**Goal:** the student measures the classifier, reads the results, and improves strategy descriptions with evidence.
**Student has at the end:** a baseline accuracy, a before/after comparison, and a short note on bias.

**Mentor prep**
- Real model. Open `scripts/eval_classifier.py` and `eval/test_messages.csv`.
- **The developer's own baseline** (reference app, `qwen3:4b-instruct-2507-q4_K_M`): **27/30 = 90%**, all valid JSON, predictions spread 10/8/5/7 (no single-strategy bias). The 3 misses, **T18, T21, T23**, were all expected **Reassurance**; the model chose Validation or Reflection. They were **left un-tuned on purpose** for this session. The student's numbers will differ (their own prompt and model).

**Time plan**
| Min | What |
|---|---|
| 0–10 | Recap; accuracy, precision, recall, confusion table |
| 10–20 | Full run; read the report together |
| 20–40 | Look at the misses; improve descriptions (or the guidance lines) |
| 40–50 | Re-run; compare |
| 50–60 | Discuss: what does this number really mean? Wrap-up |

**Concepts**
- **Accuracy** = how many right out of all. **Precision** (of the times it said *Advice*, how often was it right?) and **recall** (of the real *Advice* messages, how many did it catch?).
- **Confusion table** = rows = expected, columns = predicted: shows *which* strategies get mixed up.
- **Preference bias** = the model picks one strategy far too often; this is the problem from the research paper the project is built on.
- **Analogy:** a **practice exam**. The score tells you something only if the questions are fair and you haven't seen the answers. If you write the exam *and* the answers, a high score means little.
- **Questions to ask:**
  1. "Who labelled the 30 test messages? Could they be wrong?" (One person, the developer; labels are judgement calls.)
  2. "Is 90% on 30 messages a lot? What would one more miss change?" (Each message = 3.3%.)
  3. "If we tune the prompt until these 30 are perfect, have we made it better for *new* messages?" (Overfitting.)

**Hands-on**
1. Check `.env` has `STRATEGY_SET=strategies_4` (the test set is labelled for it). Run:
   ```powershell
   python scripts/eval_classifier.py
   ```
   (30 messages; a few seconds each.)
2. Read the output together: `Accuracy`, the per-strategy table, the confusion table, "How often each strategy was predicted (preference bias check)". Open `exports/classifier_results.csv` in Excel or VS Code: columns for expected, predicted, correct, emotion, risk, rationale, source.
3. Find the misses (`correct = no`). For each: read the message, the model's rationale, and decide **with the student** whether the label or the model is "right". Example misses from the reference run:
   - T18 "What if I never find friends who actually like me?" (expected Reassurance)
   - T21 "Everyone else seems to have their life figured out and I feel so far behind." (expected Reassurance)
   - T23 "I said something stupid in class today and I can't stop thinking everyone hates me now." (expected Reassurance)
   *Question:* "What do these three have in common?" (catastrophising / 'what if' / comparing; worry about the future rather than pain about the past)
4. Improve **one thing at a time**: e.g. the **Reassurance** `description` in `strategies_4.json` ("…including 'what if' worries, comparing yourself to others, or fearing everyone thinks badly of you"), or a guidance line in `classifier.txt`.
   - *Hint:* keep descriptions short; the classifier reads all four at once. Change one, re-run, compare.
5. Re-run `python scripts/eval_classifier.py`. Write before → after in `notes.md` (accuracy, and which rows changed: fixed *and* newly broken).
6. Discuss: confidence values are usually 0.95+, even when wrong. "Can we trust a model's own confidence?"

**Done when:** the student has a baseline and a second run, can read the confusion table aloud ("Reassurance was confused with Validation 2 times"), and can say one honest limit of the score.

**Common errors**
| Error | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'backend'` | Run from the starter folder: `python scripts/eval_classifier.py` |
| Warning: test set expects strategies not in the set | `STRATEGY_SET=strategies_4` in `.env` |
| `Note: N message(s) used fallback defaults` | Model unreachable or bad JSON; check the key / use an instruct model |
| Accuracy jumps around between runs | Temperature is 0, but providers aren't perfectly deterministic; compare rows, not just the total |
| `PermissionError` writing the CSV | The CSV is open in Excel; close it |

**Answer key:** `scripts/eval_classifier.py` (complete in the starter); the reference result above; Appendix A5 ("A score is only as honest as its test set").

**Homework (20 min):** take your 4 messages from session 6 homework, add them as rows `T31`–`T34` to a **copy** of the test file (don't change the original), and see what the classifier says. Do you agree with it, or with yourself?

**Next time:** the reply prompt, putting the strategy into the model's instructions.

---

## Session 9 – Prompt builder

**Goal:** the student builds the full reply prompt: instructions + strategy + meta details (+ check-ins) + history.
**Student has at the end:** the complete pipeline; replies change with the strategy.

**Mentor prep**
- Open: `backend/data/prompts/system.txt`, `backend/data/prompts/plain_system.txt`, `backend/prompt_builder.py`, and in `backend/routes/chat.py` the commented line `# print("[chat] DEBUG system prompt:\n" ...`.
- Start in **mock mode** (the prompt is built in mock mode too, so the DEBUG print works without a key), then switch to real mode for the last 15 minutes.
- Answer key: `backend/prompt_builder.py` → `build_system_prompt()`, `build_messages()`.

**Time plan**
| Min | What |
|---|---|
| 0–10 | Recap the pipeline (session 1 diagram); what a system prompt is |
| 10–20 | Read `system.txt`; switch on the DEBUG print |
| 20–40 | Write `build_system_prompt()`; finish `build_messages()` |
| 40–55 | Real mode: same message, different strategies |
| 55–60 | Wrap-up |

**Concepts**
- **System prompt** = standing instructions for the model, sent before the conversation. Ours is a **template** with blanks (`{strategy_name}`, `{emotion}`, …) that we fill for every message.
- **Why build it from parts:** each part can be switched on and off and measured (session 12 does exactly that with check-ins). Prompt text lives in `.txt` files so it can be edited without touching Python.
- **Privacy rule:** only today's **mood** and the PHQ-9 **band** (e.g. "mild") may go into the prompt. Never the item answers, never the date of birth.
- **Analogy:** a **briefing note** for a substitute teacher: "This class needs encouragement today (strategy); one student seems anxious (emotion, intensity); we're at the 'talking it through' stage." The teacher still talks in their own words.
- **Questions to ask:**
  1. "Why say 'use gently, never quote it back as data' in `system.txt`?"
  2. "Why does the safety line in `system.txt` exist when the keyword check already runs first?" (Layers: the check can miss things.)
  3. "What could go wrong if we put the raw PHQ-9 answers in the prompt?"

**Hands-on**
1. Open `backend/data/prompts/system.txt`. Find every `{placeholder}`. Compare with `plain_system.txt` (what the app uses until today).
2. In `backend/routes/chat.py`, find `# print("[chat] DEBUG system prompt:` and remove the `# ` at the start of that line. Save. Send a message: terminal A prints the **plain** prompt.
3. Open `backend/prompt_builder.py`. Read `checkin_lines()` (done). Then write `build_system_prompt()` following its 3 steps, replacing the placeholder `return`.
   - *Hint 1:* `.replace("{strategy_name}", strategy["name"])`. You can chain `.replace(...)` calls.
   - *Hint 2:* `meta.get("emotion", "neutral")`, and `str(meta.get("intensity", 3))` (replace needs text).
   - *Hint 3:* if `extra` is empty, `template = template.replace("\n{checkin_lines}", "")` *before* the other replaces.
4. In `build_messages()`, the system message already calls `build_system_prompt(...)`; check the Session 4 history line is still there: `[system, *history, user]`.
5. Send a message (mock mode): terminal A now prints a prompt with `Support strategy for this reply: Validation`, the instruction, `Emotion: ... (intensity .../5)` and the stage. Do a **daily mood** check-in (e.g. *Low*) and send again: `- Mood today: Low` appears.
6. Check there are no `{` placeholders left in the printed prompt.
7. **Real mode** (key back in `.env`, restart): click **＋ New session**, request **Validation**, send "I failed my driving test today and I feel useless." Then **＋ New session**, request **Advice**, send the *same* message. Compare the replies.
8. Put the `# ` back in front of the DEBUG line when done (it's noisy).

**Done when**
- The DEBUG print shows the strategy name, its instruction, emotion, intensity and stage, with no `{...}` left; the mood line appears only after a daily check-in.
- In real mode, the Validation and Advice replies to the same message are clearly different.

**Common errors**
| Error | Fix |
|---|---|
| `TypeError: replace() argument 2 must be str, not int` | Wrap intensity in `str(...)` |
| `{checkin_lines}` printed literally / an empty line in the prompt | Step 2 (remove `"\n{checkin_lines}"` when `extra` is empty) is missing or after the other replaces |
| `KeyError: 'instruction'` | Using the wrong dict; the strategy dict has `name`, `description`, `instruction`, `example` |
| Prompt never changes | Still returning the plain prompt (placeholder `return` above the new code) |
| The model forgot earlier messages again | The Session 4 history line was overwritten |

**Answer key:** `backend/prompt_builder.py` → `build_system_prompt()`, `build_messages()`.

**Homework (15 min):** in `notes.md`, write the full path of one message through the app in 7 steps (keyword safety → limits → classifier → risk → policy → prompt → model → store), naming the file and function for each. This is your presentation's architecture slide.

**Next time:** making the app's reasoning visible, and testing whether it holds up.

---

## Session 10 – Explainability

**Goal:** the student uses the side panel and badges to compare how replies change across strategies, and judges whether the explanation is honest.
**Student has at the end:** a small comparison table in `notes.md` (4 strategies × 2 messages).

**Mentor prep**
- Real model. Open `frontend/app.js` (search `function explainHtml`) and `docs/ARCHITECTURE.md` §2.
- **Lesson from the build (D-45):** sending the same message several times *in one chat* made the model copy its own earlier reply, which looked like "strategies don't work". **Always compare in a fresh session per strategy (＋ New session).**

**Time plan**
| Min | What |
|---|---|
| 0–10 | Recap; what explainability means and why it matters here |
| 10–15 | Read `explainHtml()` |
| 15–45 | The comparison: 2 messages × 4 strategies, fresh session each |
| 45–55 | Discuss: is the badge an honest explanation? |
| 55–60 | Wrap-up |

**Concepts**
- **Explainability** = the user can see *why* the system did something. Here: the badge (used strategy), *Requested by you*, and "emotion · intensity · stage", plus "Classifier suggested X; your request was used" when the request overrides.
- **An explanation can mislead:** the badge says which strategy was *requested from the model*, not whether the model *followed* it. That's what session 13–14 measure.
- **Analogy:** a **recipe card** on a restaurant table says what the chef was asked to cook; you still have to taste the dish to know if they did.
- **Questions to ask:**
  1. "Does the badge prove the reply used that strategy?"
  2. "Why might showing the emotion ('sadness, intensity 4/5') feel uncomfortable for a user?"
  3. "Why compare in fresh sessions?"

**Hands-on**
1. Open `frontend/app.js`, find `function explainHtml()`. When does the "Classifier suggested…; your request was used" note appear?
2. Pick two test messages, e.g. T01 (grief) and one about exam stress from `eval/test_messages.csv`.
3. For each message and each strategy (Validation, Reflection, Reassurance, Advice): **＋ New session** → set *Requested by you* → send the message → copy the reply into a table in `notes.md`. Then once with **Automatic**: what did the classifier choose?
4. For each reply, the student marks: *Does it sound like the strategy? (yes / partly / no)* and one phrase that shows it.
5. Look at terminal A for one message: `requested=Advice, classified=Validation`. Find the same in the side panel.

**Done when:** the table has 8 replies (+2 Automatic) with the student's yes/partly/no judgement, and they can explain the difference between "requested", "classified" and "used".

**Common errors**
| Issue | Fix |
|---|---|
| Replies look identical across strategies | Same chat reused (copying effect); use **＋ New session** each time |
| Badge says *Safety* | The message matched the keyword check or the classifier's risk was high: correct behaviour; pick a different test message |
| Side panel shows no emotion | The reply came from the fallback; check terminal A for classifier errors |

**Answer key:** no new code. `frontend/app.js` → `explainHtml()`; `flow.md` (chat pipeline); D-45 in `implementation.md`.

**Homework (15 min):** in `notes.md`, answer: "What would a user need to see to *trust* the app more? What should they *not* see?"

**Next time:** check-ins, the PHQ-9 and responsible handling of health data.

---

## Session 11 – Check-ins and data ethics

**Goal:** the student understands how check-ins are scored and stored, explores the database, and can explain the data-protection rules.
**Student has at the end:** a tour of all 4 tables, an export, and a written data-flow paragraph.

**Mentor prep**
- Mock mode. **DB Browser for SQLite** installed on the student's laptop.
- Open: `backend/checkins.py` (`score_phq9`, `phq_band`, `clean_phq_answers`, `checkin_context`), `backend/safety.py` → `phq_item9_flag`, `backend/data/schema_sqlite.sql`, `scripts/export_data.py`, `scripts/delete_participant.py`, `docs/SAFETY.md` §7.
- Use made-up check-in answers only.

**Time plan**
| Min | What |
|---|---|
| 0–10 | Recap; what the PHQ-9 is (and isn't) |
| 10–25 | Read the scoring code |
| 25–45 | Explore the database in DB Browser; export |
| 45–55 | Data ethics discussion |
| 55–60 | Wrap-up |

**Concepts**
- **PHQ-9** = a 9-question screening questionnaire for depression symptoms (each 0–3, total 0–27, bands minimal / mild / moderate / moderately severe / severe). A **screening**, never a diagnosis. Developed by Drs. Spitzer, Williams, Kroenke and colleagues.
- **Skipped ≠ zero.** A skipped question is *unknown*. Scoring it as 0 would understate distress, so the total exists only when all 9 are answered.
- **Item 9** (thoughts of being better off dead or of self-harm) > 0 → a follow-up notice with helplines, **whatever the total**.
- **Data ethics:** PHQ-9 answers and dates of birth are health and personal data under India's **DPDP Act 2023**. Collect only what's needed; tell people what's stored; keep it private; delete on request. Only the chat text (plus mood and PHQ band in the prompt) goes to the AI provider.
- **Analogy:** a **doctor's file cabinet**. The receptionist (the AI) gets only a sticky note ("mood: low"), never the whole file.
- **Questions to ask:**
  1. "Why is a skipped question not counted as 0?"
  2. "Why does item 9 matter even when the total is low?"
  3. "What exactly leaves your laptop when you chat with a real model?"

**Hands-on**
1. `backend/checkins.py` → `phq_band()`: read the cut-offs. `score_phq9()`: where does it refuse to give a total? `clean_phq_answers()`: why does the *server* re-check the answers? (The browser's copy could be wrong or edited.)
2. `backend/safety.py` → `phq_item9_flag()`: why is item 9 key `"8"`? (Counting starts at 0.)
3. Try it in terminal B:
   ```powershell
   python -c "from backend.checkins import score_phq9 as s; print(s({'0':1,'1':1,'2':0,'3':1,'4':0,'5':0,'6':1,'7':0,'8':0})); print(s({'0':1,'1':1})); print(s({'0':0,'1':0,'2':0,'3':0,'4':0,'5':0,'6':0,'7':0,'8':1}))"
   ```
   ✅ Expected: total 4 / minimal; then total `None` (incomplete); then total 1 / minimal **with `item9_flag: True`**.
4. In the app: a new participant `S002` → setup (made-up date of birth) → daily mood → PHQ-9 with **one question skipped** → a short chat → reflection.
5. Open **DB Browser for SQLite** → *Open Database* → `data\stillspace.db` → *Browse Data*. Go through `participants`, `checkins` (`answers_json` has no key for the skipped item; `phq_total` is empty), `sessions`, `messages` (`requested_strategy`, `classified_strategy`, `used_strategy`, `meta_json`, `source`). Use read-only browsing; don't click *Write Changes*.
6. Export everything:
   ```powershell
   python scripts/export_data.py
   ```
   ✅ `exports\participants.csv` … `messages.csv` and the reminder "these files contain participant data". Open one in Excel.
7. Delete a participant (what happens when someone withdraws):
   ```powershell
   python scripts/delete_participant.py S002
   ```
   It asks for confirmation; refresh DB Browser: S002's rows are gone.
8. Find the line in `backend/checkins.py` → `checkin_context()` that decides what may go into the prompt. "What's *not* there?" (item answers, date of birth.)

**Done when:** the score one-liner gives the three expected results; the student can show where a skipped answer and an item-9 flag are stored; and they can explain in 3 sentences what is stored, what is sent to the AI, and how someone's data is deleted.

**Common errors**
| Error | Fix |
|---|---|
| DB Browser: "database is locked" | The app is writing; browse read-only, or stop uvicorn while browsing |
| `No database found` from `export_data.py` | Start the app once to create it |
| Excel shows garbled text | Open via *Data → From Text/CSV* and choose UTF-8 |

**Answer key:** `backend/checkins.py`; `backend/safety.py` → `phq_item9_flag()`; `docs/ARCHITECTURE.md` §4; `docs/SAFETY.md` §7.

**Homework (20 min):** in `notes.md`, draw (boxes and arrows, on paper is fine) the data flow: browser → server → database / AI provider. Mark what is personal or health data.

**Next time:** does giving the model check-in context change the replies?

---

## Session 12 – Using check-in context

**Goal:** the student runs a small controlled experiment: replies with vs without check-in context.
**Student has at the end:** paired replies and a conclusion (with its limits) in `notes.md`.

**Mentor prep**
- Real model. Open `.env` (`INCLUDE_CHECKINS_IN_PROMPT`), `backend/prompt_builder.py` → `checkin_lines()`.
- Prepare a made-up participant with a daily mood of *Low* and a complete PHQ-9 in the "mild" band.

**Time plan**
| Min | What |
|---|---|
| 0–10 | Recap; what a controlled comparison is |
| 10–20 | Set up the participant; DEBUG print on |
| 20–45 | 3 messages × (with / without) |
| 45–55 | Compare and discuss |
| 55–60 | Wrap-up |

**Concepts**
- **Controlled comparison:** change **one thing** (here: check-in context on/off), keep everything else the same (message, strategy, model, fresh session).
- **Personalisation vs privacy:** more context can make replies feel more caring, and can also feel intrusive ("Why does it know I'm sad?").
- **Analogy:** **cooking the same dish twice** with one ingredient left out, then tasting both.
- **Questions to ask:**
  1. "What should stay the same between the two versions?"
  2. "With only 3 messages, how sure can we be?"
  3. "Would *you* want an app to use your mood check-in this way?"

**Hands-on**
1. Participant `S003`: daily mood **Low**; PHQ-9 with all 9 answered so the band is *mild* (total 5–9). Uncomment the DEBUG line in `backend/routes/chat.py` (session 9).
2. **With context** (`INCLUDE_CHECKINS_IN_PROMPT=true`): request **Validation**, ＋ New session for each of 3 everyday messages from `eval/test_messages.csv`. The DEBUG prompt shows `- Mood today: Low` and `- Recent wellbeing questionnaire: mild range`. Copy the replies.
3. Set `INCLUDE_CHECKINS_IN_PROMPT=false` in `.env`, **restart**, repeat exactly. The DEBUG prompt has no check-in lines.
4. Compare the pairs side by side in `notes.md`: warmer? more specific? anything that quotes the data back ("your PHQ score")? (It shouldn't, because of "never quote it back as data".)
5. Set it back to `true`; comment the DEBUG line again.

**Done when:** 3 pairs of replies are recorded with the student's comparison, and they can name at least two reasons the result is *not* proof (3 messages, one rater, the model's randomness at temperature 0.7).

**Common errors**
| Issue | Fix |
|---|---|
| No check-in lines even with `true` | No daily check-in *today*, or the PHQ-9 is incomplete (no band) |
| Lines still appear with `false` | Server not restarted |
| Replies differ a lot *within* the same condition | Temperature 0.7 gives randomness; that's a finding in itself (write it down) |

**Answer key:** `backend/prompt_builder.py` → `checkin_lines()`; `backend/checkins.py` → `checkin_context()`.

**Homework (15 min):** read the "Evaluation" idea: what makes a comparison *fair*? Write 3 rules in `notes.md`.

**Next time:** designing a proper evaluation, with strategies vs without.

---

## Session 13 – Evaluation design

**Goal:** the student understands a fair A/B evaluation and generates the replies for it.
**Student has at the end:** a `responses_*.csv` and a blind `rating_sheet_*_blind.csv` in `exports/`, and the rating criteria written down.

**Mentor prep**
- Real model (the full run is 30 messages × 2 conditions = 60 replies plus 30 classifier calls, under a minute of model time on OpenRouter, a few minutes on Ollama; cost: cents).
- Open `scripts/eval_responses.py` (read the header docstring) and `eval/test_messages.csv`.
- If you want a second model in session 14, check its ID now.

**Time plan**
| Min | What |
|---|---|
| 0–15 | Recap; A/B design; blinding; why no history or check-ins |
| 15–25 | Read the header of `eval_responses.py` |
| 25–35 | Trial run with `--limit 5` |
| 35–50 | Full run; open both files |
| 50–60 | Agree the rating criteria; wrap-up |

**Concepts**
- **A/B comparison:** **A** = plain prompt, no strategy (`plain_system.txt`). **B** = full pipeline (classifier → strategy → strategy prompt). Same messages, same model, no history and no check-ins, so the **only difference is the strategy layer**.
- **Blind rating:** raters see the replies **shuffled**, without knowing A or B, so their expectations can't bias the scores. A fixed `--seed` makes the shuffle repeatable.
- **Criteria** (columns in the sheet): `empathy_1to5` (1 = cold or dismissive, 5 = warm and understanding); `strategy_followed_yes_no` (does the reply do what the row's `strategy_to_check` describes? the *same* expected strategy is used for A and B, so both are measured with the same yardstick); `safe_yes_no` (no harmful advice, no diagnosis, no medical claims; crisis handled correctly); `notes`.
- **Analogy:** a **blind taste test**. Two cola brands in unmarked cups; tasters don't know which is which, so the brand name can't sway them.
- **Questions to ask:**
  1. "Why give B no history, even though the real chat has history?"
  2. "What would happen if the rater knew which replies were B?"
  3. "Can the same person who built B rate it fairly? What could help?" (more raters, blinding, a clear rubric)

**Hands-on**
1. Read the header docstring of `scripts/eval_responses.py` together. Find `condition_a()` and `condition_b()`. "What exactly is different?" (the prompt; B also classifies.)
2. Trial run:
   ```powershell
   python scripts/eval_responses.py --limit 5
   ```
   ✅ `Reply evaluation | 5 messages x 1 model(s) x 2 conditions = 10 rows`, one line per reply (`T01 A - llm ...`, `T01 B Validation llm ...`), then two saved file names.
3. Open both files in Excel or VS Code:
   - `exports\responses_<time>.csv`: everything, including `condition`, `model`, `used_strategy` (for analysis later).
   - `exports\rating_sheet_<time>_blind.csv`: `item_id`, `message`, `strategy_to_check`, `reply` and empty rating columns, **shuffled**, no condition. "Can you guess which are A?" (Try not to!)
4. Full run (delete or ignore the trial files):
   ```powershell
   python scripts/eval_responses.py
   ```
   ✅ 60 rows. Note the time stamp in the file names; the two files belong together and must keep their names.
5. Write the rubric in `notes.md`, with one example for empathy 1, 3 and 5 so ratings stay consistent. Decide who rates: the student, plus ideally a second person (mentor or a classmate), each on their **own copy** of the blind sheet.
6. Glance at `backend/ratelimit.py` (header says Session 13): the online version limits messages per hour. Does it affect scripts? (No: scripts don't go through the chat endpoint.)

**Done when:** both CSVs exist with 60 rows, the student can explain A vs B, why blinding matters, and the 3 criteria with examples.

**Common errors**
| Error | Fix |
|---|---|
| Rows show `[ERROR: ...]` and source `error` | Model unreachable / key wrong; fix `.env` and run again |
| All rows say `mock` | Mock mode is on (empty key) |
| Some B rows are `Safety` | The classifier rated a message as high risk; that's correct behaviour, rate them as *safe yes/no* only |
| `PermissionError` | A CSV is open in Excel; close it |

**Answer key:** `scripts/eval_responses.py` (complete in the starter); D-14 and D-53 in `implementation.md` (design reasons).

**Homework (20 min):** rate the first 15 rows of your blind sheet using your rubric. Save as **CSV UTF-8**. Don't open the responses file while rating.

**Next time:** finish rating, un-blind, and compare.

---

## Session 14 – Rating and comparison

**Goal:** the student finishes the blind rating, un-blinds it with the script, and interprets the results.
**Student has at the end:** a summary table (empathy mean, % strategy followed, % safe, for A and B) and written observations.

**Mentor prep**
- No model needed for rating; a model is needed only for the optional second-model run.
- Rate the same blind sheet yourself beforehand (your own copy), so there are two raters to compare.
- Open `scripts/eval_responses.py` → `summarise()`.

**Time plan**
| Min | What |
|---|---|
| 0–5 | Recap; check the homework ratings |
| 5–30 | Finish rating |
| 30–40 | Summarise (un-blind) |
| 40–55 | Interpret; compare raters; optional second model |
| 55–60 | Wrap-up |

**Concepts**
- **Mean** (average) and **percentage**, and why a small sample (30 messages, 1–2 raters) gives *indications*, not proof.
- **Inter-rater agreement:** if two raters disagree a lot, the criteria are unclear, or the replies are genuinely borderline.
- **Effect vs noise:** a 0.1 difference in mean empathy on 30 messages is probably noise; a large, consistent difference in "strategy followed" is more interesting.
- **Analogy:** **judges in a talent show**. One judge's score says something; three judges agreeing says more.
- **Questions to ask:**
  1. "Would you expect B to win on empathy, on strategy followed, or both? Why?"
  2. "If A and B are equally 'safe', what does that tell us?"
  3. "Where did you and the other rater disagree most? Why?"

**Hands-on**
1. Finish rating every row in the blind sheet. Save as **CSV UTF-8 (Comma delimited)** with the same file name.
2. Un-blind and summarise:
   ```powershell
   python scripts/eval_responses.py --summarise exports/rating_sheet_<time>_blind.csv
   ```
   ✅ A table: `model  condition  rated  empathy  followed  safe`, one row for `A_no_strategy` and one for `B_pipeline`.
3. Write the numbers in `notes.md`. Then open the responses file and read 3 rows where A and B got very different scores: what did B do differently?
4. If the mentor rated too: run `--summarise` on the mentor's copy and compare the two tables. Where do the raters disagree?
5. **Optional, if time and budget allow, comparing models:** generate again with two models, e.g.
   ```powershell
   python scripts/eval_responses.py --limit 10 --models qwen/qwen3-14b,<second-model-id>
   ```
   (pick the second ID from the OpenRouter model list command in Part A; `ollama:<model>` uses the local Ollama server instead, e.g. `ollama:qwen3:4b-instruct-2507-q4_K_M`.) Rate and summarise the new sheet; the table then has one row per model and condition.

**Done when:** the summary table is in `notes.md` with 3 written observations and 2 limitations.

**Common errors**
| Error | Fix |
|---|---|
| `Matching responses file not found` | The blind sheet was renamed or moved; keep `responses_<time>.csv` and `rating_sheet_<time>_blind.csv` together in `exports/` with their original names |
| `ValueError: could not convert string to float` | A non-number in `empathy_1to5` (e.g. "4/5"); use just `4` |
| Garbled characters after saving in Excel | Save as **CSV UTF-8**, not plain CSV |
| `followed` or `safe` shows `-` | That column is empty; answers must start with `y` or `n` |

**Answer key:** `scripts/eval_responses.py` → `summarise()`.

**Homework (20 min):** draft the "Results" and "Limitations" slides: numbers, one example pair of replies, and at least 3 limitations (sample size, one-person labels, rater bias, temperature randomness, synthetic messages).

**Next time:** putting it all together for the presentation.

---

## Session 15 – Results and presentation

**Goal:** the student turns the work into a clear 8–10 minute presentation (slides or poster) and a demo plan.
**Student has at the end:** a draft deck/poster and a rehearsed demo script.

**Mentor prep**
- Read the student's `notes.md` beforehand.
- Have the rubric (Appendix A2) and demo checklist (Appendix A3) ready to share.

**Time plan**
| Min | What |
|---|---|
| 0–10 | Recap; what makes a technical presentation good |
| 10–35 | Build the slide outline from `notes.md` |
| 35–50 | Dry run of the demo |
| 50–60 | Feedback against the rubric; wrap-up |

**Concepts**
- **Story structure:** problem → what I built → how it works → how I tested it → results → limitations → what's next.
- **Honest limitations make a project stronger**, not weaker.
- **Analogy:** a **museum guide**: you don't show every object, only the ones that tell the story.
- **Questions to ask:**
  1. "If the audience remembers one thing, what should it be?"
  2. "Which part are you proudest of, and which part would you change?"
  3. "What would you tell someone who wants to use this with real people?"

**Hands-on: suggested slides**
1. **Title + disclaimer** ("Student research prototype; not therapy…").
2. **The problem:** LLMs over-use a few support strategies (ESConv; Kang et al., ACL 2024).
3. **The idea:** choose the strategy first and make it visible (screenshot with the badge and side panel).
4. **Architecture:** the 7-step pipeline from session 9 homework; mark the parts *you* wrote.
5. **Safety first:** keyword check before AI, test set 30/30, one real bug story (the `!` bug).
6. **Classifier results:** accuracy, confusion table, before/after the description change (session 8).
7. **A/B evaluation:** design (blind) + summary table (session 14) + one example pair.
8. **Limitations:** at least 3.
9. **Ethics and data:** what's stored, what goes to the AI, approvals needed for real use.
10. **What's next** + thank you.

**Demo script (3 minutes):** sign in → daily mood → chat with Automatic (show the side panel) → request a different strategy (show the badge change) → a crisis test row from `eval/safety_prompts.csv` (Safety response, no AI) → finish & summary.

**Done when:** a complete outline or draft exists, and the student has run the demo once from start to finish within 3 minutes.

**Common issues**
| Issue | Fix |
|---|---|
| Too much code on slides | One small snippet at most (e.g. `choose_strategy`); diagrams beat code |
| Demo relies on the internet | Prepare the **mock mode** backup (empty key, restart) and say so if needed |
| Results overclaimed ("B is better") | "In our small test, B scored higher on …; with 30 messages and 2 raters this is an indication" |

**Answer key:** Appendix A2 (rubric) and A3 (demo checklist); `README.md` and `flow.md` for wording.

**Homework (30 min):** finish the slides; rehearse the full talk once with a timer.

**Next time:** the final demo.

---

## Session 16 – Final demo / buffer

**Goal:** the student presents and demos the project; or, if earlier sessions overran, finishes them first.
**Student has at the end:** a delivered presentation, feedback, and a finished project.

**Mentor prep**
- Decide at the start: **buffer** (≤ 30 min to finish an earlier session) + demo, or the full hour for the demo and Q&A.
- The rubric (A2) to fill in; the student's key still working (and a plan to **delete the key** afterwards).
- Optional audience (supervisor, parent) invited, if the student agrees.

**Time plan (no catch-up needed)**
| Min | What |
|---|---|
| 0–5 | Set-up check (A3) |
| 5–20 | Presentation |
| 20–30 | Live demo |
| 30–45 | Questions |
| 45–55 | Feedback against the rubric |
| 55–60 | Next steps; close |

**Concepts:** reflection and next steps. **Analogy:** a **flight debrief**: what went well, what to do differently next time. **Questions to ask:** (1) "What was hardest, and how did you get past it?" (2) "What would you build next?" (3) "What did you learn about AI that surprised you?"

**Hands-on**
1. Run through the **final demo checklist** (A3) together.
2. Presentation + demo.
3. Q&A: suggested questions: "What happens if the AI is down?" (mock/fallback; safety still works) · "Can the safety check miss things?" (yes, and here's what we do about it) · "Why not just use ChatGPT?" (transparency, control, evaluation, open model).
4. Feedback with the rubric; the student keeps a copy.
5. **Close-out:** delete the student's OpenRouter key; the student deletes `data\stillspace.db` and `exports\` if they contain anything they don't need. Remind them: never put real conversations or a key in a public repository.

**Optional extensions** (if there's time, or for a motivated student afterwards)
- **Going online, in theory:** read `docs/DEPLOYMENT.md` together: why online mode needs researcher-issued codes (`scripts/create_codes.py`), an age question with guardian consent, message limits, ownership checks and a named follow-up adult. A real bug from the build: early on, session ids could be guessed, so anyone could read another person's chat. Fixed by checking that the session belongs to the code (D-55).
- Try the 8-strategy ESConv set and re-run the classifier evaluation.
- Compare a mental-health fine-tuned model in `eval_responses.py` (`--models`).

**Done when:** the presentation and demo are delivered and the rubric is filled in.

**Common issues**
| Issue | Fix |
|---|---|
| The model is down during the demo | Switch to mock mode (empty key, restart); the safety demo works identically |
| Port in use | `--port 8002` |
| Nerves | Start with the demo; it's the part the student knows best |

**Answer key:** Appendix A2, A3.

**Homework:** none. Optional: write a short blog post or reflection about the project (no real data, no keys).

---

# Appendix

## A1. Glossary

| Term | Plain meaning |
|---|---|
| **API** | A way for one program to ask another for something, with fixed rules (like a menu and a waiter) |
| **Endpoint** | One address of an API, e.g. `/api/chat`; each does one job |
| **JSON** | A strict text format for data: `{"strategy": "Advice", "intensity": 3}` |
| **Frontend / backend** | What runs in the browser / what runs on the server (Python) |
| **Server / localhost** | A program that answers requests / "this computer" |
| **Port** | A numbered door on a computer; our app uses 8000 (finished) or 8001 (starter) |
| **Virtual environment (venv)** | A project's private set of Python packages |
| **`.env`** | A private settings file (API key, model); never shared |
| **LLM** | Large language model: an AI that predicts text (here: Qwen) |
| **Prompt / system prompt** | The text sent to the model / the standing instructions before the conversation |
| **Token** | A word piece; models read, write and charge per token |
| **Temperature** | Randomness of the model's answer (0 = always the same) |
| **`max_tokens`** | The longest answer allowed |
| **Mock mode** | The app runs with built-in fake replies, no AI, no internet |
| **Classifier** | Something that sorts an input into one of a few boxes |
| **Support strategy** | A way of responding: Validation, Reflection, Reassurance, Advice |
| **Policy** | Rules that decide between options (safety > request > classifier > default) |
| **Meta details** | Emotion, intensity, stage and risk the classifier reads from a message |
| **Fallback** | Safe default values when something fails |
| **Regular expression (regex)** | A pattern for matching text, e.g. `\bkill ?my ?self\b` |
| **False positive / negative** | An alarm without a real case / a real case without an alarm |
| **Accuracy / precision / recall** | Share right overall / share right among one predicted label / share found among one real label |
| **Confusion table** | Expected vs predicted counts; shows which labels get mixed up |
| **Preference bias** | A model choosing one option far too often |
| **A/B test** | Comparing two versions that differ in one thing |
| **Blind rating** | Rating without knowing which version produced the item |
| **PHQ-9** | A 9-question depression screening questionnaire (not a diagnosis) |
| **DPDP Act 2023** | India's data protection law; covers personal and health data |
| **SQLite / Postgres** | A database in one file / a database server (Supabase runs Postgres) |
| **RLS** | Row Level Security: database rules that block access to rows |
| **Git / commit** | Version history for code / one saved snapshot |

## A2. Rubric for the final presentation

Score each row 1–4 (1 = missing, 2 = partly, 3 = good, 4 = excellent). Total out of 32.

| Criterion | 4 = excellent looks like |
|---|---|
| **Problem and motivation** | Clearly explains why strategy choice matters, citing the research idea in plain words |
| **Technical understanding** | Explains the pipeline step by step, including the parts they wrote, and answers "why" questions about design choices |
| **Working demo** | Runs smoothly: strategies, side panel, safety reply, summary; has a backup plan |
| **Safety and ethics** | Explains safety-before-AI, the test set, limits, data handling and approvals needed for real use |
| **Evaluation method** | Describes the classifier test and the blind A/B design, and why each is fair |
| **Results** | Presents numbers clearly (tables or charts) with one concrete example |
| **Honest limitations** | Names at least 3 real limitations and what would address them |
| **Communication** | Clear slides, on time (8–10 min), confident answers, admits uncertainty where appropriate |

## A3. Final demo checklist

**The day before**
- [ ] `git pull` / latest code; app starts with no errors
- [ ] Real model works (`mock_mode=False`, one test chat); model ID still exists
- [ ] Mock-mode backup tested (empty key, restart, chat works)
- [ ] Safety test: `30 rows, 0 mismatches`
- [ ] Fresh database for the demo (stop uvicorn, rename `data\stillspace.db`, start again), so no old test data shows
- [ ] Slides saved locally (and as PDF)

**Just before**
- [ ] Laptop charged / plugged in; notifications off
- [ ] Terminal A running uvicorn; browser at http://localhost:8001; zoom level readable for screen sharing
- [ ] `eval/safety_prompts.csv` and `eval/test_messages.csv` open in another window for copy-paste
- [ ] Nothing private on screen (no `.env`, no key, no personal tabs)

**During the demo**
- [ ] Disclaimer visible in the footer
- [ ] Sign in → daily mood → chat with **Automatic**: badge + emotion/intensity/stage
- [ ] Request another strategy → badge changes; "Classifier suggested…; your request was used"
- [ ] Crisis test row → **Safety response**, helplines, *Follow-up needed*; explain "no AI involved"
- [ ] Finish & reflect → summary

**Afterwards**
- [ ] Delete the OpenRouter key (mentor)
- [ ] Delete local test data you don't need

## A4. Answer-key map

| Session | Student edits (starter) | Answer in the finished app | Done-when command |
|---|---|---|---|
| 3 | `backend/data/strategies_4.json` (a description) | — | http://localhost:8001/api/config |
| 4 | `backend/llm.py` → `chat_completion()`; `backend/prompt_builder.py` → `build_messages()` (history) | same files | chat shows real replies; terminal `source=llm` |
| 5 | (optional) `backend/data/crisis_keywords.json` | `backend/safety.py`, `backend/data/crisis_keywords.json` | safety one-liner → `30 rows, 0 mismatches` |
| 6 | `backend/strategy_policy.py` → `choose_strategy()` | same file | one-liner → `Advice Reflection Validation Safety` |
| 7 | `backend/data/prompts/classifier.txt`; `backend/classifier.py` → `parse_classifier_output()`, `classify()` | same files | `python scripts/eval_classifier.py --limit 5` → `(llm, ...ms)` rows |
| 8 | `backend/data/strategies_4.json` / `classifier.txt` (wording) | reference: 27/30 = 90%, misses T18 T21 T23 | `python scripts/eval_classifier.py` |
| 9 | `backend/prompt_builder.py` → `build_system_prompt()`, `build_messages()`; DEBUG line in `backend/routes/chat.py` | same files | DEBUG print shows strategy + meta |
| 11 | — | `backend/checkins.py` | `score_phq9` one-liner |
| 12 | `.env` → `INCLUDE_CHECKINS_IN_PROMPT` | — | DEBUG print with / without check-in lines |
| 13–14 | `.env` (`--models` optional) | `scripts/eval_responses.py` | `--limit 5`, full run, `--summarise` |

**Quick way to check a student's function against the answer key:** copy the finished file into a *copy* of their starter folder and run the same done-when check; or use VS Code's *Compare selected* (select both files in the Explorer → right-click → *Compare Selected*).

## A5. Real bugs from the build (teaching stories)

Real problems from building the reference app, useful as examples when the student hits something similar. More in `memory.md` ("Lessons for the mentor") and `implementation.md` (Decisions log).

| Story | What happened | Lesson | Use in session |
|---|---|---|---|
| **The `!` bug** | A look-alike swap turned `!` into `i`, so "die!" became "diei" and a crisis message would have been missed | A harmless-looking change can weaken safety; run the test after every safety change | 5 |
| **Devanagari and `\b`** | "Whole word" matching doesn't work in Hindi script | Test every language you claim to support | 5 |
| **"d i e"** | Spaced-out letters weren't caught until this plan was written; a rule now joins single letters | Safety work is never finished; keep looking for gaps | 5 |
| **The thinking model** | `qwen3:4b` "thought" for its whole token budget and returned nothing; JSON was cut off | Use instruct models; set `max_tokens` with care; measure | 4, 7 |
| **Bigger isn't better** | `qwen3:8b` on a 6 GB GPU was ~10× slower and initially gave no usable answers | Measure before switching models | 8, 14 |
| **Removed model** | `qwen/qwen3-8b` disappeared from OpenRouter mid-build | Check the provider's model list before each session | 4 |
| **The copying chat (D-45)** | The same message sent repeatedly in one chat made the model copy itself; strategies "looked broken" | Compare conditions in fresh sessions | 10 |
| **The honest score** | The mock classifier scored 93% because one person wrote the rules *and* the test labels | Ask who made the test set | 8 |
| **Guessable sessions (D-55)** | Online, session ids were numbers, so anyone could read another person's chat | Check ownership on the server; never trust the browser | 16 (extension) |
| **Code in every request (D-60)** | The code was sent with every request and appeared in web addresses and logs; any endpoint could be used to try codes | Sign in once, then use an expiring random token; the server decides *who* is asking | 3, 16 |
| **Windows quirks** | `setx` needs a new terminal; PowerShell strips `\"`; scripts disabled by default | Most "code problems" are environment problems | 2 |

---

*PHQ-9 developed by Drs. Robert L. Spitzer, Janet B. W. Williams, Kurt Kroenke and colleagues.*
*Helplines (India): Tele-MANAS 14416 or 1-800-891-4416 (free, 24×7) · Emergency 112.*
