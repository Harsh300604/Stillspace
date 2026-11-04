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
- **Bigger model tried and rejected (D-43):** `qwen3:8b` produced cut-off JSON (it was still thinking) and took 35–51 s per message, because it doesn't fit fully in the 6 GB GPU. The dev setup stays on `qwen3:4b-instruct` for both jobs. The code now sends `/no_think` to hybrid Qwen3 models even when the prompt is a single user message, which is also needed for the handoff model `qwen/qwen3-14b`.
- **Confidence isn't trustworthy:** the model said 0.95+ even when wrong, so the app never uses it to make decisions.

---

## 8. Strategy-aware replies (Phase 7)

### The pipeline, in order (spec 5; D-44)
1. **Keyword safety**: on a match, fixed reply, no AI at all.
2. **Classifier**: strategy, emotion, intensity, stage, risk (it sees the recent history).
3. **Classifier risk** `high` → the same fixed reply (`safety_flag="classifier"`). The second safety net.
4. **Strategy policy**: safety > the user's request > the classifier's suggestion > the first strategy in the file.
5. **Prompt builder**: `system.txt` + the strategy's instruction + emotion/intensity/stage + check-in lines + history.
6. **Reply**: model (or the mock reply for that strategy).
7. **Store everything**: requested, classified and used strategy, plus the classifier's meta, on both messages.

### What goes into the prompt (privacy)
- **Only** today's mood ("Mood today: Low") and the latest **complete** PHQ-9 **band** ("moderate range"), and only when `INCLUDE_CHECKINS_IN_PROMPT=true`.
- **Never** the date of birth or individual PHQ answers. Verified by inspecting every request a test model server received.
- **Teaching note (Session 12):** toggling `INCLUDE_CHECKINS_IN_PROMPT` and comparing replies is a hands-on way to discuss what data an AI really needs.

### Explainability panel
- Under "Currently used by model": the strategy, then "Emotion · intensity · stage". If the user's request overrode the classifier: "Classifier suggested X; your request was used."
- **Badges stay honest:** a fallback reply shows "Fallback reply", not a strategy, because no strategy shaped it.

### Comparing strategies needs separate conversations (D-45)
- In the developer's first check, the same message sent four times in **one** conversation made the 4B model repeat its earlier reply word for word for "Reflection". The history outweighed the new strategy instruction.
- **Decision:** compare strategies in **fresh sessions**. This also applies to the Phase 9 evaluation script, which classifies and replies to each test message independently.
- **Teaching note:** a nice example of how a test set-up can create a "bug" that isn't in the code.

### A gap found while testing
- "I just want to sleep and never wake up" slipped past the keywords. It would only have been caught by the classifier's risk check. A keyword rule was added, so the deterministic net catches it too. *Lesson: write tests for indirect phrasings, not only the obvious ones.*

### Ending a session and the summary (Phase 8, D-52)
- **Finish & reflect** ends the session on the server; **View summary** saves the reflection; **Skip** saves nothing.
- **The summary page is built by the server**, from what was stored, not from what the browser remembers. That way it matches the exported data exactly.
- **Chat time uses the server clock**, from opening the chat to Finish. *Teaching note:* ask the student what "chat time" should mean for the research. Including pauses is the simple choice; measuring only active typing would need more design.
- **Export:** one CSV per table, with the Excel marker so Hinglish/Devanagari text displays correctly. The files contain participant data and are git-ignored.

### Evaluating replies fairly (Phase 9, D-53)
- **A vs B, nothing else different:** A = plain prompt, B = full strategy pipeline. Same message, same model, **no history and no check-in data in either**, so any difference comes from the strategy layer.
- **Blind rating:** raters get a shuffled sheet without condition, model or strategy, so they can't (even unconsciously) favour the strategy condition. The full file keeps everything for analysis, linked by `item_id`. A fixed seed makes the shuffle repeatable.
- **The same yardstick:** "strategy followed" is judged against the test set's expected strategy for every row.
- **Several models:** `--models a,b`, with `ollama:` for local ones; the same model does classify and reply in B.
- **Teaching note (Sessions 13–14):** why blinding matters, why we remove history (D-45), and what the numbers can and can't show with 30 synthetic messages and one or two raters.

---

## 9. Going online: Supabase and online safety (Phase 11, built)

### Why a new phase (D-46)
- The developer plans to deploy the app so the student can share it with people. The spec's prototype is local-only, so this is a deliberate extension.
- **Order:** Phases 8 → 9 → 11 → 10. The handover docs and `mentoring.md` stay last, so they describe the final code.
- **The local setup does not change:** the student course still runs on SQLite, offline, in mock mode.

### Supabase, not Neon (D-47)
- Both are hosted Postgres. Supabase was chosen for its dashboard (the student can see tables, like DB Browser), its region choice (India-near hosting matters for DPDP), and built-in auth if real logins are ever needed.
- **SQLite when `DATABASE_URL` is empty, Supabase when it is set.** All SQL stays in `db.py`.
- **Row Level Security is switched on with no policies:** Supabase exposes tables through a public API by default; RLS with no policies blocks that, and only our backend's direct connection can read the data.

### Online safety additions (D-48 to D-50)
- **Researcher-issued, unguessable codes:** without them, anyone could type `P001` and read another person's answers and date of birth (K-08).
- **Rate limits** protect the paid model budget; **safety replies are never limited**.
- **Limits:** 40 messages per participant per hour, 700 per day in total (developer's numbers).
- **No alert channel (D-51, developer's choice):** a safety report script (code, time and flag type, no message text) and a **written review routine** instead. *Trade-off:* the follow-up adult only learns about a flag when the report is run, so how often it's run must be agreed before launch. The participant always gets the helplines instantly.
- **Ages (D-50):** 18+ **and** under-18 with guardian consent. An age question at consent; under-18 needs an extra guardian tick; the signed guardian form is collected outside the app.
- **Hosting:** Railway or Render (both documented). **Supabase needs only one value**, the Session-pooler connection string, in `DATABASE_URL`.
- **Consent text, a delete-participant script** (right to withdraw), demo and `/docs` pages off.
- **Session ownership (D-55, found while building):** session ids are simple numbers, so a visitor could have guessed another person's id. Every chat and summary request now carries the participant code, and the server checks the session belongs to it. *Teaching note: a classic security bug ("insecure direct object reference") and a good discussion of why ids alone are not access control.*
- **Only issued codes online (D-56, found in testing):** "refuse codes that don't exist" wasn't enough, because local testing with the Supabase database writes guessable codes like `P001` into it. Codes from `create_codes.py` are now marked `issued`, and only those sign in online. *Teaching note: shared databases between test and production are a classic source of security holes; ideally use a separate Supabase project for testing.*
- **Behind a proxy:** on Railway/Render every request arrives from the host's proxy, so the sign-in limit reads the visitor's real address from `X-Forwarded-For`; otherwise all visitors would share one limit.
- **Same code for both worlds (D-54):** `db_connect.py` hides the two small differences between SQLite and Postgres (placeholders and new ids), so all other files stay the same. The student course still runs on SQLite.
- **Pre-launch checklist** in `docs/DEPLOYMENT.md`: no link is shared until ethics approval, approved consent text, a named follow-up adult and a privacy notice are in place.
- **Teaching note:** a strong final-session topic. Moving from a prototype to real users changes the responsibilities far more than the code.

---

## 10. Handover: docs and the student starter (Phase 10)

### The student starter (D-57)
- **What's left to write:** the 5 spec functions (`chat_completion`, `check_message`, `choose_strategy`, `classify`, `build_messages`) **plus** `parse_classifier_output`, `build_system_prompt` and the classifier prompt text, mapped to Sessions 4, 6, 7 and 9.
- **What stays written:** everything else, including small helpers (thinking-text removal, JSON extraction, risk cleaning, check-in lines), so each session fits in one hour.
- **Safety is never a TODO:** `check_message()` works from day one, and the `"Safety"` line in `choose_strategy()` is already there with "never remove this". The student *studies* safety (Session 5); they don't *build* it from zero.
- **Safe placeholders:** each stub returns something harmless (a reply saying it's a TODO, default classifier values, the first strategy, the plain prompt) and prints `[TODO Session N]`, so the app always runs and the student sees exactly what's missing.
- **Teaching note:** the finished app in the main folder is the answer key. The verification swapped in the finished functions to prove the "done when" checks are reachable.

### `mentoring.md` (Phase 10, part 2)
- **Structure follows spec 15.1 exactly**, and every session uses the same headings so the mentor always knows where to look. Hints come before answers, and every "done when" has a command with its expected output, so success is never a matter of opinion.
- **Real material from the build:** the developer's classifier misses (T18, T21, T23) are the Session 8 exercise (they were left un-tuned on purpose, D-42); the `!` bug, the thinking model, the copying chat (D-45) and the guessable sessions (D-55) are teaching stories (appendix A5).
- **Mock mode as the safety net:** every session works without a model; real-model checks move to homework if the internet fails.
- **The student gets only the starter (D-59)** as a zip, with the student docs inside it, so the answer key isn't one folder away.
- **Safety gap found while writing (D-58):** spaced letters ("d i e") were not caught. The fix only adds matches; the test set still passes. It became a Session 5 story about safety never being finished.

### `flow.md`
- Added at the developer's request: a plain-language map of users, sign-up and sign-in (no accounts; codes only), the journey, the chat pipeline, safety and the researcher's scripts. A good first read for the mentor and the student.

---

## 11. Scope decisions

- **Classifier (D-21):** prompt-based with Qwen. A trained DistilBERT/DeBERTa classifier is a documented **stretch idea only** (spec section 3 puts it out of scope; 30 test messages are too few to train on; the ESConv dataset would be the source).
- **Extra checks (D-19):** some phases have extra checks marked "(Extra)". All the spec's checks are kept.
- **Plain prompt reused (D-14):** Phase 4's no-strategy prompt is also "condition A" in the Phase 9 evaluation.

---

## 12. Changelog of this file

| Date | Phase | Change |
|---|---|---|
| 4 Nov 2026 | after Phase 4 | File created; covers D-01 to D-39 |
| 4 Nov 2026 | Phase 5 | Safety section updated (D-40) |
| 4 Nov 2026 | Phase 6 | Classifier section added (D-41); first real result and no-tuning decision (D-42); qwen3:8b comparison and hybrid-model fix (D-43) |
| 4 Nov 2026 | Phase 7 | Strategy-aware replies section added (D-44); check-5 method (D-45) |
| 4 Nov 2026 | Phase 8 | Summary, reflection and export (D-52) |
| 4 Nov 2026 | Phase 9 | Evaluation design: A vs B, blind rating sheet (D-53) |
| 4 Nov 2026 | Phase 11 | Built: Supabase support, online safeguards, session ownership (D-54, D-55); issued-codes fix (D-56) |
| 4 Nov 2026 | Phase 10 (part 1) | Handover docs, flow.md, student starter design (D-57) |
| 4 Nov 2026 | after Phase 7 | Deployment plan: Supabase + online safety as Phase 11 (D-46 to D-50); developer's choices on hosting, ages, limits, no alerts (D-49 to D-51) |
| 4 Nov 2026 | Phase 10 part 2 | `mentoring.md` section added (D-58, D-59) |
