# mentoring.md: Session 9 - Prompt builder
"""POST /api/chat: the full pipeline from spec section 5 (sessions live in routes/sessions.py).

    1. keyword safety check      safety.find_crisis_match()  -> fixed reply, no AI
    2. classifier                classifier.classify()       -> strategy + meta
    3. classifier-risk safety    risk == "high"              -> fixed reply
    4. strategy policy           strategy_policy.choose_strategy()
    5. prompt builder            prompt_builder.build_messages()
    6. reply                     llm.chat_completion() or mock.mock_reply()
    7. log everything            db.insert_message() + one console line
"""

import json
import time
from contextlib import closing

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend import checkins, classifier, config, db, llm, mock, prompt_builder, safety, strategy_policy

router = APIRouter()

MAX_MESSAGE_CHARS = 3000  # same limit as the chat box in the page
FALLBACK_REPLY = ("I'm sorry, I couldn't put a reply together just now. "
                  "Would you like to tell me a bit more, or try sending that again?")
META_KEYS = ["emotion", "intensity", "stage", "risk", "confidence", "rationale"]


class ChatBody(BaseModel):
    session_id: int
    message: str
    requested_strategy: str | None = "Automatic"


def history_as_chat(rows) -> list[dict]:
    """Turn stored messages into the {"role", "content"} list the model expects."""
    return [{"role": row["role"], "content": row["text"]} for row in rows]


def safety_reply(conn, body: ChatBody, message: str, flag: str, meta: dict,
                 classified: str | None, started: float) -> dict:
    """Store and return the fixed crisis reply. No reply model is called on this path."""
    reply = safety.crisis_response()
    latency_ms = int((time.perf_counter() - started) * 1000)
    common = {"requested_strategy": body.requested_strategy, "classified_strategy": classified,
              "used_strategy": "Safety", "safety_flag": flag, "meta_json": json.dumps(meta)}
    db.insert_message(conn, body.session_id, "user", message, **common)
    db.insert_message(conn, body.session_id, "assistant", reply, source="safety", latency_ms=latency_ms, **common)
    conn.commit()
    print(f"[chat] strategy=Safety safety={flag} rule={meta.get('matched_rule', '-')} source=safety {latency_ms}ms")
    return {"reply": reply, "requested_strategy": body.requested_strategy, "classified_strategy": classified,
            "used_strategy": "Safety", "meta": meta, "safety": {"flag": flag, "helplines": safety.HELPLINES},
            "source": "safety", "model": None, "latency_ms": latency_ms}


def generate_reply(prompt: list[dict], strategy_name: str, turn: int) -> tuple[dict, str]:
    """Step 6: mock reply, or the model's reply. Returns (result, source)."""
    if config.is_mock_mode():
        return mock.mock_reply(strategy_name, turn), "mock"
    try:
        result = llm.chat_completion(prompt, temperature=0.7, max_tokens=300)
    except llm.LLMError as error:
        # The real reason goes to the terminal; the user gets a friendly message
        # and a Retry button. Nothing is stored, so Retry is clean (D-32).
        print(f"[chat] LLM error: {error}")
        raise HTTPException(502, "The AI model could not be reached just now. Please try again in a moment.")
    if not result["text"]:
        result["text"] = FALLBACK_REPLY
        return result, "fallback"
    return result, "llm"


@router.post("/api/chat")
def chat(body: ChatBody) -> dict:
    """Reply to one user message using the full pipeline, and store both messages."""
    message = body.message.strip()
    if not message:
        raise HTTPException(400, "Please type a message first.")
    if len(message) > MAX_MESSAGE_CHARS:
        raise HTTPException(400, f"Messages can be at most {MAX_MESSAGE_CHARS} characters.")

    started = time.perf_counter()
    with closing(db.get_connection()) as conn:
        session = db.get_session(conn, body.session_id)
        if session is None:
            raise HTTPException(404, "Chat session not found. Please start a new session.")

        # Step 1: deterministic safety check, BEFORE any AI call (spec 11.5).
        rule_id = safety.find_crisis_match(message)
        if rule_id:
            return safety_reply(conn, body, message, "keyword", {"matched_rule": rule_id}, None, started)

        # History is read BEFORE storing the new message, so it is not sent twice.
        history = history_as_chat(db.recent_messages(conn, body.session_id, config.HISTORY_TURNS))
        strategies = config.load_strategies()
        names = [s["name"] for s in strategies]

        # Step 2: classifier.
        result = classifier.classify(message, history, strategies)
        meta = {key: result[key] for key in META_KEYS}
        meta.update({"classifier_source": result["source"], "classifier_ms": result["latency_ms"]})

        # Step 3: the classifier's risk is a second safety net.
        if result["risk"] == "high":
            return safety_reply(conn, body, message, "classifier", meta, result["strategy"], started)

        # Step 4: requested vs classified -> used strategy.
        used = strategy_policy.choose_strategy(body.requested_strategy, result["strategy"], "none", names)
        strategy = next(s for s in strategies if s["name"] == used)

        # Step 5: prompt = system text + strategy + meta + check-in context + history.
        participant = db.get_participant_by_id(conn, session["participant_id"])
        context = checkins.checkin_context(conn, participant)
        prompt = prompt_builder.build_messages(strategy, meta, context, history, message)
        # print("[chat] DEBUG system prompt:\n" + prompt[0]["content"])  # DEBUG: print system prompt

        # Step 6: reply.
        reply, source = generate_reply(prompt, used, db.count_messages(conn, body.session_id, "assistant"))
        latency_ms = int((time.perf_counter() - started) * 1000)

        # Step 7: store both messages with all metadata.
        common = {"requested_strategy": body.requested_strategy, "classified_strategy": result["strategy"],
                  "used_strategy": used, "meta_json": json.dumps(meta)}
        db.insert_message(conn, body.session_id, "user", message, **common)
        db.insert_message(conn, body.session_id, "assistant", reply["text"], source=source,
                          model=reply["model"], latency_ms=latency_ms, **common)
        conn.commit()

    print(f"[chat] strategy={used} (requested={body.requested_strategy}, classified={result['strategy']}) "
          f"emotion={meta['emotion']} safety=none source={source} {latency_ms}ms")
    return {"reply": reply["text"], "requested_strategy": body.requested_strategy,
            "classified_strategy": result["strategy"], "used_strategy": used, "meta": meta,
            "safety": {"flag": "none", "helplines": []}, "source": source, "model": reply["model"],
            "latency_ms": latency_ms}
