# mentoring.md: Session 11 - Check-ins and data ethics
"""Participant codes, their status, preferences, and the demo date shift.

There are no passwords: a participant is only a pseudonymous code like P001
typed on the consent screen (spec section 4).
"""

import re
from contextlib import closing
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend import checkins, config, db

router = APIRouter()

CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{3,20}$")  # same rule as the browser (D-09)


class CodeBody(BaseModel):
    code: str


class ParticipantUpdate(BaseModel):
    preferred_strategy: str | None = None
    dob: str | None = None  # "YYYY-MM-DD", or "" to remove it


class DemoAdvance(BaseModel):
    code: str
    days: int


def normalise_code(code: str) -> str:
    """Check the code format and return it upper-case, so p001 and P001 are one person."""
    code = code.strip()
    if not CODE_PATTERN.match(code):
        raise HTTPException(400, "Participant code must be 3-20 letters or digits.")
    return code.upper()


def strategy_names() -> list[str]:
    """Names in the active strategy set, used to validate preferences."""
    return [s["name"] for s in config.load_strategies()]


def find_participant(conn, code: str):
    """Load a participant or answer 404, so every route handles unknown codes the same way."""
    participant = db.get_participant(conn, normalise_code(code))
    if participant is None:
        raise HTTPException(404, "Participant code not found. Please start from the consent page.")
    return participant


def check_dob(dob: str) -> str | None:
    """Accept a real past date in YYYY-MM-DD form; empty text means 'remove it'."""
    if dob == "":
        return None
    try:
        parsed = date.fromisoformat(dob)
    except ValueError:
        raise HTTPException(400, "Date of birth must look like 2008-05-31.")
    if parsed > date.today():
        raise HTTPException(400, "Date of birth cannot be in the future.")
    return dob


def check_preferred(name: str) -> str:
    """A preference must be 'Automatic' or a strategy from the active set."""
    if name != "Automatic" and name not in strategy_names():
        raise HTTPException(400, f"Unknown support strategy: {name}")
    return name


@router.post("/api/participants")
def login_participant(body: CodeBody) -> dict:
    """Create the participant if the code is new, then return their status."""
    code = normalise_code(body.code)
    with closing(db.get_connection()) as conn:
        participant = db.get_participant(conn, code)
        created = participant is None
        if created:
            participant = db.create_participant(conn, code)
            conn.commit()
        print(f"[participants] {'new' if created else 'returning'} participant {code}")
        return {"created": created, "status": checkins.build_status(conn, participant, strategy_names())}


@router.get("/api/participants/{code}/status")
def get_status(code: str) -> dict:
    """Which check-ins are due today, latest PHQ-9 result, preference."""
    with closing(db.get_connection()) as conn:
        participant = find_participant(conn, code)
        return checkins.build_status(conn, participant, strategy_names())


@router.patch("/api/participants/{code}")
def update_participant(code: str, body: ParticipantUpdate) -> dict:
    """Save the preferred strategy and/or date of birth."""
    with closing(db.get_connection()) as conn:
        participant = find_participant(conn, code)
        fields = {}
        if body.preferred_strategy is not None:
            fields["preferred_strategy"] = check_preferred(body.preferred_strategy)
        if body.dob is not None:
            fields["dob"] = check_dob(body.dob)
        db.update_participant(conn, participant["id"], fields)
        conn.commit()
        participant = db.get_participant(conn, participant["code"])
        return checkins.build_status(conn, participant, strategy_names())


@router.post("/api/demo/advance")
def demo_advance(body: DemoAdvance) -> dict:
    """Pretend days have passed (preview buttons). Only exists in demo mode."""
    if not config.DEMO_MODE:
        raise HTTPException(404, "Not found")
    if not 0 <= body.days <= 60:
        raise HTTPException(400, "days must be between 0 and 60.")
    with closing(db.get_connection()) as conn:
        participant = find_participant(conn, body.code)
        new_offset = (participant["demo_day_offset"] or 0) + body.days
        db.update_participant(conn, participant["id"], {"demo_day_offset": new_offset})
        conn.commit()
        participant = db.get_participant(conn, participant["code"])
        print(f"[demo] {participant['code']} demo date moved +{body.days} days (offset now {new_offset})")
        return checkins.build_status(conn, participant, strategy_names())
