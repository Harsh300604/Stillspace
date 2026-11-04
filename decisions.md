# Stillspace: Decisions Record

> **Who this is for:** the mentor (and later the student) who wants to understand *why* the app is built the way it is.
> **How it relates to other files:** `implementation.md` keeps the short, numbered **Decisions log** (D-01, D-02, …) required by the spec. This file explains the same decisions in plain language, grouped by topic, with the alternatives considered and a teaching note. The IDs match, so you can jump between the two.
> **Updated:** after every phase.

Each entry has:
- **Decision**: what we chose
- **Why**: the reason
- **Alternatives**: what else was considered
- **Teaching note**: what this can teach the student, or what to watch for in a session

---

## 1. Ground rules that shaped everything

| Rule | Where it came from | Effect on the code |
|---|---|---|
| The spec (`Stillspace_Build_Specification.docx`) is the source of truth | Developer | When the spec is silent, choose the simplest option and log it |
| Keep the mockup's visual design | Spec section 12 | The CSS is copied byte for byte; additions live in one marked block at the end of `styles.css` |
| Never weaken safety | Spec section 11.5 and the developer | Safety runs before any AI call and works in mock mode and offline |
| Student-friendly code | Spec section 13 | Plain functions, short files, comments that explain *why*, no ORM, no frameworks beyond the spec |
| Build one phase at a time, and the developer tests each | Developer | Every phase ends with numbered manual checks in `implementation.md` |
| Nothing installed or cached on C: | Developer's C: drive was nearly full | See section 2 |

---

## 2. Developer laptop and storage (D: drive)

### All installs and caches on D: (D-02, D-03, D-20)
- **Decision:** project in `D:\CreatED-cloud\stillspace`, the venv inside it (`.venv`), pip cache `D:\cache\pip`, temp files `D:\cache\tmp`, Ollama models `D:\ollama\models`.
- **Why:** C: had about 48 GB free and was nearly full. The code only uses paths relative to the project root (`pathlib`), so it works in any folder.
- **Alternatives:** `D:\Projects\stillspace` as the spec suggests. The developer preferred an existing folder, and nothing else changes.
- **Teaching note:** the student's `docs/SETUP.md` uses normal default locations; the D: rule was only for the developer's laptop. It's a good moment to explain *environment variables* (`setx PIP_CACHE_DIR …`).

### `tzdata` added as a sixth package (D-04)
- **Decision:** `requirements.txt` has the spec's five packages **plus `tzdata`**.
- **Why:** Windows has no built-in timezone database. Without `tzdata`, `ZoneInfo("Asia/Kolkata")` crashes, and "daily" check-ins depend on the local date.
- **Alternatives:** hard-code +05:30. That would silently ignore the `APP_TIMEZONE` setting.
- **Teaching note:** a real example of "it works on my Mac/Linux but not on Windows".

### PowerShell quirks (D-01, D-31)
- **Decision:** the venv activation command is `.\.venv\Scripts\Activate.ps1` (the spec had a typo). Every `python -c "…"` command in the docs uses only **single quotes** inside.
- **Why:** Windows PowerShell 5.1 strips `\"` before passing text to Python, which caused a `SyntaxError` during Phase 3 testing.
- **Teaching note:** if a student copies a command and gets a strange `SyntaxError`, check the quotes first.

---

## 3. Choosing and running the AI model

### What happened, in order
1. The spec's default was **`qwen/qwen3-8b` on OpenRouter**.
2. Phase 4 check 0 showed that **this model is no longer listed on OpenRouter** (K-02).
3. The developer did not want to spend money while building and testing, so we chose **Ollama on the laptop** (free and local) for development (D-37).
4. The Ollama tray app kept saving models to **C:**, ignoring `OLLAMA_MODELS`. Fix: start the server by hand with `$env:OLLAMA_MODELS = "D:\ollama\models"; ollama serve`.
5. The Ollama tag `qwen3:4b` turned out to be an **always-thinking** build: it ignored every "don't think" switch. Fix: use the **instruct** build `qwen3:4b-instruct-2507-q4_K_M` (D-39).

### Two setups, same code (D-37, D-38)
- **Decision:**

  | | Developer (building and testing) | Student and mentor (after handoff) |
  |---|---|---|
  | Provider | Ollama on the laptop (free) | OpenRouter (paid credits, with a spending limit) |
  | Model | `qwen3:4b-instruct-2507-q4_K_M` (GPU: RTX 4050, 6 GB) | `qwen/qwen3-14b` (default in `.env.example`) |
  | `.env` | `LLM_BASE_URL=http://localhost:11434/v1`, `LLM_API_KEY=ollama` | OpenRouter URL and their own key |

- **Why:** the spec assumes a hosted API and **no GPU** on the student's laptop (8 GB of RAM is tight for a local model). The developer wants zero cost. Both providers speak the same "OpenAI-compatible" API, so only three `.env` lines change.
- **Alternatives:** OpenRouter `qwen/qwen3.5-9b` (closest to 8B, but unknown thinking behaviour), `qwen/qwen3-32b`, free `:free` models (none were listed for Qwen; they come with daily limits and possible prompt logging).
- **Teaching note:** a great example of configuration vs code: swapping providers needs no code change. For the evaluation (Phase 9) the student must use **one model consistently** and name it in the report, because different models reply differently.

### Switching off "thinking" (D-15, D-33, D-39)
- **Decision:** `llm.py` asks each provider not to think: `{"reasoning": {"enabled": false}}` for OpenRouter, `{"think": false}` for Ollama, nothing for unknown providers, and `/no_think` for Qwen3 models. It **always** strips thinking text afterwards, including a lone `</think>` without an opening tag.
- **Why:** Qwen3 models can write long hidden reasoning. Tests on the developer's Ollama 0.40.14 showed three different behaviours (ignored the switch; moved the thinking into a separate field; put the thinking inside the reply). Thinking also uses up the 300-token reply limit and makes replies slow.
- **Teaching note:** shows why you test with the real model and never trust that a setting "just works". The tests are recorded in D-39.

### Timeout as a setting (D-36)
- **Decision:** `LLM_TIMEOUT_SECONDS` in `.env` (default 120).
- **Why:** the first reply from a local model can take a while as it loads into memory.

### Mental-health fine-tuned comparison model (D-23, K-04): still open
- Needed before Phase 9. It will probably run on Ollama like the dev model. If the two models are on different providers, `--models` in `eval_responses.py` will accept a provider prefix.

---

## 4. Safety

### Two independent nets (spec 11.5; D-22)
- **Decision:** (1) a **keyword/regex check runs before any AI call**: on a match, the AI is never called and a fixed crisis reply with **Tele-MANAS 14416 / 1-800-891-4416** and **112** is returned; (2) the classifier's `risk: "high"` triggers the same fixed reply (Phase 7).
- **Why:** the developer asked for a safety layer that does not depend on the AI model. A model can be offline, wrong, or not called at all in mock mode.
- **Phase 5 strengthening (built, D-40):**
  - **Normalise first:** lower case; apostrophes removed (`can't` = `cant`); look-alike digits swapped inside words (`k1ll`, `$uicide`); separators between letters removed (`s.u.i.c.i.d.e`); stretched letters checked two ways (`dieee`, `killlll`).
  - **`!` is never swapped:** "die!" would have become "diei" and slipped through. *Lesson: a tidy-looking improvement can weaken safety, so always re-run the test set.*
  - **Rules in a JSON file** with ids: 36 phrases (whole words; Devanagari as plain text) and 13 regex patterns for flexible wording (English, Hinglish, Devanagari).
  - **Every match is logged** with its rule id (terminal and `meta_json`), so false alarms can be reviewed later.
  - **Test set:** 30 synthetic rows (20 crisis, 10 tricky normal), all correct; 25 more unseen crisis phrasings were also caught.
  - **Known false positive kept:** "suicide squad". No exception was added, because an exception could hide a real crisis.
- **Alternatives considered:** asking the AI model to detect crises (rejected as the *only* net: it can be offline, wrong, or not called in mock mode; it is used as the *second* net in Phase 7); a large off-the-shelf toxicity model (not in the spec's package list, and not explainable to a student).
- **Display:** the fixed reply in the mockup's warm follow-up colours, the badge "Safety response", tap-to-call helpline links, and "Follow-up needed" in the risk panel for the rest of the session.
- **Teaching note:** discuss false positives ("this exam is killing me") versus false negatives (indirect phrasing). The student never writes crisis test messages: the developer supplies synthetic ones.

### AI errors never touch safety (D-32)
- **Decision:** if the AI model fails (wrong key, no internet), the user sees a friendly error with **Retry** and nothing is stored. If the model returns an empty reply, a gentle fallback reply is shown.
- **Why:** the safety check happens before the AI call, so a broken model cannot block a crisis reply.

### PHQ-9 item 9 (D-30, D-40)
- **Decision:** item 9 > 0 sets `item9_flag`, shows the follow-up notice **with the helpline numbers** (and the follow-up contact if set), and turns the risk indicator to "Follow-up needed", **independent of the total score**. The rule lives in `safety.phq_item9_flag()` since Phase 5.
- **Never** shown: a computed risk percentage.

---

## 5. Data and privacy

### Participants are codes, not people (D-09)
- **Decision:** a participant is a code like `P001` (3–20 letters or digits, stored upper-case). No passwords, names or email addresses.
- **Why:** spec section 4. Upper-casing avoids `p001` and `P001` becoming two people.

### What is stored, and how (D-10 to D-13, D-24, D-25, D-28)
- Unanswered questions are **absent keys**, never 0, so a skipped PHQ item is "unknown", not "no symptoms".
- The PHQ-9 total and band exist **only when all 9 items are answered**. The **server** re-scores it, even though the browser shows a live score.
- Daily check-in: **one row per local day**; later saves merge into it. Finishing with everything skipped still counts as done ("completion is an explicit action").
- "Today" uses `APP_TIMEZONE` plus a per-participant **demo offset** (for the preview-day buttons).
- Conversation memory: the last **6 messages** (`HISTORY_TURNS`) are sent to the model.
- **Teaching note:** these are good data-ethics discussions (Session 11). The DB file is git-ignored, and so are exports.

---

## 6. Frontend (mockup to working app)

- **Kept:** layout, colours, fonts, dark mode, text size, mobile layout. Verified automatically: computed styles are identical to the mockup.
- **Changed (spec 12 only):** a participant code field; accurate wording (no "scripted", "nothing is stored" or "no AI"); strategy lists from the server; saving check-ins; real chat; a disclaimer under every step; a "Mock mode" tag in the header (D-35); "Signed in as P001 / Switch participant".
- **Routing (D-26, D-27):** "Continue →" opens whatever check-in is due (setup → daily → two-week → chat); "Skip to chat →" stays because check-ins are optional. A refresh keeps you signed in.
- **Reply badge (D-34):** until Phase 7 it shows the source ("Mock reply", "AI reply" or "Fallback reply"); from Phase 7 it shows the strategy used.
- **Teaching note:** every change in `app.js` is marked `CHANGED:`, so a student can compare it with the original mockup.

---

## 7. The strategy classifier (Phase 6)

### Prompt-based classifier (D-21, D-41)
- **Decision:** one AI call (temperature 0) reads the new message plus recent history and answers with JSON: strategy, emotion, intensity, stage, risk, confidence, rationale. The prompt lives in `prompts/classifier.txt`.
- **Why:** spec 11.3, and the developer's suggestion to start with prompt-based classification.
- **Alternatives:** a trained DistilBERT/DeBERTa classifier (a stretch idea: needs labelled data such as ESConv, plus training time); keyword rules only (that is the mock classifier: fine offline, but shallow).

### Never trust the model's JSON (D-41)
- **Decision:** the parser removes thinking text and code fences, takes the first `{...}`, keeps numbers in range, maps unknown names to safe defaults and validates the result with pydantic. If that fails: one retry, then fixed defaults (`classifier unavailable`).
- **Why:** small local models often add chatty text or slightly wrong values. The chat must never crash because of a badly formatted answer.
- **Safety detail:** a risk value the code doesn't recognise (e.g. "medium") is treated as **high**. The spec says "when unsure between low and high, choose high".
- **Teaching note:** Session 7 can show the 13 messy answers the parser was tested with (code fences, `<think>`, "intensity": 9 …), a nice lesson in defensive programming.

### Measuring it honestly
- `scripts/eval_classifier.py` prints accuracy, per-strategy precision/recall, a confusion table and the **preference-bias check** (how often each strategy is predicted).
- The 30 test messages are synthetic and labelled for the 4-strategy set.
- **Teaching note:** the mock classifier scores 93% only because the same person wrote the rules and the test messages. A good discussion of overfitting and test-set honesty (Session 8).
- **First real result (D-42):** `qwen3:4b-instruct` on Ollama scored **27/30 = 90%** with 30/30 valid JSON and no preference bias. The 3 misses were all "Reassurance" messages that the model read as "Validation"/"Reflection" (self-criticism phrased as a feeling).
- **Decision: no tuning on the test set.** The misses become the Session 8 exercise: the student edits strategy descriptions, re-runs the script and discusses whether the improvement would hold on *new* messages.
- **Confidence isn't trustworthy:** the model said 0.95+ even when wrong, so the app never uses it to make decisions.

---

## 8. Scope decisions

- **Classifier (D-21):** prompt-based with Qwen. A trained DistilBERT/DeBERTa classifier is a documented **stretch idea only** (spec section 3 puts it out of scope; 30 test messages are too few to train on; the ESConv dataset would be the source).
- **Extra checks (D-19):** some phases have extra checks marked "(Extra)". All the spec's checks are kept.
- **Plain prompt reused (D-14):** Phase 4's no-strategy prompt is also "condition A" in the Phase 9 evaluation.

---

## 9. Changelog of this file

| Date | Phase | Change |
|---|---|---|
| 4 Nov 2026 | after Phase 4 | File created; covers D-01 to D-39 |
| 4 Nov 2026 | Phase 5 | Safety section updated (D-40) |
| 4 Nov 2026 | Phase 6 | Classifier section added (D-41); first real result and no-tuning decision (D-42) |
