import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("nova_dashboard.activity")

WORKSPACE = Path.home() / "OpenClawOps"
REPORTS = WORKSPACE / "reports"
ACTIVITY_REPORT = REPORTS / "nova-live-activity-feed.json"


def read_recent_activity(limit: int = 100) -> Dict[str, Any]:
    """Return the newest activity events for the dashboard polling endpoint."""
    try:
        if not ACTIVITY_REPORT.exists():
            return {
                "schema_version": "1.0",
                "updated_at": "unknown",
                "event_count": 0,
                "events": [],
            }

        with ACTIVITY_REPORT.open("r", encoding="utf-8-sig") as file:
            payload = json.load(file)

        events = payload.get("events", [])

        return {
            "schema_version": payload.get("schema_version", "1.0"),
            "updated_at": payload.get("updated_at", "unknown"),
            "event_count": len(events),
            "events": events[-limit:],
        }

    except Exception as exc:
        logger.exception("Failed reading activity feed: %s", exc)
        return {
            "schema_version": "1.0",
            "updated_at": "error",
            "event_count": 0,
            "events": [],
            "error": str(exc),
        }
