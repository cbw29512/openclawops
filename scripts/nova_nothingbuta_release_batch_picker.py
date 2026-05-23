from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

REGISTRY_PATH = DATA_DIR / "nothingbuta_candidate_registry.json"
JSON_OUT = DATA_DIR / "nothingbuta_release_batch_picker.json"
MD_OUT = REPORTS_DIR / "nothingbuta-release-batch-picker.md"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def load_registry() -> dict[str, Any]:
    """Load the current local candidate registry."""
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logging.exception("Failed to load registry.")
        raise SystemExit(1) from exc


def pick_ready_candidates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select only candidates that passed local preview/audit gates."""
    try:
        ready = [
            item for item in items
            if item.get("state") == "local_preview_ready"
            and item.get("audit_status") == "PASS"
            and item.get("local_preview_path")
        ]

        return sorted(
            ready,
            key=lambda item: (
                -int(item.get("strict_quality_score") or 100),
                str(item.get("name", "")),
            ),
        )
    except Exception as exc:
        logging.exception("Failed to pick ready candidates.")
        raise SystemExit(1) from exc


def write_outputs(ready: list[dict[str, Any]], blocked: list[dict[str, Any]]) -> None:
    """Write local-only JSON and Markdown release review packets."""
    try:
        now = datetime.now().astimezone().isoformat(timespec="seconds")

        payload = {
            "generated_at": now,
            "purpose": "Local-only release batch picker for NothingButA ready tool candidates.",
            "safety": {
                "commit_allowed": False,
                "push_allowed": False,
                "publish_allowed": False,
                "github_pages_changes_allowed": False,
                "analytics_allowed": False,
                "ads_allowed": False,
                "affiliate_links_allowed": False,
                "lead_capture_allowed": False,
                "outreach_allowed": False,
            },
            "ready_count": len(ready),
            "blocked_count": len(blocked),
            "selected_candidates": ready,
            "blocked_candidates": blocked,
        }

        JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Release Batch Picker",
            "",
            f"Generated: {now}",
            "",
            "## Summary",
            "",
            f"- Ready candidates: {len(ready)}",
            f"- Blocked candidates: {len(blocked)}",
            "- Commit allowed: false",
            "- Push allowed: false",
            "- Publish allowed: false",
            "- GitHub Pages changes allowed: false",
            "- Analytics allowed: false",
            "- Ads allowed: false",
            "- Affiliate links allowed: false",
            "- Lead capture allowed: false",
            "- Outreach allowed: false",
            "",
            "## Selected Ready Candidates",
            "",
        ]

        for index, item in enumerate(ready, start=1):
            lines.extend(
                [
                    f"### {index}. {item.get('name')}",
                    "",
                    f"- Slug: `{item.get('slug')}`",
                    f"- Tool ID: `{item.get('tool_id')}`",
                    f"- Audit: `{item.get('audit_status')}`",
                    f"- Score: `{item.get('strict_quality_score', 100)}`",
                    f"- Local preview: `{item.get('local_preview_path')}`",
                    "",
                ]
            )

        lines.extend(["## Blocked / Not Selected", ""])

        for item in blocked:
            lines.extend(
                [
                    f"### {item.get('name')}",
                    "",
                    f"- Slug: `{item.get('slug')}`",
                    f"- State: `{item.get('state')}`",
                    f"- Audit: `{item.get('audit_status')}`",
                    f"- Problems: `{item.get('audit_problems')}`",
                    "",
                ]
            )

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    except Exception as exc:
        logging.exception("Failed to write release batch picker outputs.")
        raise SystemExit(1) from exc


def main() -> None:
    registry = load_registry()
    items = registry.get("generated_candidates", [])

    if not isinstance(items, list):
        logging.error("generated_candidates is not a list.")
        raise SystemExit(1)

    ready = pick_ready_candidates(items)
    blocked = [item for item in items if item not in ready]

    write_outputs(ready, blocked)

    print("NOTHINGBUTA RELEASE BATCH PICKER: PASS")
    print(f"ready_count: {len(ready)}")
    print(f"blocked_count: {len(blocked)}")
    print(f"json: {JSON_OUT}")
    print(f"markdown: {MD_OUT}")


if __name__ == "__main__":
    main()