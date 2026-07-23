"""Bounded activity-feed reader for the local Nova dashboard."""

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("nova_dashboard.activity")
WORKSPACE = Path.home() / "OpenClawOps"
REPORTS = WORKSPACE / "reports"
ACTIVITY_REPORT = REPORTS / "nova-live-activity-feed.json"
MAX_ACTIVITY_LIMIT = 200


def read_recent_activity(limit: int = 100) -> Dict[str, Any]:
    """Return a bounded event tail without exposing local filesystem errors."""
    safe_limit = max(1, min(int(limit), MAX_ACTIVITY_LIMIT))
    try:
        if not ACTIVITY_REPORT.is_file():
            return {
                "schema_version": "1.0",
                "updated_at": "unknown",
                "event_count": 0,
                "events": [],
            }

        with ACTIVITY_REPORT.open("r", encoding="utf-8-sig") as file:
            payload = json.load(file)
        events = payload.get("events", [])
        if not isinstance(events, list):
            raise ValueError("Activity events must be a list")

        return {
            "schema_version": str(payload.get("schema_version", "1.0")),
            "updated_at": str(payload.get("updated_at", "unknown")),
            "event_count": len(events),
            "events": events[-safe_limit:],
        }
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        logger.exception("Failed reading activity feed")
        return {
            "schema_version": "1.0",
            "updated_at": "error",
            "event_count": 0,
            "events": [],
            "error": "Activity feed is unavailable.",
        }
