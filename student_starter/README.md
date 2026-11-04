# Stillspace: student starter

This is the **complete Stillspace app** with the five "brain" functions left for you to write, one or two per mentoring session. The web page, database, check-ins and safety check are finished and work from the first minute: you start in **mock mode** and replace placeholders step by step.

> **Safety first.** This is a research prototype, not therapy. Never test it with your own real problems; use the prepared messages in `eval/`. If anything real comes up, stop and tell your mentor. Helplines: **Tele-MANAS 14416** (free, 24x7) · **Emergency 112**.

## Run it

Set up Python, the venv and the packages as in the main project's `docs/SETUP.md` (the commands are the same), but **inside this `student_starter` folder**:
```powershell
cd student_starter
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn backend.main:app --reload --port 8001
```
Open **http://localhost:8001** (port 8001, so it can run next to the finished app on 8000). Sign in with any code, e.g. `S001`.

✅ What works straight away: consent, check-ins, PHQ-9 scoring, mood, the chat in mock mode, the **safety reply** for crisis messages, reflection and summary.
⏳ What's a placeholder until you write it: real AI replies, the classifier's choice, your requested strategy, the strategy-aware prompt and conversation memory. The terminal prints `[TODO Session N] ...` whenever a placeholder is used.

## Your TODOs

| Session | File → function | What you build | Done when |
|---|---|---|---|
| 4 | `backend/llm.py` → `chat_completion()` | One call to the AI model (any OpenAI-compatible provider) | With a key or Ollama in `.env`, the chat shows real replies; terminal `source=llm` |
| 4 | `backend/prompt_builder.py` → `build_messages()` | Add the conversation history (memory) | The model remembers what you said two messages ago |
| 5 | `backend/safety.py` → `check_message()` (*already works*) | Read it, run the safety test, discuss limits | `30 rows, 0 mismatches` |
| 6 | `backend/strategy_policy.py` → `choose_strategy()` | Request beats classifier; default = first strategy | Choosing "Advice" makes the badge say Advice |
| 7 | `backend/classifier.py` → `classify()` + `parse_classifier_output()` and `backend/data/prompts/classifier.txt` | The classifier prompt and safe JSON parsing | `python scripts/eval_classifier.py` shows `source=llm` and an accuracy |
| 9 | `backend/prompt_builder.py` → `build_system_prompt()` + `build_messages()` | Strategy instruction + emotion/stage + check-ins in the prompt | Replies change with the strategy; the DEBUG print shows the full prompt |

Each function's docstring lists the steps and hints. Try the steps yourself first; look at the hints when you're stuck. Your mentor has the finished version (the main project folder) as the answer key.

## Useful commands

```powershell
# Safety test (must always say 30 rows, 0 mismatches)
python -c "import csv; from backend.safety import check_message; rows=list(csv.DictReader(open('eval/safety_prompts.csv', encoding='utf-8-sig'))); bad=[r for r in rows if check_message(r['message']) != (r['expect']=='crisis')]; print(len(rows), 'rows,', len(bad), 'mismatches')"

# Classifier accuracy (after Session 7)
python scripts/eval_classifier.py

# Replies with vs without strategies (Session 13)
python scripts/eval_responses.py --limit 5
```

## Rules for your code
- Plain functions, short and clear; a comment says **why**, not what.
- Prompt text stays in `backend/data/prompts/*.txt`, not in Python strings.
- **Never weaken the safety check or remove the `"Safety"` line in `choose_strategy`.**
- Your `.env` (API key!) and `data/*.db` are never committed.
