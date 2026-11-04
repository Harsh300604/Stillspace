# mentoring.md: Session 3 - How the app talks
"""The FastAPI app: one process that serves both the API and the web page.

Start it from the project folder with:
    uvicorn backend.main:app --reload
"""

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend import config, db
from backend.routes import chat, checkins, config_route, participants, sessions

# Online, some settings are required before anything else happens (D-46).
for level, problem in config.production_problems():
    print(f"[startup] {level.upper()}: {problem}")
if any(level == "stop" for level, _ in config.production_problems()):
    raise SystemExit("[startup] Fix the settings above in your .env (or the host's variables) and start again.")

# Create any missing tables before the first request (safe to repeat every start).
db.create_tables()

# Online, FastAPI's automatic /docs, /redoc and /openapi.json pages are switched off,
# so the API is not advertised to visitors.
docs = {} if not config.IS_PRODUCTION else {"docs_url": None, "redoc_url": None, "openapi_url": None}
app = FastAPI(title="Stillspace", version=config.APP_VERSION, **docs)

# Each routes/ file owns one group of endpoints; main.py just plugs them in.
app.include_router(config_route.router)
app.include_router(participants.router)
app.include_router(checkins.router)
app.include_router(sessions.router)
app.include_router(chat.router)

# /static/styles.css, /static/app.js, ... come straight from the frontend folder.
app.mount("/static", StaticFiles(directory=config.FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the single-page frontend."""
    return FileResponse(config.FRONTEND_DIR / "index.html")


# A readable start-up line helps spot a wrong .env without opening the browser.
print(
    f"[startup] Stillspace {config.APP_VERSION} | env={config.APP_ENV} | strategies={config.STRATEGY_SET} | "
    f"mock_mode={config.is_mock_mode()} | demo_mode={config.DEMO_MODE} | db={db.describe()}"
)
