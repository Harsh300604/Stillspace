# mentoring.md: Session 11 - Check-ins and data ethics
"""POST /api/checkins: save setup, daily, fortnightly (PHQ-9) and post-session answers.

The server scores the PHQ-9 itself and stores that score, even though the
browser shows a live score too: stored research data must not depend on code
running in someone's browser.
"""

from contextlib import closing
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend import checkins, db
from backend.routes.participants import check_dob, check_preferred, find_participant, strategy_names

router = APIRouter()

CHECKIN_TYPES = {"setup", "daily", "fortnightly", "post_session"}


class CheckinBody(BaseModel):
    code: str
    type: str
    answers: dict[str, Any] = {}
    session_id: int | None = None


def drop_empty(answers: dict) -> dict:
    """Unanswered questions are stored as absent keys, never as 0 or null (spec section 9)."""
    return {k: v for k, v in answers.items() if v is not None and v != ""}


def save_setup(conn, participant, answers: dict) -> int:
    """Setup also updates the participant row, so the preference is used from now on."""
    answers = drop_empty(answers)
    fields = {"setup_done": 1}
    if "dob" in answers:
        fields["dob"] = check_dob(answers["dob"])
    if "preferred" in answers:
        fields["preferred_strategy"] = check_preferred(answers["preferred"])
    db.update_participant(conn, participant["id"], fields)
    return db.insert_checkin(conn, participant["id"], "setup", answers, checkins.local_today(participant).isoformat())


def save_daily(conn, participant, answers: dict) -> int:
    """One daily row per local date: later saves merge into it (D-11).

    A value of null removes that answer (e.g. "Skip for now" after picking a
    mood). An empty row is still created: finishing with everything skipped
    counts as done, like in the mockup ("completion is an explicit action").
    """
    if "mood" in answers and answers["mood"] is not None and answers["mood"] not in checkins.MOOD_LABELS:
        raise HTTPException(400, f"Mood must be one of: {', '.join(checkins.MOOD_LABELS)}")
    today = checkins.local_today(participant).isoformat()
    existing = db.latest_checkin(conn, participant["id"], "daily", local_date=today)
    merged = db.get_checkin(conn, existing["id"])["answers"] if existing else {}
    merged.update(answers)
    merged = drop_empty(merged)
    if existing:
        db.update_checkin_answers(conn, existing["id"], merged)
        return existing["id"]
    return db.insert_checkin(conn, participant["id"], "daily", merged, today)


def save_fortnightly(conn, participant, answers: dict) -> int:
    """PHQ-9 plus the extra wellbeing questions; the extras never change the score."""
    try:
        phq_answers = checkins.clean_phq_answers(drop_empty(answers.get("phq") or {}))
    except ValueError as error:
        raise HTTPException(400, str(error))
    stored = {"phq": phq_answers, "extra": drop_empty(answers.get("extra") or {})}
    score = checkins.score_phq9(phq_answers)
    checkin_id = db.insert_checkin(conn, participant["id"], "fortnightly", stored,
                                   checkins.local_today(participant).isoformat(), phq=score)
    print(f"[checkins] {participant['code']} PHQ-9 answered={len(phq_answers)}/9 "
          f"total={score['total']} band={score['band']} item9_flag={score['item9_flag']}")
    return checkin_id


def save_post_session(conn, participant, answers: dict, session_id: int | None) -> int:
    """Reflection answers belong to one chat session of this participant."""
    session = db.get_session(conn, session_id) if session_id else None
    if session is None or session["participant_id"] != participant["id"]:
        raise HTTPException(400, "A valid session_id is needed for a post-session reflection.")
    return db.insert_checkin(conn, participant["id"], "post_session", drop_empty(answers),
                             checkins.local_today(participant).isoformat(), session_id=session_id)


@router.post("/api/checkins")
def save_checkin(body: CheckinBody) -> dict:
    """Store one check-in. Returns the stored row and the updated status."""
    if body.type not in CHECKIN_TYPES:
        raise HTTPException(400, f"type must be one of: {', '.join(sorted(CHECKIN_TYPES))}")
    with closing(db.get_connection()) as conn:
        participant = find_participant(conn, body.code)
        if body.type == "setup":
            checkin_id = save_setup(conn, participant, body.answers)
        elif body.type == "daily":
            checkin_id = save_daily(conn, participant, body.answers)
        elif body.type == "fortnightly":
            checkin_id = save_fortnightly(conn, participant, body.answers)
        else:
            checkin_id = save_post_session(conn, participant, body.answers, body.session_id)
        conn.commit()
        participant = db.get_participant(conn, participant["code"])
        return {
            "checkin": db.get_checkin(conn, checkin_id) if checkin_id else None,
            "status": checkins.build_status(conn, participant, strategy_names()),
        }
