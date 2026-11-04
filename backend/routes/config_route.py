# mentoring.md: Session 3 - How the app talks
"""GET /api/config: everything the browser needs to draw itself.

The frontend builds its strategy lists, helpline text and the mock/demo tags
from this response, so nothing like that is hard-coded in app.js.
"""

from fastapi import APIRouter

from backend import config

router = APIRouter()


@router.get("/api/config")
def get_config() -> dict:
    """Return public settings. The API key is deliberately never included."""
    strategies = config.load_strategies()
    return {
        "app_version": config.APP_VERSION,
        "strategy_set": config.STRATEGY_SET,
        # Only name + description go to the browser; the model instructions
        # stay on the server where the prompt is built.
        "strategies": [{"name": s["name"], "description": s["description"]} for s in strategies],
        "helplines": config.HELPLINES,
        "mock_mode": config.is_mock_mode(),
        "demo_mode": config.DEMO_MODE,
        "followup_contact": config.FOLLOWUP_CONTACT,
    }
