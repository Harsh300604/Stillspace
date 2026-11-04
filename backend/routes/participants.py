# mentoring.md: Session 11 - Check-ins and data ethics
"""Participant codes, their status, preferences, and the demo date shift.

There are no passwords: a participant is only a pseudonymous code like P001
typed on the consent screen (spec section 4). Online (APP_ENV=production) only
codes issued by the researcher with scripts/create_codes.py can sign in, and the
consent step records the age answer (D-48, D-50).
"""

import re
from contextlib import closing
from datetime import date

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend import checkins, config, db, ratelimit

router = APIRouter()

CODE_PATTERN = re.compile(r"^[A-Za-z0-9-]{3,20}$")  # same rule as the browser; "-" for issued codes (D-09, D-48)
INVALID_CODE = "This participant code is not valid. Please check the code you were given."


class CodeBody(BaseModel):
    code: str
    age_group: str | None = None          # "18plus" or "under18" (online consent step)
    guardian_consent: bool | None = None  # required for "under18"


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
        # Online, a wrong format gets the same answer as an unknown code, so it reveals nothing.
        raise HTTPException(400, INVALID_CODE if config.IS_PRODUCTION else "Participant code must be 3-20 letters, digits or hyphens.")
    return code.upper()


def client_ip(request: Request) -> str:
    """The visitor's IP. Behind Railway/Render's proxy the real one is the first X-Forwarded-For entry."""
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")


def consent_fields(body: CodeBody) -> dict:
    """Online only: check the age answer against AGE_POLICY and return the columns to store."""
    if body.age_group == "18plus":
        return {"age_group": "18plus", "guardian_consent": 0, "consent_at": db.now_iso()}
    if body.age_group == "under18":
        if config.AGE_POLICY != "18plus_or_guardian":
            raise HTTPException(403, "This study is only open to people aged 18 or older.")
        if not body.guardian_consent:
            raise HTTPException(403, "Participants under 18 need a parent's or guardian's consent before taking part.")
        return {"age_group": "under18", "guardian_consent": 1, "consent_at": db.now_iso()}
    raise HTTPException(400, "Please answer the age question on the consent page.")


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
def login_participant(body: CodeBody, request: Request) -> dict:
    """Sign in. Locally a new code creates the participant; online only issued codes work."""
    if not ratelimit.allow(f"login:{client_ip(request)}", config.LOGIN_LIMIT_PER_MINUTE, 60):
        raise HTTPException(429, "Too many sign-in attempts. Please wait a minute and try again.")
    code = normalise_code(body.code)
    with closing(db.get_connection()) as conn:
        participant = db.get_participant(conn, code)
        created = participant is None
        if config.IS_PRODUCTION:
            # Only issued codes: codes typed during local testing (e.g. P001) may also be in
            # the database, but they are guessable, so they never work online (D-56).
            if created or not participant["issued"]:
                print(f"[participants] refused {'unknown' if created else 'non-issued'} code from {client_ip(request)}")
                raise HTTPException(403, INVALID_CODE)
            db.update_participant(conn, participant["id"], consent_fields(body))
            conn.commit()
            participant = db.get_participant(conn, code)
        elif created:
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
