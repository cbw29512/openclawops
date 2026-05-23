from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path


# Objective:
# Build a local-only release freeze packet for the 24 staged NothingButA pages.
#
# This script DOES NOT:
# - commit
# - push
# - publish
# - change GitHub Pages
# - add analytics
# - add ads
# - add affiliate links
# - add lead capture
# - do outreach


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
)

logger = logging.getLogger("nothingbuta_release_freeze")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
STAGING_DIR = ROOT / "nothingbuta" / "staging"
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

JSON_OUT = DATA_DIR / "nothingbuta_release_freeze_packet.json"
MD_OUT = REPORTS_DIR / "nothingbuta-release-freeze-packet.md"


BLOCKED_ACTIONS = {
    "commit_allowed": False,
    "push_allowed": False,
    "publish_allowed": False,
    "github_pages_changes_allowed": False,
    "analytics_allowed": False,
    "ads_allowed": False,
    "affiliate_links_allowed": False,
    "lead_capture_allowed": False,
    "outreach_allowed": False,
}


def sha256_file(path: Path) -> str:
    """Return a SHA256 checksum for one staged file."""
    try:
        digest = hashlib.sha256()

        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)

        return digest.hexdigest()

    except Exception as exc:
        logger.exception("Failed to hash file: %s", path)
        raise RuntimeError(f"Failed to hash file: {path}") from exc


def collect_staged_pages() -> list[dict]:
    """Collect every staged index.html file as a release candidate."""
    try:
        pages: list[dict] = []

        for index_path in sorted(STAGING_DIR.glob("*/index.html")):
            slug = index_path.parent.name

            pages.append(
                {
                    "slug": slug,
                    "path": str(index_path),
                    "sha256": sha256_file(index_path),
                    "exists": index_path.exists(),
                    "release_candidate": True,
                }
            )

        return pages

    except Exception as exc:
        logger.exception("Failed to collect staged pages")
        raise RuntimeError("Failed to collect staged pages") from exc


def build_packet() -> dict:
    """Build the full freeze packet as machine-readable state."""
    try:
        pages = collect_staged_pages()

        packet = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "project": "NothingButA",
            "release_type": "local_staging_freeze",
            "staging_dir": str(STAGING_DIR),
            "page_count": len(pages),
            "expected_page_count": 24,
            "status": "PASS" if len(pages) == 24 else "BLOCKED",
            "manual_preview_note": "Chris reported staged pages load and seem to work.",
            "blocked_actions": BLOCKED_ACTIONS,
            "rollback_plan": {
                "strategy": "Do not overwrite live/public files until explicit approval.",
                "restore_method": "Keep factory candidates and staging files unchanged until final approval.",
                "minimum_rollback_artifacts": [
                    "nothingbuta_local_staging_copy_proof.json",
                    "nothingbuta_release_freeze_packet.json",
                    "staged index.html SHA256 checksums",
                ],
            },
            "final_approval_checklist": [
                "Confirm 24 staged pages exist.",
                "Confirm all staged pages have SHA256 checksums.",
                "Confirm manual browser preview passed.",
                "Confirm no internal AI/system notes are visible.",
                "Confirm no external actions are enabled.",
                "Confirm Chris explicitly approves the exact next action before publishing or committing.",
            ],
            "pages": pages,
        }

        return packet

    except Exception as exc:
        logger.exception("Failed to build release freeze packet")
        raise RuntimeError("Failed to build release freeze packet") from exc


def write_outputs(packet: dict) -> None:
    """Write JSON and Markdown reports."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        JSON_OUT.write_text(json.dumps(packet, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Release Freeze Packet",
            "",
            f"Generated: {packet['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: {packet['status']}",
            f"- Page count: {packet['page_count']}",
            f"- Expected page count: {packet['expected_page_count']}",
            f"- Staging directory: `{packet['staging_dir']}`",
            f"- Manual preview note: {packet['manual_preview_note']}",
            "",
            "## Blocked External Actions",
            "",
        ]

        for key, value in packet["blocked_actions"].items():
            lines.append(f"- {key}: `{value}`")

        lines.extend(
            [
                "",
                "## Rollback Plan",
                "",
                f"- Strategy: {packet['rollback_plan']['strategy']}",
                f"- Restore method: {packet['rollback_plan']['restore_method']}",
                "",
                "Minimum rollback artifacts:",
            ]
        )

        for artifact in packet["rollback_plan"]["minimum_rollback_artifacts"]:
            lines.append(f"- `{artifact}`")

        lines.extend(["", "## Final Approval Checklist", ""])

        for item in packet["final_approval_checklist"]:
            lines.append(f"- [ ] {item}")

        lines.extend(["", "## Frozen Staged Pages", ""])

        for page in packet["pages"]:
            lines.extend(
                [
                    f"### {page['slug']}",
                    "",
                    f"- Path: `{page['path']}`",
                    f"- SHA256: `{page['sha256']}`",
                    f"- Release candidate: `{page['release_candidate']}`",
                    "",
                ]
            )

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    except Exception as exc:
        logger.exception("Failed to write release freeze outputs")
        raise RuntimeError("Failed to write release freeze outputs") from exc


def main() -> int:
    """Run the local-only freeze packet generator."""
    try:
        packet = build_packet()
        write_outputs(packet)

        print("NOTHINGBUTA RELEASE FREEZE PACKET:", packet["status"])
        print("pages:", packet["page_count"])
        print("json:", JSON_OUT)
        print("markdown:", MD_OUT)

        return 0 if packet["status"] == "PASS" else 1

    except Exception as exc:
        logger.exception("Release freeze packet failed")
        print("NOTHINGBUTA RELEASE FREEZE PACKET: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())