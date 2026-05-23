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
            "# NothingButA Traffic Intelligence v2",
            "",
            f"Generated: {proof['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: `{proof['status']}`",
            f"- Traffic source status: `{proof['traffic_source_status']}`",
            f"- CSV files found: `{proof['csv_files_found']}`",
            f"- Rows read: `{proof['rows_read']}`",
            f"- Pages analyzed: `{proof['pages_analyzed']}`",
            "",
            "## Top Opportunities",
            "",
        ]

        opportunities = proof.get("opportunities", [])

        if not opportunities:
            lines.append("No traffic opportunities yet. Add Search Console CSV exports to the traffic inbox.")
        else:
            for item in opportunities[:15]:
                ctr_percent = round(float(item.get("ctr", 0.0)) * 100, 2)
                lines.append(
                    f"- `{item['slug']}` score `{item['traffic_score']}` | "
                    f"clicks `{item['clicks']}` | impressions `{item['impressions']}` | "
                    f"CTR `{ctr_percent}%` | position `{round(float(item['position']), 2)}` | "
                    f"{item['opportunity_type']}"
                )

        lines.extend(
            [
                "",
                "## Monetization Gate",
                "",
                "- Monetization remains gated.",
                "- No ads, affiliate links, lead capture, outreach, or spending without Chris approval.",
            ]
        )

        md_path.write_text("\n".join(lines), encoding="utf-8")

    except Exception as exc:
        logger.exception("Failed to write traffic reports")
        raise RuntimeError("Failed to write traffic reports") from exc
