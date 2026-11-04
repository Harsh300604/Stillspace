# mentoring.md: Session 13 - Evaluation design
"""Simple rate limits kept in memory (D-49).

Why: online, every chat message costs money at the model provider, and a sign-in
form can be attacked by guessing codes. These limits stop both without any
extra framework.

    chat:    CHAT_LIMIT_PER_HOUR per participant, and DAILY_CHAT_LIMIT for the whole app
    sign-in: LOGIN_LIMIT_PER_MINUTE per IP address

The safety reply is never limited: routes/chat.py checks safety BEFORE these limits.
Limits reset when the server restarts and are per server process, which is fine
for one small instance on Railway or Render.
"""

import threading
import time
from collections import defaultdict, deque

_lock = threading.Lock()  # FastAPI runs normal routes in several threads at once
_hits: dict[str, deque] = defaultdict(deque)


def allow(key: str, limit: int, window_seconds: int) -> bool:
    """Record one attempt for `key` and say whether it is still within `limit` per window.

    A limit of 0 or less means "no limit".
    """
    if limit <= 0:
        return True
    now = time.monotonic()
    with _lock:
        hits = _hits[key]
        while hits and now - hits[0] > window_seconds:
            hits.popleft()  # forget attempts that are older than the window
        if len(hits) >= limit:
            return False
        hits.append(now)
        return True


def reset() -> None:
    """Forget all attempts (used by tests)."""
    with _lock:
        _hits.clear()
