# mentoring.md: Session 9 - Prompt builder
"""Chat sessions and POST /api/chat.

Phase 5 version: keyword safety check, then a plain reply (no strategy yet).
The steps from spec section 5, in order:
    1. keyword safety check        (now)
    2. classifier                  (Phase 6/7)
    3. classifier-risk safety      (Phase 7)
    4. strategy policy             (Phase 7)
    5. prompt builder              (Phase 7)
    6. LLM reply or mock reply     (now)
    7. log everything              (now)
"""

import json
import time
from contextlib import closing

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend import config, db, llm, mock, safety
from backend.routes.participants import find_participant

router = APIRouter()

MAX_MESSAGE_CHARS = 3000  # same limit as the chat box in the page
FALLBACK_REPLY = ("I'm sorry, I couldn't put a reply together just now. "
                  "Would you like to tell me a bit more, or try sending that again?")


class SessionBody(BaseModel):
    code: str


class ChatBody(BaseModel):
    session_id: int
    message: str
    requested_strategy: str | None = "Automatic"


def read_prompt(name: str) -> str:
    """Load a prompt file from backend/data/prompts/ (read each time, so edits apply without restart)."""
    return (config.PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


def safety_reply(conn, body: ChatBody, message: str, flag: str, rule_id: str, started: float) -> dict:
    """Store and return the fixed crisis reply. No AI model is called on this path."""
    reply = safety.crisis_response()
    latency_ms = int((time.perf_counter() - started) * 1000)
    meta = {"matched_rule": rule_id}  # which keyword rule fired, so false alarms can be reviewed
    db.insert_message(conn, body.session_id, "user", message, requested_strategy=body.requested_strategy,
                      used_strategy="Safety", safety_flag=flag, meta_json=json.dumps(meta))
    db.insert_message(conn, body.session_id, "assistant", reply, requested_strategy=body.requested_strategy,
                      used_strategy="Safety", safety_flag=flag, meta_json=json.dumps(meta),
                      source="safety", latency_ms=latency_ms)
    conn.commit()
    print(f"[chat] strategy=Safety safety={flag} rule={rule_id} source=safety {latency_ms}ms")
    return {
        "reply": reply,
        "requested_strategy": body.requested_strategy,
        "classified_strategy": None,
        "used_strategy": "Safety",
        "meta": meta,
        "safety": {"flag": flag, "helplines": safety.HELPLINES},
        "source": "safety",
        "model": None,
        "latency_ms": latency_ms,
    }


def history_as_chat(rows) -> list[dict]:
    """Turn stored messages into the {"role", "content"} list the model expects."""
    return [{"role": row["role"], "content": row["text"]} for row in rows]


@router.post("/api/sessions")
def start_session(body: SessionBody) -> dict:
    """Create a new chat session for a participant."""
    with closing(db.get_connection()) as conn:
        participant = find_participant(conn, body.code)
        session_id = db.create_session(conn, participant["id"])
        conn.commit()
    print(f"[chat] new session {session_id} for {participant['code']}")
    return {"session_id": session_id}


@router.post("/api/chat")
def chat(body: ChatBody) -> dict:
    """Reply to one user message and store both messages."""
    message = body.message.strip()
    if not message:
        raise HTTPException(400, "Please type a message first.")
    if len(message) > MAX_MESSAGE_CHARS:
        raise HTTPException(400, f"Messages can be at most {MAX_MESSAGE_CHARS} characters.")

    started = time.perf_counter()
    with closing(db.get_connection()) as conn:
        if db.get_session(conn, body.session_id) is None:
            raise HTTPException(404, "Chat session not found. Please start a new session.")

        # Step 1: deterministic safety check, BEFORE any AI call (spec 11.5).
        rule_id = safety.find_crisis_match(message)
        if rule_id:
            return safety_reply(conn, body, message, "keyword", rule_id, started)

        # History is read BEFORE storing the new message, so it is not sent twice.
        history = history_as_chat(db.recent_messages(conn, body.session_id, config.HISTORY_TURNS))
        prompt = [{"role": "system", "content": read_prompt("plain_system.txt")}, *history,
                  {"role": "user", "content": message}]

        if config.is_mock_mode():
            result = mock.mock_reply(None, db.count_messages(conn, body.session_id, "assistant"))
            source = "mock"
        else:
            try:
                result = llm.chat_completion(prompt, temperature=0.7, max_tokens=300)
            except llm.LLMError as error:
                # The real reason goes to the terminal; the user gets a friendly
                # message and a Retry button. Nothing is stored, so Retry is clean.
                print(f"[chat] LLM error: {error}")
                raise HTTPException(502, "The AI model could not be reached just now. Please try again in a moment.")
            source = "llm"
            if not result["text"]:
                result["text"], source = FALLBACK_REPLY, "fallback"

        db.insert_message(conn, body.session_id, "user", message, requested_strategy=body.requested_strategy)
        db.insert_message(conn, body.session_id, "assistant", result["text"],
                          requested_strategy=body.requested_strategy, source=source,
                          model=result["model"], latency_ms=result["latency_ms"])
        conn.commit()

    print(f"[chat] strategy=- safety=none source={source} model={result['model']} {result['latency_ms']}ms")
    return {
        "reply": result["text"],
        "requested_strategy": body.requested_strategy,
        "classified_strategy": None,  # Phase 6/7
        "used_strategy": None,        # Phase 7
        "meta": {},
        "safety": {"flag": "none", "helplines": []},
        "source": source,
        "model": result["model"],
        "latency_ms": result["latency_ms"],
    }
