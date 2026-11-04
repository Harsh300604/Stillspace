-- Stillspace tables for SQLite (local use and the student course). Spec section 9.
-- Created automatically on start-up; "IF NOT EXISTS" makes it safe to run every time.
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    dob TEXT NULL,
    preferred_strategy TEXT DEFAULT 'Automatic',
    setup_done INTEGER DEFAULT 0,
    demo_day_offset INTEGER DEFAULT 0,
    age_group TEXT NULL,               -- '18plus' | 'under18' (online version, D-50)
    guardian_consent INTEGER DEFAULT 0,
    consent_at TEXT NULL
);
CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY,
    participant_id INTEGER NOT NULL REFERENCES participants(id),
    type TEXT NOT NULL,                -- setup | daily | fortnightly | post_session
    answers_json TEXT NOT NULL,        -- unanswered questions are absent keys, never 0
    phq_total INTEGER NULL,            -- only when all 9 PHQ items are answered
    phq_band TEXT NULL,
    phq_complete INTEGER DEFAULT 0,
    item9_flag INTEGER DEFAULT 0,
    session_id INTEGER NULL,           -- post_session only
    local_date TEXT NOT NULL,          -- YYYY-MM-DD in APP_TIMEZONE (+ demo offset)
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
    role TEXT NOT NULL,                -- user | assistant
    text TEXT NOT NULL,
    requested_strategy TEXT NULL,
    classified_strategy TEXT NULL,
    used_strategy TEXT NULL,
    meta_json TEXT NULL,
    safety_flag TEXT DEFAULT 'none',   -- none | keyword | classifier
    source TEXT NULL,                  -- llm | mock | safety | fallback
    model TEXT NULL,
    latency_ms INTEGER NULL,
    created_at TEXT NOT NULL
);
