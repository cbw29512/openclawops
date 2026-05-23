from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

PROPOSAL_PATH = DATA / "nothingbuta_staging_copy_proposal.json"
REPORT_PATH = REPORTS / "nothingbuta-local-staging-copy-dry-run.md"

DRY_RUN_ONLY = True

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def load_proposal() -> dict[str, Any]:
    try:
        return json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logging.exception("Failed to load staging proposal.")
        raise SystemExit(1) from exc


def validate_item(item: dict[str, Any]) -> dict[str, Any]:
    source = Path(str(item.get("source_preview_path", "")))
    dest = Path(str(item.get("proposed_staging_path", "")))

    return {
        "name": item.get("name"),
        "slug": item.get("slug"),
        "source": str(source),
        "dest": str(dest),
        "source_exists": source.exists(),
        "checksum_matches_freeze": item.get("checksum_matches_freeze") is True,
        "copy_allowed_in_proposal": item.get("copy_allowed") is True,
        "would_copy": False,
        "reason": "dry_run_only",
    }


def write_report(results: list[dict[str, Any]], blocked: list[dict[str, Any]]) -> None:
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    problems = [
        item for item in results
        if not item["source_exists"] or not item["checksum_matches_freeze"]
    ]

    lines = [
        "# NothingButA Local Staging Copy Dry Run",
        "",
        f"Generated: {now}",
        "",
        "## Summary",
        "",
        f"- Proposed items checked: {len(results)}",
        f"- Blocked / held back: {len(blocked)}",
        f"- Source/checksum problems: {len(problems)}",
        "- Dry run only: true",
        "- Files copied: 0",
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
        "## Checked Items",
        "",
    ]

    for index, item in enumerate(results, start=1):
        lines.extend(
            [
                f"### {index}. {item['name']}",
                "",
                f"- Slug: `{item['slug']}`",
                f"- Source exists: `{item['source_exists']}`",
                f"- Checksum matches freeze: `{item['checksum_matches_freeze']}`",
                f"- Would copy: `{item['would_copy']}`",
                f"- Reason: `{item['reason']}`",
                f"- Source: `{item['source']}`",
                f"- Destination: `{item['dest']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Next Approval Gate",
            "",
            "This was a dry run. Local staging copy still requires explicit Chris approval before any files are copied.",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    proposal = load_proposal()
    items = proposal.get("proposed_items", [])
    blocked = proposal.get("blocked_items", [])

    if not isinstance(items, list):
        logging.error("proposed_items is not a list.")
        raise SystemExit(1)

    results = [validate_item(item) for item in items]
    write_report(results, blocked)

    problem_count = len(
        [
            item for item in results
            if not item["source_exists"] or not item["checksum_matches_freeze"]
        ]
    )

    print("NOTHINGBUTA LOCAL STAGING COPY DRY RUN: PASS" if problem_count == 0 else "NOTHINGBUTA LOCAL STAGING COPY DRY RUN: WARN")
    print(f"checked: {len(results)}")
    print(f"blocked: {len(blocked)}")
    print(f"source_problem_count: {problem_count}")
    print("files_copied: 0")
    print(f"report: {REPORT_PATH}")

    if problem_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()