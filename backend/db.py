# mentoring.md: Session 11 - Check-ins and data ethics
"""SQLite storage: one file (data/stillspace.db), plain SQL, no ORM.

The tables match spec section 9. They are created automatically on start-up,
so a fresh clone needs no setup step. Open the file in DB Browser for SQLite
to see exactly what is stored.
"""

import json
import sqlite3
from datetime import datetime, timezone

from backend import config

TABLES_SQL = """
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    dob TEXT NULL,
    preferred_strategy TEXT DEFAULT 'Automatic',
    setup_done INTEGER DEFAULT 0,
    demo_day_offset INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY,
    participant_id INTEGER NOT NULL REFERENCES participants(id),
    type TEXT NOT NULL,              -- setup | daily | fortnightly | post_session
    answers_json TEXT NOT NULL,      -- unanswered questions are absent keys, never 0
    phq_total INTEGER NULL,          -- only when all 9 PHQ items are answered
    phq_band TEXT NULL,
    phq_complete INTEGER DEFAULT 0,
    item9_flag INTEGER DEFAULT 0,
    session_id INTEGER NULL,         -- post_session only
    local_date TEXT NOT NULL,        -- YYYY-MM-DD in APP_TIMEZONE (+ demo offset)
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    participant_id INTEGER NOT NULL REFERENCES participants(id),
    started_at TEXT NOT NULL,
    ended_at TEXT NULL,
    chat_seconds INTEGER NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL,              -- user | assistant
    text TEXT NOT NULL,
    requested_strategy TEXT NULL,
    classified_strategy TEXT NULL,
    used_strategy TEXT NULL,
    meta_json TEXT NULL,
    safety_flag TEXT DEFAULT 'none', -- none | keyword | classifier
    source TEXT NULL,                -- llm | mock | safety | fallback
    model TEXT NULL,
    latency_ms INTEGER NULL,
    created_at TEXT NOT NULL
);
"""


def now_iso() -> str:
    """Current time as an ISO string in UTC, so timestamps sort and compare correctly."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_connection() -> sqlite3.Connection:
    """Open the database. Use it as `with closing(get_connection()) as conn:` so it always closes."""
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts: row["code"]
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables() -> None:
    """Create any missing tables. Safe to run on every start-up."""
    conn = get_connection()
    try:
        conn.executescript(TABLES_SQL)
        conn.commit()
    finally:
        conn.close()


# ---------- participants ----------

def get_participant(conn: sqlite3.Connection, code: str) -> sqlite3.Row | None:
    """Find a participant by code, or None if the code is new."""
    return conn.execute("SELECT * FROM participants WHERE code = ?", (code,)).fetchone()


def create_participant(conn: sqlite3.Connection, code: str) -> sqlite3.Row:
    """Add a new participant with default settings and return the stored row."""
    conn.execute("INSERT INTO participants (code, created_at) VALUES (?, ?)", (code, now_iso()))
    return get_participant(conn, code)


def update_participant(conn: sqlite3.Connection, participant_id: int, fields: dict) -> None:
    """Update only the given columns. Column names come from our own code, never from the user."""
    allowed = {"dob", "preferred_strategy", "setup_done", "demo_day_offset"}
    for column, value in fields.items():
        if column in allowed:
            conn.execute(f"UPDATE participants SET {column} = ? WHERE id = ?", (value, participant_id))


# ---------- check-ins ----------

def insert_checkin(conn: sqlite3.Connection, participant_id: int, checkin_type: str, answers: dict,
                   local_date: str, phq: dict | None = None, session_id: int | None = None) -> int:
    """Store one check-in and return its id. `phq` holds the server-side PHQ-9 score fields."""
    phq = phq or {}
    cursor = conn.execute(
        "INSERT INTO checkins (participant_id, type, answers_json, phq_total, phq_band, phq_complete,"
        " item9_flag, session_id, local_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (participant_id, checkin_type, json.dumps(answers), phq.get("total"), phq.get("band"),
         int(phq.get("complete", False)), int(phq.get("item9_flag", False)), session_id, local_date, now_iso()),
    )
    return cursor.lastrowid


def update_checkin_answers(conn: sqlite3.Connection, checkin_id: int, answers: dict) -> None:
    """Replace the answers of an existing check-in (used for the daily upsert)."""
    conn.execute("UPDATE checkins SET answers_json = ? WHERE id = ?", (json.dumps(answers), checkin_id))


def latest_checkin(conn: sqlite3.Connection, participant_id: int, checkin_type: str,
                   local_date: str | None = None) -> sqlite3.Row | None:
    """Most recent check-in of a type, optionally only on one local date."""
    sql = "SELECT * FROM checkins WHERE participant_id = ? AND type = ?"
    params: list = [participant_id, checkin_type]
    if local_date:
        sql += " AND local_date = ?"
        params.append(local_date)
    return conn.execute(sql + " ORDER BY id DESC LIMIT 1", params).fetchone()


def get_checkin(conn: sqlite3.Connection, checkin_id: int) -> dict:
    """One check-in as a plain dict, with answers decoded from JSON (for API responses)."""
    row = conn.execute("SELECT * FROM checkins WHERE id = ?", (checkin_id,)).fetchone()
    result = dict(row)
    result["answers"] = json.loads(result.pop("answers_json"))
    return result


def get_session(conn: sqlite3.Connection, session_id: int) -> sqlite3.Row | None:
    """Find a chat session by id (sessions are created from Phase 4 on)."""
    return conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
