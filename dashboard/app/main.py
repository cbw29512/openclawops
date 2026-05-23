import logging

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.state import build_dashboard_state, apply_vote

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("nova_dashboard")

app = FastAPI(title="Nova Money Scout Command Center")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """Render the local Nova dashboard."""
    try:
        state = build_dashboard_state()
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "state": state,
            },
        )
    except Exception as exc:
        logger.exception("Dashboard render failed: %s", exc)
        return HTMLResponse(f"<h1>Dashboard error</h1><pre>{exc}</pre>", status_code=500)


@app.get("/api/state")
async def api_state() -> JSONResponse:
    """Return the dashboard state as JSON for future live refresh."""
    try:
        return JSONResponse(build_dashboard_state())
    except Exception as exc:
        logger.exception("State API failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


@app.post("/vote")
async def vote(item_id: str = Form(...), vote_value: str = Form(...)) -> RedirectResponse:
    """Boost or Bury an opportunity item.

    This calls the existing local vote script. It does not publish, sell,
    outreach, spend, commit, push, or change live assets.
    """
    try:
        result = apply_vote(item_id=item_id, vote=vote_value)

        if not result.get("ok"):
            logger.error("Vote failed: %s", result.get("message"))
        else:
            logger.info("Vote applied: %s %s", item_id, vote_value)

        return RedirectResponse(url="/", status_code=303)

    except Exception as exc:
        logger.exception("Vote endpoint failed: %s", exc)
        return RedirectResponse(url="/", status_code=303)

# Live activity feed endpoint.
# This returns observable operations only, not private chain-of-thought.
from app.activity import read_recent_activity

@app.get("/activity")
async def activity_feed():
    return read_recent_activity(limit=100)

# === NOTHINGBUTA_ROUTE_INTEGRATION START ===
try:
    from .nothingbuta_routes import router as nothingbuta_router
except ImportError:
    from nothingbuta_routes import router as nothingbuta_router

app.include_router(nothingbuta_router)
# === NOTHINGBUTA_ROUTE_INTEGRATION END ===
