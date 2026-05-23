from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)


def build_growth_decision(monitor: dict, seo: dict, git_state: dict) -> dict:
    try:
        monitor_status = monitor.get("status", "UNKNOWN")
        failed_pages = int(monitor.get("failed_pages", 0) or 0)

        total_opportunities = int(seo.get("total_opportunities", 0) or 0)
        high_priority = int(seo.get("high_priority_opportunities", 0) or 0)

        working_tree_dirty = bool(git_state.get("status_short"))

        problems: list[str] = []

        if monitor_status != "PASS":
            problems.append("live_quality_monitor_not_pass")

        if failed_pages > 0:
            problems.append("live_quality_failed_pages_present")

        if total_opportunities > 0:
            problems.append("seo_opportunities_present")

        if high_priority > 0:
            problems.append("high_priority_seo_opportunities_present")

        if working_tree_dirty:
            problems.append("repo_working_tree_not_clean")

        status = "PASS" if not problems else "NEEDS_REVIEW"

        if status == "PASS":
            recommendation = (
                "Stay in hourly watch mode. Next growth step is wiring real traffic/search stats "
                "before monetization decisions."
            )
        else:
            recommendation = (
                "Review the listed problems before changing pages, monetization, analytics, "
                "ads, affiliate links, lead capture, or outreach."
            )

        return {
            "status": status,
            "problems": problems,
            "recommendation": recommendation,
            "little_brother": {
                "live_quality_status": monitor_status,
                "live_quality_failed_pages": failed_pages,
                "seo_total_opportunities": total_opportunities,
                "seo_high_priority_opportunities": high_priority,
                "repo_working_tree_dirty": working_tree_dirty,
            },
            "big_brother": {
                "review_required": status != "PASS",
                "reason": problems,
                "next_recommendation": recommendation,
            },
            "traffic_stats": {
                "status": "not_wired",
                "next_step": "Wire Search Console or analytics export before traffic-driven decisions.",
            },
            "monetization": {
                "status": "gated",
                "blocked_until": "traffic source and monetization method are explicitly approved",
            },
        }

    except Exception as exc:
        logger.exception("Failed to build growth decision")
        raise RuntimeError("Failed to build growth decision") from exc
