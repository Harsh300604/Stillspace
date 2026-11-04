# mentoring.md: Session 11 - Check-ins and data ethics
"""PHQ-9 scoring and check-in scheduling (spec section 11.6).

Plain functions with no web code, so they are easy to read and to try in a
Python shell: from backend.checkins import score_phq9
"""

import json
import sqlite3
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from backend import config, db, safety

PHQ_ITEMS = 9
FORTNIGHT_DAYS = 14
MOOD_LABELS = ["Low", "Unsettled", "Neutral", "Okay", "Good"]  # same order as the mockup's mood buttons


def phq_band(total: int) -> str:
    """Standard PHQ-9 severity bands."""
    if total <= 4:
        return "minimal"
    if total <= 9:
        return "mild"
    if total <= 14:
        return "moderate"
    if total <= 19:
        return "moderately severe"
    return "severe"


def score_phq9(phq_answers: dict) -> dict:
    """Score PHQ-9 answers given as {"0": 0-3, ..., "8": 0-3}.

    A total and band exist only when all 9 items are answered: an unanswered
    item is unknown, not zero, so scoring it as zero would understate distress.
    Item 9 (key "8") is flagged on its own, whatever the total.
    """
    answered = len(phq_answers)
    complete = answered == PHQ_ITEMS
    total = sum(phq_answers.values()) if complete else None
    return {
        "total": total,
        "band": phq_band(total) if complete else None,
        "complete": complete,
        "item9_flag": safety.phq_item9_flag(phq_answers),  # rule lives in safety.py (D-30)
    }


def clean_phq_answers(raw: dict) -> dict:
    """Keep only valid PHQ items ("0".."8" -> whole number 0-3); raise ValueError otherwise.

    The server re-checks everything because the score is stored for research,
    and the browser's copy could be wrong or edited.
    """
    cleaned = {}
    for key, value in raw.items():
        if key not in {str(i) for i in range(PHQ_ITEMS)}:
            raise ValueError(f"Unknown PHQ-9 item: {key}")
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 3:
            raise ValueError(f"PHQ-9 item {int(key) + 1} must be a whole number from 0 to 3")
        cleaned[key] = value
    return cleaned


def local_today(participant: sqlite3.Row) -> date:
    """Today's date in APP_TIMEZONE, moved forward by the participant's demo offset."""
    today = datetime.now(ZoneInfo(config.APP_TIMEZONE)).date()
    return today + timedelta(days=participant["demo_day_offset"] or 0)


def build_status(conn: sqlite3.Connection, participant: sqlite3.Row, strategy_names: list[str]) -> dict:
    """Everything the frontend needs to decide which check-in is due (GET .../status)."""
    today = local_today(participant).isoformat()
    daily = db.latest_checkin(conn, participant["id"], "daily", local_date=today)
    fortnightly = db.latest_checkin(conn, participant["id"], "fortnightly")

    # Due if never done, or if the last one is 14+ days old (implementation.md D-12).
    fortnightly_due = True
    if fortnightly:
        days_since = (date.fromisoformat(today) - date.fromisoformat(fortnightly["local_date"])).days
        fortnightly_due = days_since >= FORTNIGHT_DAYS

    daily_answers = json.loads(daily["answers_json"]) if daily else {}
    latest_phq = None
    if fortnightly:
        latest_phq = {
            "total": fortnightly["phq_total"],
            "band": fortnightly["phq_band"],
            "complete": bool(fortnightly["phq_complete"]),
            "item9_flag": bool(fortnightly["item9_flag"]),
            "date": fortnightly["local_date"],
        }

    # A stored preference from another strategy set would not match the dropdown.
    preferred = participant["preferred_strategy"] or "Automatic"
    if preferred != "Automatic" and preferred not in strategy_names:
        preferred = "Automatic"

    return {
        "code": participant["code"],
        "setup_done": bool(participant["setup_done"]),
        "daily_due": daily is None,
        "fortnightly_due": fortnightly_due,
        "today_mood": daily_answers.get("mood"),
        "latest_phq": latest_phq,
        "preferred_strategy": preferred,
        # Extra fields (implementation.md D-24): let the page show saved answers
        # again after a refresh, and show the demo date.
        "local_date": today,
        "demo_day_offset": participant["demo_day_offset"] or 0,
        "answers": {
            "setup": {k: v for k, v in {"dob": participant["dob"], "preferred": participant["preferred_strategy"]}.items() if v},
            "daily": daily_answers,
            # Only the current fortnight's answers; once a new one is due the form starts empty.
            "fortnightly": json.loads(fortnightly["answers_json"]) if fortnightly and not fortnightly_due else {},
        },
    }
