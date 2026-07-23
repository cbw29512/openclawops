"""Authenticated local Nova Dashboard application."""

import logging

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.activity import read_recent_activity
from app.security import (
    allowed_hosts,
    require_authentication,
    require_same_origin,
)
from app.state import apply_vote, build_dashboard_state

try:
    from .nothingbuta_routes import router as nothingbuta_router
except ImportError:
    from nothingbuta_routes import router as nothingbuta_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("nova_dashboard")

app = FastAPI(
    title="Nova Money Scout Command Center",
    docs_url=None,
    redoc_url=None,
    dependencies=[
        Depends(require_authentication),
        Depends(require_same_origin),
    ],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts(),
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """Render the local operator dashboard."""
    try:
        state = build_dashboard_state()
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "state": state},
        )
    except Exception:
        logger.exception("Dashboard render failed")
        return HTMLResponse(
            "<h1>Dashboard unavailable</h1>",
            status_code=500,
        )


@app.get("/api/state")
async def api_state() -> JSONResponse:
    """Return dashboard state without exposing internal exception details."""
    try:
        return JSONResponse(build_dashboard_state())
    except Exception:
        logger.exception("State API failed")
        return JSONResponse(
            {"ok": False, "error": "Dashboard state is unavailable."},
            status_code=500,
        )


@app.post("/vote")
async def vote(
    item_id: str = Form(..., min_length=1, max_length=200),
    vote_value: str = Form(..., pattern="^(boost|bury)$"),
) -> RedirectResponse:
    """Apply a bounded local priority vote."""
    try:
        result = apply_vote(item_id=item_id, vote=vote_value)
        if not result.get("ok"):
            logger.error("Vote operation reported failure")
        else:
            logger.info("Applied local vote for item %s", item_id)
    except Exception:
        logger.exception("Vote endpoint failed")
    return RedirectResponse(url="/", status_code=303)


@app.get("/activity")
async def activity_feed() -> dict:
    return read_recent_activity(limit=100)


app.include_router(nothingbuta_router)
