# mentoring.md: Session 3 - How the app talks
"""Reads settings from .env once at startup and exposes them as plain variables.

Every other file imports settings from here, so changing the model, the
strategy set or the timezone only ever means editing .env (never the code).
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Paths are built from this file's location, never from a drive letter, so the
# project works wherever it lives (D:\Projects\stillspace on the dev laptop,
# anywhere on the student's laptop, macOS or Linux).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DATA_DIR = PROJECT_ROOT / "backend" / "data"
PROMPTS_DIR = BACKEND_DATA_DIR / "prompts"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Read .env from the project root even if uvicorn is started from elsewhere.
load_dotenv(PROJECT_ROOT / ".env")

APP_VERSION = "0.1.0"


def _get_bool(name: str, default: bool) -> bool:
    """Turn a .env text value like 'true' / 'False' / '1' into a real bool."""
    value = os.getenv(name, "").strip().lower()
    if value == "":
        return default
    return value in ("1", "true", "yes", "on")


def _get_int(name: str, default: int) -> int:
    """Read a whole number from .env, falling back to the default if it is not a number."""
    try:
        return int(os.getenv(name, "").strip())
    except ValueError:
        return default


def _get_text(name: str, default: str) -> str:
    """Read text from .env; an empty value counts as 'not set'."""
    value = os.getenv(name, "").strip()
    return value or default


LLM_BASE_URL = _get_text("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_API_KEY = _get_text("LLM_API_KEY", "")
LLM_MODEL = _get_text("LLM_MODEL", "qwen/qwen3-8b")
CLASSIFIER_MODEL = _get_text("CLASSIFIER_MODEL", LLM_MODEL)
MOCK_MODE = _get_bool("MOCK_MODE", False)
STRATEGY_SET = _get_text("STRATEGY_SET", "strategies_4")
INCLUDE_CHECKINS_IN_PROMPT = _get_bool("INCLUDE_CHECKINS_IN_PROMPT", True)
HISTORY_TURNS = _get_int("HISTORY_TURNS", 6)
APP_TIMEZONE = _get_text("APP_TIMEZONE", "Asia/Kolkata")
DEMO_MODE = _get_bool("DEMO_MODE", True)
FOLLOWUP_CONTACT = _get_text("FOLLOWUP_CONTACT", "")

# A relative DB_PATH is resolved from the project root so the database always
# lands inside the project folder (and therefore on D: for the developer).
DB_PATH = PROJECT_ROOT / _get_text("DB_PATH", "data/stillspace.db")

# Helplines live in one place so the UI, the crisis reply and the docs can
# never show different numbers (implementation.md D-06).
HELPLINES = [
    {"name": "Tele-MANAS", "number": "14416", "alt": "1-800-891-4416", "note": "free, 24x7"},
    {"name": "Emergency", "number": "112", "alt": "", "note": ""},
]


def is_mock_mode() -> bool:
    """Mock mode is on when forced in .env or when there is no API key to use."""
    return MOCK_MODE or LLM_API_KEY == ""


def load_strategies() -> list[dict]:
    """Load the strategy list named by STRATEGY_SET from backend/data/<name>.json.

    Read fresh on each call so a student can edit the JSON file and see the
    change after a page reload. Fails loudly if the file is missing, because
    a silent fallback would hide a typo in .env.
    """
    path = BACKEND_DATA_DIR / f"{STRATEGY_SET}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Strategy file not found: {path}. Check STRATEGY_SET in .env "
            "(expected strategies_4 or strategies_esconv8)."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)
