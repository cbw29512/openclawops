from __future__ import annotations

import json
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def write_reports(proof: dict, json_path: Path, md_path: Path) -> None:
    try:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)

        json_path.write_text(json.dumps(proof, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Growth Autopilot v1",
            "",
            f"Generated: {proof['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: `{proof['status']}`",
            f"- Live quality: `{proof['decision']['little_brother']['live_quality_status']}`",
            f"- Failed live pages: `{proof['decision']['little_brother']['live_quality_failed_pages']}`",
            f"- SEO opportunities: `{proof['decision']['little_brother']['seo_total_opportunities']}`",
            f"- High priority SEO opportunities: `{proof['decision']['little_brother']['seo_high_priority_opportunities']}`",
            f"- Repo dirty: `{proof['decision']['little_brother']['repo_working_tree_dirty']}`",
            "",
            "## Big Brother Review",
            "",
            f"- Review required: `{proof['decision']['big_brother']['review_required']}`",
            f"- Recommendation: {proof['decision']['big_brother']['next_recommendation']}",
            "",
            "## Monetization Gate",
            "",
            f"- Status: `{proof['decision']['monetization']['status']}`",
            f"- Blocked until: {proof['decision']['monetization']['blocked_until']}",
            "",
            "## Traffic Stats",
            "",
            f"- Status: `{proof['decision']['traffic_stats']['status']}`",
            f"- Next step: {proof['decision']['traffic_stats']['next_step']}",
            "",
            "## Safety Gates",
            "",
        ]

        for key, value in proof["safety_gates"].items():
            lines.append(f"- {key}: `{value}`")

        md_path.write_text("\n".join(lines), encoding="utf-8")

    except Exception as exc:
        logger.exception("Failed to write growth reports")
        raise RuntimeError("Failed to write growth reports") from exc
