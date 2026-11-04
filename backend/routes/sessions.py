# mentoring.md: Session 11 - Check-ins and data ethics
"""Chat sessions: start, end and summary (spec section 10).

A session is one conversation. It starts when the chat is first opened and
ends when the person clicks "Finish & reflect". The summary page is built from
what the server stored, not from what the browser remembers.
"""

from contextlib import closing
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend import checkins, config, db
from backend.routes.participants import find_participant

router = APIRouter()


class SessionBody(BaseModel):
    code: str


def load_session(conn, session_id: int):
    """Get a session or answer 404, so every route handles a wrong id the same way."""
    session = db.get_session(conn, session_id)
    if session is None:
        raise HTTPException(404, "Chat session not found. Please start a new session.")
    return session


def seconds_between(start_iso: str, end_iso: str) -> int:
    """Whole seconds between two ISO timestamps from db.now_iso()."""
    return max(0, int((datetime.fromisoformat(end_iso) - datetime.fromisoformat(start_iso)).total_seconds()))


@router.post("/api/sessions")
def start_session(body: SessionBody) -> dict:
    """Create a new chat session for a participant."""
    with closing(db.get_connection()) as conn:
        participant = find_participant(conn, body.code)
        session_id = db.create_session(conn, participant["id"])
        conn.commit()
    print(f"[chat] new session {session_id} for {participant['code']}")
    return {"session_id": session_id}


@router.post("/api/sessions/{session_id}/end")
def end_session(session_id: int) -> dict:
    """Store ended_at and chat_seconds. The server's clock is used, not the browser's (D-13)."""
    with closing(db.get_connection()) as conn:
        session = load_session(conn, session_id)
        ended_at = db.now_iso()
        chat_seconds = seconds_between(session["started_at"], ended_at)
        db.end_session(conn, session_id, ended_at, chat_seconds)
        conn.commit()
    print(f"[chat] session {session_id} ended after {chat_seconds}s")
    return {"session_id": session_id, "ended_at": ended_at, "chat_seconds": chat_seconds}


@router.get("/api/sessions/{session_id}/summary")
def session_summary(session_id: int) -> dict:
    """Message count, chat time, strategy counts, latest PHQ-9 and reflection answers."""
    with closing(db.get_connection()) as conn:
        session = load_session(conn, session_id)
        participant = db.get_participant_by_id(conn, session["participant_id"])
        # A session that was never ended counts up to now.
        chat_seconds = session["chat_seconds"]
        if chat_seconds is None:
            chat_seconds = seconds_between(session["started_at"], db.now_iso())
        last_user = db.last_message(conn, session_id, "user")
        last_reply = db.last_message(conn, session_id, "assistant")
        status = checkins.build_status(conn, participant, [s["name"] for s in config.load_strategies()])
        return {
            "session_id": session_id,
            "started_at": session["started_at"],
            "ended_at": session["ended_at"],
            "chat_seconds": chat_seconds,
            "message_count": db.count_messages(conn, session_id, "user"),
            "reply_count": db.count_messages(conn, session_id, "assistant"),
            "strategy_counts": db.used_strategy_counts(conn, session_id),
            "requested_strategy": last_user["requested_strategy"] if last_user else status["preferred_strategy"],
            "last_used_strategy": last_reply["used_strategy"] if last_reply else None,
            "latest_phq": status["latest_phq"],
            "reflection": db.reflection_for_session(conn, session_id),
        }
