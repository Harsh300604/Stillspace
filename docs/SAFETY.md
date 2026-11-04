# Safety in Stillspace

> **Read before any testing with people.** Stillspace is a student research prototype. It is **not therapy, diagnosis or an emergency service**, and its safety layer is a simple safeguard, **not** a risk assessment.
> **Helplines (India):** **Tele-MANAS 14416** or **1-800-891-4416** (free, 24x7) · **Emergency 112**.

---

## 1. Ground rules

1. **Use synthetic or role-played conversations.** The developer has written the test messages (`eval/safety_prompts.csv`, `eval/test_messages.csv`), so nobody needs to write crisis messages of their own.
2. **Never use your own real problems as test input**, and never ask someone else to. If something real comes up while testing, stop and follow section 5.
3. **Real participants need approvals first:** ethics approval from the supervising organisation, informed consent, **guardian consent for under-18s**, a **named adult for follow-up** on safety flags (`FOLLOWUP_CONTACT`), and a privacy notice. PHQ-9 answers and dates of birth are health and personal data under India's **DPDP Act 2023**. See the checklist in `docs/DEPLOYMENT.md`.
4. **Never weaken the safety layer to make something else work.** Every change to `backend/safety.py` or `backend/data/crisis_keywords.json` must be followed by the safety test (section 4).

## 2. How the safety layer works

| Layer | Where | What it does |
|---|---|---|
| **1. Keyword check** (runs first) | `backend/safety.py`, `backend/data/crisis_keywords.json` | Checks every chat message for crisis wording **before any AI call**. On a match the AI is **never called**: the person gets a fixed reply with helplines. Works in mock mode, offline and when the model is broken. Never rate-limited. |
| **2. Classifier risk** | `backend/classifier.py` | The classifier's answer includes `risk`. `high` (any mention of self-harm, suicide, wanting to die or being in danger, even indirect; "when unsure, choose high") → the same fixed reply. Unclear values like "medium" count as high. |
| **3. PHQ-9 item 9** | `backend/safety.py`, `backend/checkins.py` | Item 9 ("thoughts that you would be better off dead, or of hurting yourself") above 0 → `item9_flag`, a follow-up notice with helplines, **whatever the total score**. |
| **4. Risk indicator** | right-hand panel | "**Follow-up needed**" after any safety reply in this session or when the latest PHQ-9 has item 9 > 0; otherwise "Not assessed". **Never a percentage.** |
| **5. The reply prompt** | `backend/data/prompts/system.txt` | Tells the model to stop applying the strategy and point to Tele-MANAS / 112 / a trusted adult if self-harm or being unsafe is mentioned. |

### What the keyword check catches
- English phrases and patterns ("kill myself", "end my life", "no reason to live", "sleep and never wake up", …)
- Hinglish ("mar jaana", "zindagi khatam", "jeena nahi chahta", …) and Devanagari ("आत्महत्या", "मरना चाहता", …)
- Spelling tricks, after normalising: capitals, curly apostrophes, `can't`/`cant`, look-alike digits (`k1ll`, `$uicide`), separated letters (`s.u.i.c.i.d.e`, `d i e`), stretched letters (`dieee`)
- Every match is logged with its **rule id** (terminal + database), so false alarms can be reviewed.

### The fixed crisis reply
From `backend/data/prompts/crisis_response.txt`: it acknowledges the person, says the prototype can't help in an emergency, lists **Tele-MANAS 14416 / 1-800-891-4416** and **112**, encourages contacting a trusted adult now, and names `FOLLOWUP_CONTACT` if set. It shows in a gold box with the badge **"Safety response"** and tap-to-call numbers.

## 3. Known limits (be honest about these)

- **It can miss things.** Indirect or unusual wording may not match any keyword; the classifier is a second net, but it can be wrong, offline (mock mode has no classifier risk) or fooled.
- **It can raise false alarms.** Example kept on purpose: "I love the movie *suicide* squad" triggers the crisis reply. A false alarm is safer than a missed crisis, so **don't add exceptions** that could hide a real one.
- **Figures of speech pass** ("this exam is killing me", "I'm dying to see that movie", "dead tired"); they're in the test set.
- **It is not a clinical assessment.** The PHQ-9 is a screening questionnaire, not a diagnosis.
- **No automatic alert** goes to anyone. Online, the follow-up adult must run `scripts/safety_report.py` on an agreed schedule (`docs/DEPLOYMENT.md`).

## 4. Running the safety test set

`eval/safety_prompts.csv` has 30 synthetic, non-graphic messages: 20 marked `crisis` (direct, indirect, self-harm, spelling tricks, Hinglish, Devanagari, slang) and 10 marked `normal` (tricky figures of speech).

**Quick check (no server needed)**, in the project folder with the venv active:
```powershell
python -c "import csv; from backend.safety import check_message; rows=list(csv.DictReader(open('eval/safety_prompts.csv', encoding='utf-8-sig'))); bad=[r for r in rows if check_message(r['message']) != (r['expect']=='crisis')]; print(len(rows), 'rows,', len(bad), 'mismatches'); [print('MISMATCH', r['id'], r['expect'], r['message']) for r in bad]"
```
✅ Expected: `30 rows, 0 mismatches`. Run it after **every** change to the safety files.

**In the app:** paste the `crisis` rows into the chat. Each should get the fixed reply with 14416 and 112 and the badge "Safety response"; the terminal shows `[chat] strategy=Safety safety=keyword rule=<id>`. The `normal` rows should get ordinary replies.

**Review flags:** `python scripts/safety_report.py --days 1` lists code, time, flag type and rule id, never the message text.

## 5. If a real disclosure happens

This applies to the mentor, the student, or anyone running a session, whether during testing, a demo, or a real study.

**Right away**
1. **Stop the session.** The person matters more than the project.
2. **Stay calm and present.** Listen, thank them for telling you, and don't promise to keep it secret if they may be at risk.
3. **If anyone may be in immediate danger: call 112** (or the local emergency number). Don't leave a person at immediate risk alone.
4. **Share the helplines:** **Tele-MANAS 14416** or **1-800-891-4416** (free, 24x7, many Indian languages).
5. **Involve a trusted adult** (for a student: a parent/guardian, teacher or school counsellor), according to your organisation's safeguarding procedure.

**Afterwards**
6. **Tell the named follow-up adult / supervisor** the same day. Record only what's needed: what happened, when, what was done. Not the chat text unless your procedure requires it.
7. **Follow your organisation's safeguarding policy** for anything involving a minor.
8. If it came through the app during a study: run the safety report, follow up as agreed, and consider whether the study should pause.
9. **Look after yourself too.** Talk to a supervisor; it's normal for this to stay with you.

**Don't:** try to counsel or diagnose; investigate; share the person's details with anyone outside the safeguarding process; post about it.

## 6. Online version (Phase 11)

Online (`APP_ENV=production`) adds: only researcher-issued codes can sign in, an age question with guardian consent for under-18s, the study's consent text, message limits that **never** block the safety reply, session ownership checks, and no demo or `/docs` pages. The app **refuses to start** without `FOLLOWUP_CONTACT`. Details and the pre-launch checklist: `docs/DEPLOYMENT.md`.

## 7. Data and privacy

- Data stays in your own database (local SQLite file or your own Supabase project). **Only the chat text** goes to the AI provider you configure (none in mock mode; your own computer with Ollama), and that provider's policy applies.
- PHQ-9 answers and dates of birth are **never** sent to the AI.
- The database, exports and `.env` are git-ignored. Never commit real data. Delete a participant on request with `python scripts/delete_participant.py <code>`.

PHQ-9 developed by Drs. Robert L. Spitzer, Janet B. W. Williams, Kurt Kroenke and colleagues.
