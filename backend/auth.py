# mentoring.md: Session 11 - Check-ins and data ethics
"""Sign-in tokens: how the server knows WHO is asking, on every request (D-60).

The participant code is typed once, on the consent page. If it is accepted, the
server creates a long random token and gives it to the browser. From then on the
browser sends only that token, in the request header

    Authorization: Bearer <token>

and every endpoint finds the participant FROM THE TOKEN. A request can therefore
only ever reach the data of the person who signed in with it: nobody can ask for
someone else's data by typing a different code or session number into a request.

Why this is safer than sending the code every time:
  - the code never appears in web addresses or server logs;
  - a token expires (SIGN_IN_HOURS) and is deleted on "Switch participant";
  - only a SHA-256 hash of each token is stored, so a copy of the database
    cannot be used to sign in;
  - tokens are 256-bit random values: guessing one is not realistic.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request

from backend import config, db

EXPIRED = "Your sign-in has expired or is not valid. Please enter your participant code again."


def hash_token(token: str) -> str:
    """Store and look up tokens by their hash, never the token itself."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_token(conn: db.Connection, participant_id: int) -> dict:
    """Create a new sign-in token for this participant. Returns {"token", "expires_at"}."""
    db.run(conn, "DELETE FROM auth_tokens WHERE expires_at < ?", (db.now_iso(),))  # housekeeping
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=config.SIGN_IN_HOURS)).isoformat(timespec="seconds")
    db.insert(conn, "INSERT INTO auth_tokens (participant_id, token_hash, created_at, expires_at) VALUES (?, ?, ?, ?)",
              (participant_id, hash_token(token), db.now_iso(), expires_at))
    return {"token": token, "expires_at": expires_at}


def token_from_request(request: Request) -> str:
    """Read "Authorization: Bearer <token>", or answer 401 when it is missing."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer ") or not header[7:].strip():
        raise HTTPException(401, EXPIRED)
    return header[7:].strip()


def require_participant(conn: db.Connection, request: Request) -> dict:
    """The signed-in participant for this request, or 401. Every endpoint except sign-in calls this."""
    row = db.run(conn, "SELECT * FROM auth_tokens WHERE token_hash = ?",
                 (hash_token(token_from_request(request)),)).fetchone()
    if row is None or row["expires_at"] < db.now_iso():  # ISO UTC times compare correctly as text
        raise HTTPException(401, EXPIRED)
    participant = db.get_participant_by_id(conn, row["participant_id"])
    if participant is None:  # deleted after signing in (withdrawal)
        raise HTTPException(401, EXPIRED)
    return participant


def revoke_token(conn: db.Connection, request: Request) -> None:
    """Sign out: delete this token so it stops working at once."""
    db.run(conn, "DELETE FROM auth_tokens WHERE token_hash = ?", (hash_token(token_from_request(request)),))
