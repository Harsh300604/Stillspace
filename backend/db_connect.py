# mentoring.md: Session 11 - Check-ins and data ethics
"""Opening the database: SQLite locally, Postgres (Supabase) online (D-47).

    DATABASE_URL empty -> SQLite file data/stillspace.db (local use, student course)
    DATABASE_URL set   -> Postgres, e.g. a Supabase project (online version)

Both use the same tables and the same SQL. The only differences are handled
here: Postgres writes placeholders as %s instead of ?, and returns new ids with
"RETURNING id". Everything else in db.py works unchanged.
"""

import sqlite3
from typing import Any
from urllib.parse import urlparse

from backend import config

USING_POSTGRES = bool(config.DATABASE_URL)
Connection = Any  # a sqlite3 or psycopg connection; both have execute(), commit() and close()

# Columns added after the first version (Phase 11). Older SQLite files get them on start-up.
ADDED_PARTICIPANT_COLUMNS = {"age_group": "TEXT NULL", "guardian_consent": "INTEGER DEFAULT 0", "consent_at": "TEXT NULL"}


def get_connection() -> Connection:
    """Open the database. Use it as `with closing(get_connection()) as conn:` so it always closes.

    Rows behave like dicts in both cases: row["code"].
    """
    if USING_POSTGRES:
        import psycopg  # imported here, so local SQLite use works even without it
        from psycopg.rows import dict_row
        # prepare_threshold=None keeps it working through Supabase's connection pooler.
        return psycopg.connect(config.DATABASE_URL, row_factory=dict_row, prepare_threshold=None, connect_timeout=10)
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def run(conn: Connection, sql: str, params: tuple | list = ()) -> Any:
    """Run one SQL statement written with ? placeholders and return the cursor.

    Our SQL never contains a literal "?" or "%", so swapping the placeholder is safe.
    """
    if USING_POSTGRES:
        sql = sql.replace("?", "%s")
    return conn.execute(sql, params)


def insert(conn: Connection, sql: str, params: tuple | list) -> int:
    """Run an INSERT and return the new row's id."""
    if USING_POSTGRES:
        return run(conn, sql + " RETURNING id", params).fetchone()["id"]
    return run(conn, sql, params).lastrowid


def create_tables() -> None:
    """Create missing tables (and add new columns to older SQLite files). Safe on every start-up."""
    schema_file = "schema_postgres.sql" if USING_POSTGRES else "schema_sqlite.sql"
    schema = (config.BACKEND_DATA_DIR / schema_file).read_text(encoding="utf-8")
    conn = get_connection()
    try:
        if USING_POSTGRES:
            conn.execute(schema)  # several statements at once are fine when there are no parameters
        else:
            conn.executescript(schema)
            existing = {row["name"] for row in conn.execute("PRAGMA table_info(participants)")}
            for column, definition in ADDED_PARTICIPANT_COLUMNS.items():
                if column not in existing:
                    conn.execute(f"ALTER TABLE participants ADD COLUMN {column} {definition}")
        conn.commit()
    finally:
        conn.close()


def describe() -> str:
    """Where the data lives, for the start-up line. Never shows the database password."""
    if USING_POSTGRES:
        return f"postgres ({urlparse(config.DATABASE_URL).hostname})"
    return str(config.DB_PATH)
