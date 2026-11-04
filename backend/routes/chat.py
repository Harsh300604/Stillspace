# mentoring.md: Session 9 - Prompt builder
"""Chat sessions and POST /api/chat.

Phase 4 version: a plain reply with no support strategy yet. Later phases add
the steps from spec section 5 in this order:
    1. keyword safety check        (Phase 5)
    2. classifier                  (Phase 6/7)
    3. classifier-risk safety      (Phase 7)
    4. strategy policy             (Phase 7)
    5. prompt builder              (Phase 7)
    6. LLM reply or mock reply     (now)
    7. log everything              (now)
"""

from contextlib import closing

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend import config, db, llm, mock
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

    with closing(db.get_connection()) as conn:
        if db.get_session(conn, body.session_id) is None:
            raise HTTPException(404, "Chat session not found. Please start a new session.")
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
