# mentoring.md: Session 11 - Check-ins and data ethics
"""Small query helpers: plain SQL, no ORM.

How the database is opened (SQLite locally, Postgres/Supabase online) lives in
db_connect.py. The tables are in backend/data/schema_*.sql and match spec
section 9. Locally, open data/stillspace.db in DB Browser for SQLite to see
exactly what is stored.
"""

import json
from datetime import datetime, timezone

from backend.db_connect import Connection, create_tables, describe, get_connection, insert, run  # noqa: F401

# Re-exported above so other files can keep writing db.get_connection(), db.create_tables().


def now_iso() -> str:
    """Current time as an ISO string in UTC, so timestamps sort and compare correctly."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------- participants ----------

def get_participant(conn: Connection, code: str) -> dict | None:
    """Find a participant by code, or None if the code is new."""
    return run(conn, "SELECT * FROM participants WHERE code = ?", (code,)).fetchone()


def get_participant_by_id(conn: Connection, participant_id: int) -> dict | None:
    """Find a participant by row id (used to get from a chat session to its participant)."""
    return run(conn, "SELECT * FROM participants WHERE id = ?", (participant_id,)).fetchone()


def create_participant(conn: Connection, code: str, issued: bool = False) -> dict:
    """Add a new participant and return the stored row.

    issued=True only for codes made by scripts/create_codes.py: online, only those can sign in (D-56).
    """
    insert(conn, "INSERT INTO participants (code, created_at, issued) VALUES (?, ?, ?)", (code, now_iso(), int(issued)))
    return get_participant(conn, code)


def update_participant(conn: Connection, participant_id: int, fields: dict) -> None:
    """Update only the given columns. Column names come from our own code, never from the user."""
    allowed = {"dob", "preferred_strategy", "setup_done", "demo_day_offset", "age_group", "guardian_consent", "consent_at"}
    for column, value in fields.items():
        if column in allowed:
            run(conn, f"UPDATE participants SET {column} = ? WHERE id = ?", (value, participant_id))


def delete_participant_data(conn: Connection, participant_id: int) -> dict:
    """Remove a participant and everything linked to them (right to withdraw). Returns row counts."""
    session_ids = [row["id"] for row in run(conn, "SELECT id FROM sessions WHERE participant_id = ?", (participant_id,)).fetchall()]
    counts = {"messages": 0}
    for session_id in session_ids:
        counts["messages"] += run(conn, "DELETE FROM messages WHERE session_id = ?", (session_id,)).rowcount
    counts["checkins"] = run(conn, "DELETE FROM checkins WHERE participant_id = ?", (participant_id,)).rowcount
    counts["sessions"] = run(conn, "DELETE FROM sessions WHERE participant_id = ?", (participant_id,)).rowcount
    counts["sign_ins"] = run(conn, "DELETE FROM auth_tokens WHERE participant_id = ?", (participant_id,)).rowcount
    counts["participants"] = run(conn, "DELETE FROM participants WHERE id = ?", (participant_id,)).rowcount
    return counts


# ---------- check-ins ----------

def insert_checkin(conn: Connection, participant_id: int, checkin_type: str, answers: dict,
                   local_date: str, phq: dict | None = None, session_id: int | None = None) -> int:
    """Store one check-in and return its id. `phq` holds the server-side PHQ-9 score fields."""
    phq = phq or {}
    return insert(
        conn,
        "INSERT INTO checkins (participant_id, type, answers_json, phq_total, phq_band, phq_complete,"
        " item9_flag, session_id, local_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (participant_id, checkin_type, json.dumps(answers), phq.get("total"), phq.get("band"),
         int(phq.get("complete", False)), int(phq.get("item9_flag", False)), session_id, local_date, now_iso()),
    )


def update_checkin_answers(conn: Connection, checkin_id: int, answers: dict) -> None:
    """Replace the answers of an existing check-in (used for the daily upsert)."""
    run(conn, "UPDATE checkins SET answers_json = ? WHERE id = ?", (json.dumps(answers), checkin_id))


def latest_checkin(conn: Connection, participant_id: int, checkin_type: str, local_date: str | None = None) -> dict | None:
    """Most recent check-in of a type, optionally only on one local date."""
    sql = "SELECT * FROM checkins WHERE participant_id = ? AND type = ?"
    params: list = [participant_id, checkin_type]
    if local_date:
        sql += " AND local_date = ?"
        params.append(local_date)
    return run(conn, sql + " ORDER BY id DESC LIMIT 1", params).fetchone()


def get_checkin(conn: Connection, checkin_id: int) -> dict:
    """One check-in as a plain dict, with answers decoded from JSON (for API responses)."""
    result = dict(run(conn, "SELECT * FROM checkins WHERE id = ?", (checkin_id,)).fetchone())
    result["answers"] = json.loads(result.pop("answers_json"))
    return result


# ---------- chat sessions and messages ----------

def create_session(conn: Connection, participant_id: int) -> int:
    """Start a new chat session and return its id."""
    return insert(conn, "INSERT INTO sessions (participant_id, started_at) VALUES (?, ?)", (participant_id, now_iso()))


def get_session(conn: Connection, session_id: int) -> dict | None:
    """Find a chat session by id."""
    return run(conn, "SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()


def insert_message(conn: Connection, session_id: int, role: str, text: str, **details) -> int:
    """Store one chat message. `details` may hold any other messages column (source, model, ...)."""
    columns = ["requested_strategy", "classified_strategy", "used_strategy", "meta_json",
               "safety_flag", "source", "model", "latency_ms"]
    values = [details.get(c) for c in columns]
    values[columns.index("safety_flag")] = details.get("safety_flag") or "none"
    return insert(
        conn,
        f"INSERT INTO messages (session_id, role, text, {', '.join(columns)}, created_at)"
        f" VALUES (?, ?, ?, {', '.join('?' for _ in columns)}, ?)",
        [session_id, role, text, *values, now_iso()],
    )


def recent_messages(conn: Connection, session_id: int, limit: int) -> list[dict]:
    """The last `limit` messages of a session, oldest first (the order the model reads them)."""
    rows = run(conn, "SELECT * FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?", (session_id, limit)).fetchall()
    return list(reversed(rows))


def end_session(conn: Connection, session_id: int, ended_at: str, chat_seconds: int) -> None:
    """Store when the session ended and how long it lasted (ending again later just updates it)."""
    run(conn, "UPDATE sessions SET ended_at = ?, chat_seconds = ? WHERE id = ?", (ended_at, chat_seconds, session_id))


def used_strategy_counts(conn: Connection, session_id: int) -> dict:
    """How many assistant replies used each strategy in a session, e.g. {"Validation": 2, "Safety": 1}."""
    rows = run(conn, "SELECT used_strategy AS strategy, COUNT(*) AS n FROM messages WHERE session_id = ?"
                     " AND role = 'assistant' GROUP BY used_strategy", (session_id,)).fetchall()
    return {(row["strategy"] or "none"): row["n"] for row in rows}


def last_message(conn: Connection, session_id: int, role: str) -> dict | None:
    """The newest message of one role in a session (for the last requested/used strategy)."""
    return run(conn, "SELECT * FROM messages WHERE session_id = ? AND role = ? ORDER BY id DESC LIMIT 1",
               (session_id, role)).fetchone()


def reflection_for_session(conn: Connection, session_id: int) -> dict | None:
    """The latest post-session reflection answers for a session, or None if it was skipped."""
    row = run(conn, "SELECT answers_json FROM checkins WHERE session_id = ? AND type = 'post_session'"
                    " ORDER BY id DESC LIMIT 1", (session_id,)).fetchone()
    return json.loads(row["answers_json"]) if row else None


def count_messages(conn: Connection, session_id: int, role: str) -> int:
    """How many messages of one role a session has (used to vary mock replies)."""
    return run(conn, "SELECT COUNT(*) AS n FROM messages WHERE session_id = ? AND role = ?",
               (session_id, role)).fetchone()["n"]


# ---------- safety report (online review routine, D-51) ----------

def safety_events(conn: Connection, since_iso: str) -> list[dict]:
    """Every safety flag since a time: chat flags (keyword/classifier) and PHQ-9 item 9. No message text."""
    chat = run(conn, "SELECT m.created_at AS time, p.code AS code, m.safety_flag AS flag, m.meta_json AS meta"
                     " FROM messages m JOIN sessions s ON s.id = m.session_id JOIN participants p ON p.id = s.participant_id"
                     " WHERE m.role = 'user' AND m.safety_flag != 'none' AND m.created_at >= ?", (since_iso,)).fetchall()
    phq = run(conn, "SELECT c.created_at AS time, p.code AS code FROM checkins c JOIN participants p ON p.id = c.participant_id"
                    " WHERE c.item9_flag = 1 AND c.created_at >= ?", (since_iso,)).fetchall()
    events = [{"time": r["time"], "code": r["code"], "type": r["flag"],
               "detail": json.loads(r["meta"] or "{}").get("matched_rule", "")} for r in chat]
    events += [{"time": r["time"], "code": r["code"], "type": "phq_item9", "detail": ""} for r in phq]
    return sorted(events, key=lambda e: e["time"])
