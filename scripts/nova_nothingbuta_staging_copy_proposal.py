from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any


# -----------------------------
# State schema:
# ROOT: local OpenClawOps project root.
# FREEZE_JSON: source-of-truth packet of frozen local previews.
# JSON_OUT / MD_OUT: local-only proposal outputs.
# STAGING_ROOT: proposed local staging destination. No files are copied by this script.
# -----------------------------
ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
STAGING_ROOT = ROOT / "nothingbuta" / "staging"

FREEZE_JSON = DATA / "nothingbuta_release_freeze_packet.json"
JSON_OUT = DATA / "nothingbuta_staging_copy_proposal.json"
MD_OUT = REPORTS / "nothingbuta-staging-copy-proposal.md"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def sha256_file(path: Path) -> str:
    """Hash a file so the proposal can detect drift before any staging copy."""
    digest = hashlib.sha256()

    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)

        return digest.hexdigest()
    except Exception as exc:
        logging.exception("Failed to checksum file: %s", path)
        raise SystemExit(1) from exc


def load_freeze_packet() -> dict[str, Any]:
    """Load the frozen preview packet created by the release freeze step."""
    try:
        return json.loads(FREEZE_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        logging.exception("Failed to load freeze packet.")
        raise SystemExit(1) from exc


def build_proposal_item(item: dict[str, Any]) -> dict[str, Any]:
    """Create one proposed staging-copy item without copying anything."""
    source_path = Path(str(item.get("local_preview_path", "")))
    slug = str(item.get("slug", "missing-slug"))

    proposed_dest = STAGING_ROOT / slug / "index.html"
    expected_hash = str(item.get("sha256", ""))
    actual_hash = sha256_file(source_path) if source_path.exists() else None

    hash_matches = actual_hash == expected_hash

    return {
        "name": item.get("name"),
        "slug": slug,
        "source_preview_path": str(source_path),
        "source_exists": source_path.exists(),
        "expected_sha256": expected_hash,
        "actual_sha256": actual_hash,
        "checksum_matches_freeze": hash_matches,
        "proposed_staging_path": str(proposed_dest),
        "copy_allowed": False,
        "requires_chris_approval": True,
    }


def write_outputs(proposal: dict[str, Any]) -> None:
    """Write JSON and Markdown proposal files for review."""
    try:
        JSON_OUT.write_text(json.dumps(proposal, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Staging Copy Proposal",
            "",
            f"Generated: {proposal['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Proposed staging copies: {proposal['proposed_count']}",
            f"- Blocked / held back: {proposal['blocked_count']}",
            f"- Source problems: {proposal['source_problem_count']}",
            "- Copy allowed: false",
            "- Commit allowed: false",
            "- Push allowed: false",
            "- Publish allowed: false",
            "- GitHub Pages changes allowed: false",
            "- Analytics allowed: false",
            "- Ads allowed: false",
            "- Affiliate links allowed: false",
            "- Lead capture allowed: false",
            "- Outreach allowed: false",
            "- Requires Chris approval before staging copy: true",
            "",
            "## Proposed Local Staging Items",
            "",
        ]

        for index, item in enumerate(proposal["proposed_items"], start=1):
            lines.extend(
                [
                    f"### {index}. {item['name']}",
                    "",
                    f"- Slug: `{item['slug']}`",
                    f"- Source exists: `{item['source_exists']}`",
                    f"- Checksum matches freeze: `{item['checksum_matches_freeze']}`",
                    f"- Source preview: `{item['source_preview_path']}`",
                    f"- Proposed staging path: `{item['proposed_staging_path']}`",
                    f"- Copy allowed: `{item['copy_allowed']}`",
                    "",
                ]
            )

        lines.extend(["## Held Back", ""])

        for item in proposal["blocked_items"]:
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

        lines.extend(
            [
                "## Next Approval Gate",
                "",
                "No files are copied by this proposal. A separate copy-only staging script may be created only after Chris explicitly approves local staging copy.",
                "",
            ]
        )

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        logging.exception("Failed to write proposal outputs.")
        raise SystemExit(1) from exc


def main() -> None:
    """Build a local-only staging proposal without changing staging files."""
    packet = load_freeze_packet()
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    frozen_items = packet.get("frozen_items", [])
    blocked_items = packet.get("blocked_items", [])

    proposed_items = [build_proposal_item(item) for item in frozen_items]

    source_problems = [
        item for item in proposed_items
        if not item["source_exists"] or not item["checksum_matches_freeze"]
    ]

    proposal = {
        "generated_at": now,
        "purpose": "Local-only staging copy proposal. This script does not copy files.",
        "staging_root": str(STAGING_ROOT),
        "proposed_count": len(proposed_items),
        "blocked_count": len(blocked_items),
        "source_problem_count": len(source_problems),
        "safety": {
            "copy_allowed": False,
            "commit_allowed": False,
            "push_allowed": False,
            "publish_allowed": False,
            "github_pages_changes_allowed": False,
            "analytics_allowed": False,
            "ads_allowed": False,
            "affiliate_links_allowed": False,
            "lead_capture_allowed": False,
            "outreach_allowed": False,
            "requires_chris_approval_before_staging_copy": True,
        },
        "proposed_items": proposed_items,
        "blocked_items": blocked_items,
    }

    write_outputs(proposal)

    status = "PASS" if not source_problems else "WARN"
    print(f"NOTHINGBUTA STAGING COPY PROPOSAL: {status}")
    print(f"proposed_count: {len(proposed_items)}")
    print(f"blocked_count: {len(blocked_items)}")
    print(f"source_problem_count: {len(source_problems)}")
    print(f"json: {JSON_OUT}")
    print(f"markdown: {MD_OUT}")

    if source_problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()