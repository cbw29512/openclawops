import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("nova_dashboard.state")

# -----------------------------
# State / Data Schema
# -----------------------------
# Dashboard is local-only.
# It reads Nova reports and can only apply local Boost/Bury votes.
# It does not publish, sell, outreach, spend, push, commit, or modify live sites.

WORKSPACE = Path.home() / "OpenClawOps"
REPORTS = WORKSPACE / "reports"
DATA = WORKSPACE / "data"
SCRIPTS = WORKSPACE / "scripts"

DAILY_REPORT = REPORTS / "daily-money-report.json"
LATEST_CYCLE = REPORTS / "ops-cycle" / "latest-cycle.json"
QUEUE_REPORT = REPORTS / "source-review-queue.json"
WORK_ORDER = REPORTS / "nova-work-order.json"
SIMULATION_RUN = REPORTS / "nova-simulation-research-run.json"
FINDER_FEE_CATEGORY = REPORTS / "finder-fee-category-simulation.json"
ACTIVITY_FEED = REPORTS / "nova-live-activity-feed.json"

OPPORTUNITY_INDEX = DATA / "opportunity_index.json"
LEARNING_LEDGER = DATA / "learning_ledger.json"

VOTE_SCRIPT = SCRIPTS / "nova-opportunity-vote.ps1"


def read_json(path: Path, fallback: Dict[str, Any]) -> Dict[str, Any]:
    """Read JSON safely so one bad/missing file does not crash the cockpit."""
    try:
        if not path.exists():
            logger.warning("Missing JSON file: %s", path)
            return fallback

        with path.open("r", encoding="utf-8-sig") as file:
            return json.load(file)

    except Exception as exc:
        logger.exception("Failed reading %s: %s", path, exc)
        return fallback


def get_items_by_bucket(queue: Dict[str, Any], bucket: str) -> List[Dict[str, Any]]:
    """Return queue items for one dashboard section."""
    try:
        return [
            item for item in queue.get("items", [])
            if item.get("recommended_dashboard_bucket") == bucket
        ]
    except Exception as exc:
        logger.exception("Failed filtering bucket %s: %s", bucket, exc)
        return []


def sort_attempts_by_score(attempts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Show the highest-scoring simulations first."""
    try:
        return sorted(
            attempts,
            key=lambda item: int(item.get("simulation_score", 0)),
            reverse=True,
        )
    except Exception as exc:
        logger.exception("Failed sorting simulation attempts: %s", exc)
        return attempts


def get_freshest_cycle(
    daily: Dict[str, Any],
    latest_cycle_report: Dict[str, Any],
    activity_feed: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Pick the freshest visible cycle for the dashboard header.

    Priority:
    1. Newest activity event with a real ops-* cycle_id
    2. latest-cycle.json
    3. daily-money-report.json latest_cycle
    """
    try:
        events = activity_feed.get("events", [])

        for event in reversed(events):
            cycle_id = str(event.get("cycle_id", "")).strip()

            if cycle_id.startswith("ops-"):
                status = "running"

                if event.get("event_type") == "cycle_complete":
                    status = str(event.get("details", {}).get("status", "pass"))

                if event.get("level") == "PASS":
                    status = "pass"

                if event.get("level") == "FAIL":
                    status = "fail"

                return {
                    "cycle_id": cycle_id,
                    "status": status,
                    "generated_at": event.get("timestamp", "unknown"),
                    "source": "activity_feed",
                }

        if latest_cycle_report.get("cycle_id"):
            return {
                "cycle_id": latest_cycle_report.get("cycle_id", "unknown"),
                "status": latest_cycle_report.get("status", "unknown"),
                "generated_at": latest_cycle_report.get("generated_at", "unknown"),
                "source": "latest_cycle_json",
            }

        latest_daily = daily.get("latest_cycle", {})

        return {
            "cycle_id": latest_daily.get("cycle_id", "unknown"),
            "status": latest_daily.get("status", "unknown"),
            "generated_at": latest_daily.get("generated_at", "unknown"),
            "source": "daily_report",
        }

    except Exception as exc:
        logger.exception("Failed selecting freshest cycle: %s", exc)
        return {"cycle_id": "unknown", "status": "error", "generated_at": "unknown", "source": "error"}


def build_dashboard_state() -> Dict[str, Any]:
    """Build the complete dashboard state from local Nova reports."""
    try:
        daily = read_json(DAILY_REPORT, {})
        latest_cycle_report = read_json(LATEST_CYCLE, {})
        queue = read_json(QUEUE_REPORT, {})
        work_order = read_json(WORK_ORDER, {})
        simulation_run = read_json(SIMULATION_RUN, {})
        finder_fee = read_json(FINDER_FEE_CATEGORY, {})
        learning = read_json(LEARNING_LEDGER, {})
        index = read_json(OPPORTUNITY_INDEX, {})
        activity_feed = read_json(ACTIVITY_FEED, {})

        latest_cycle = get_freshest_cycle(
            daily=daily,
            latest_cycle_report=latest_cycle_report,
            activity_feed=activity_feed,
        )

        audit = daily.get("audit", {})
        counts = queue.get("counts", {})
        attempts = sort_attempts_by_score(simulation_run.get("attempts", []))

        return {
            "system": {
                "cycle_id": latest_cycle.get("cycle_id", "unknown"),
                "cycle_status": latest_cycle.get("status", "unknown"),
                "cycle_generated_at": latest_cycle.get("generated_at", "unknown"),
                "cycle_source": latest_cycle.get("source", "unknown"),
                "audit_pass": audit.get("pass", 0),
                "audit_warn": audit.get("warn", 0),
                "audit_fail": audit.get("fail", 0),
                "needs_chris_signal": counts.get("needs_chris_signal", 0),
                "positive_queue": counts.get("positive_queue", 0),
                "idea_pit": counts.get("idea_pit", 0),
            },
            "work_order": {
                "work_order_id": work_order.get("work_order_id", "unknown"),
                "generated_at": work_order.get("generated_at", "unknown"),
                "items": work_order.get("items", []),
            },
            "simulation": {
                "run_id": simulation_run.get("run_id", "unknown"),
                "generated_at": simulation_run.get("generated_at", "unknown"),
                "mode": simulation_run.get("mode", "unknown"),
                "attempts": attempts,
            },
            "finder_fee": {
                "run_id": finder_fee.get("run_id", "unknown"),
                "generated_at": finder_fee.get("generated_at", "unknown"),
                "mode": finder_fee.get("mode", "unknown"),
                "top_categories": finder_fee.get("top_categories", []),
                "safety": finder_fee.get("safety", ""),
            },
            "learning": {
                "updated_at": learning.get("updated_at", "unknown"),
                "summary": learning.get("summary", {}),
                "patterns_to_repeat": learning.get("patterns_to_repeat", []),
                "patterns_to_avoid": learning.get("patterns_to_avoid", []),
            },
            "queues": {
                "positive_queue": get_items_by_bucket(queue, "positive_queue"),
                "needs_chris_signal": get_items_by_bucket(queue, "needs_chris_signal"),
                "idea_pit": get_items_by_bucket(queue, "idea_pit"),
            },
            "opportunity_index_updated_at": index.get("updated_at", "unknown"),
            "safety": {
                "external_actions_enabled": False,
                "spending_enabled": False,
                "outreach_enabled": False,
                "publishing_enabled": False,
            },
        }

    except Exception as exc:
        logger.exception("Failed to build dashboard state: %s", exc)
        return {
            "system": {"cycle_status": "error", "audit_fail": 1},
            "work_order": {"items": []},
            "simulation": {"attempts": []},
            "finder_fee": {"top_categories": []},
            "learning": {"summary": {}, "patterns_to_repeat": [], "patterns_to_avoid": []},
            "queues": {"positive_queue": [], "needs_chris_signal": [], "idea_pit": []},
            "error": str(exc),
        }


def apply_vote(item_id: str, vote: str) -> Dict[str, Any]:
    """Apply Boost/Bury through the existing local PowerShell script."""
    try:
        if vote not in {"approve", "disapprove"}:
            return {"ok": False, "message": f"Invalid vote: {vote}"}

        if not item_id.startswith("idx-"):
            return {"ok": False, "message": f"Invalid item id: {item_id}"}

        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(VOTE_SCRIPT),
                "-ItemId",
                item_id,
                "-Vote",
                vote,
                "-Note",
                "Dashboard local priority vote.",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if completed.returncode != 0:
            return {"ok": False, "message": completed.stderr or completed.stdout}

        return {"ok": True, "message": completed.stdout.strip()}

    except Exception as exc:
        logger.exception("Vote failed: %s", exc)
        return {"ok": False, "message": str(exc)}
