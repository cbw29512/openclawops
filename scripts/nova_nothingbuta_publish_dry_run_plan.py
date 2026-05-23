from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path


# Objective:
# Build a dry-run publish plan for the frozen 24 NothingButA staged pages.
#
# This script only reads files and writes a local report.
#
# This script DOES NOT:
# - copy files into the repo
# - delete repo files
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

logger = logging.getLogger("nothingbuta_publish_dry_run")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")

STAGING_DIR = ROOT / "nothingbuta" / "staging"

REPO_ROOT = ROOT / "nothingbuta" / "github" / "nothingbuta"
DOCS_DIR = REPO_ROOT / "docs"

DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

JSON_OUT = DATA_DIR / "nothingbuta_publish_dry_run_plan.json"
MD_OUT = REPORTS_DIR / "nothingbuta-publish-dry-run-plan.md"

EXPECTED_PAGE_COUNT = 24


BLOCKED_ACTIONS = {
    "copy_allowed": False,
    "delete_allowed": False,
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
    """Return a stable SHA256 checksum for one file."""
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
    """Read the frozen staged pages and map each one to its intended docs destination."""
    try:
        pages: list[dict] = []

        for source_index in sorted(STAGING_DIR.glob("*/index.html")):
            slug = source_index.parent.name
            target_index = DOCS_DIR / slug / "index.html"

            source_hash = sha256_file(source_index)
            target_exists = target_index.exists()
            target_hash = sha256_file(target_index) if target_exists else None

            if not target_exists:
                action = "would_create"
            elif source_hash == target_hash:
                action = "would_skip_same_hash"
            else:
                action = "would_overwrite_changed_file"

            pages.append(
                {
                    "slug": slug,
                    "source": str(source_index),
                    "target": str(target_index),
                    "source_sha256": source_hash,
                    "target_exists": target_exists,
                    "target_sha256": target_hash,
                    "dry_run_action": action,
                }
            )

        return pages

    except Exception as exc:
        logger.exception("Failed to collect publish dry-run pages")
        raise RuntimeError("Failed to collect publish dry-run pages") from exc


def collect_existing_docs_pages() -> list[dict]:
    """Read existing docs pages so we know what is already in the repo."""
    try:
        existing: list[dict] = []

        if not DOCS_DIR.exists():
            return existing

        for index_path in sorted(DOCS_DIR.glob("*/index.html")):
            slug = index_path.parent.name

            existing.append(
                {
                    "slug": slug,
                    "path": str(index_path),
                    "sha256": sha256_file(index_path),
                }
            )

        return existing

    except Exception as exc:
        logger.exception("Failed to collect existing docs pages")
        raise RuntimeError("Failed to collect existing docs pages") from exc


def build_plan() -> dict:
    """Build the machine-readable dry-run plan."""
    try:
        staged_pages = collect_staged_pages()
        existing_docs_pages = collect_existing_docs_pages()

        staged_slugs = {page["slug"] for page in staged_pages}
        existing_slugs = {page["slug"] for page in existing_docs_pages}

        existing_not_in_staging = sorted(existing_slugs - staged_slugs)

        status = "PASS"

        if len(staged_pages) != EXPECTED_PAGE_COUNT:
            status = "BLOCKED"

        if not REPO_ROOT.exists():
            status = "BLOCKED"

        if not DOCS_DIR.exists():
            status = "BLOCKED"

        plan = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "project": "NothingButA",
            "plan_type": "publish_dry_run",
            "status": status,
            "expected_page_count": EXPECTED_PAGE_COUNT,
            "staged_page_count": len(staged_pages),
            "repo_root": str(REPO_ROOT),
            "docs_dir": str(DOCS_DIR),
            "blocked_actions": BLOCKED_ACTIONS,
            "summary": {
                "would_create": sum(1 for page in staged_pages if page["dry_run_action"] == "would_create"),
                "would_skip_same_hash": sum(1 for page in staged_pages if page["dry_run_action"] == "would_skip_same_hash"),
                "would_overwrite_changed_file": sum(1 for page in staged_pages if page["dry_run_action"] == "would_overwrite_changed_file"),
                "existing_docs_pages_not_in_staging": existing_not_in_staging,
            },
            "rollback_plan": {
                "before_real_copy": "Create a timestamped backup of docs before any approved copy.",
                "restore_method": "Restore docs from the timestamped backup if the approved copy produces bad local preview results.",
                "approval_required": "Chris must explicitly approve the real copy action before any files are changed.",
            },
            "staged_pages": staged_pages,
            "existing_docs_pages": existing_docs_pages,
        }

        return plan

    except Exception as exc:
        logger.exception("Failed to build dry-run plan")
        raise RuntimeError("Failed to build dry-run plan") from exc


def write_outputs(plan: dict) -> None:
    """Write JSON and Markdown reports for review."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        JSON_OUT.write_text(json.dumps(plan, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Publish Dry-Run Plan",
            "",
            f"Generated: {plan['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: {plan['status']}",
            f"- Expected staged pages: {plan['expected_page_count']}",
            f"- Found staged pages: {plan['staged_page_count']}",
            f"- Repo root: `{plan['repo_root']}`",
            f"- Docs directory: `{plan['docs_dir']}`",
            "",
            "## Dry-Run Counts",
            "",
            f"- Would create: {plan['summary']['would_create']}",
            f"- Would skip same hash: {plan['summary']['would_skip_same_hash']}",
            f"- Would overwrite changed file: {plan['summary']['would_overwrite_changed_file']}",
            f"- Existing docs pages not in staging: {plan['summary']['existing_docs_pages_not_in_staging']}",
            "",
            "## Blocked Actions",
            "",
        ]

        for key, value in plan["blocked_actions"].items():
            lines.append(f"- {key}: `{value}`")

        lines.extend(
            [
                "",
                "## Rollback Plan",
                "",
                f"- Before real copy: {plan['rollback_plan']['before_real_copy']}",
                f"- Restore method: {plan['rollback_plan']['restore_method']}",
                f"- Approval required: {plan['rollback_plan']['approval_required']}",
                "",
                "## Staged Page Actions",
                "",
            ]
        )

        for page in plan["staged_pages"]:
            lines.extend(
                [
                    f"### {page['slug']}",
                    "",
                    f"- Dry-run action: `{page['dry_run_action']}`",
                    f"- Source: `{page['source']}`",
                    f"- Target: `{page['target']}`",
                    f"- Source SHA256: `{page['source_sha256']}`",
                    f"- Target exists: `{page['target_exists']}`",
                    f"- Target SHA256: `{page['target_sha256']}`",
                    "",
                ]
            )

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    except Exception as exc:
        logger.exception("Failed to write dry-run outputs")
        raise RuntimeError("Failed to write dry-run outputs") from exc


def main() -> int:
    """Run the dry-run planner."""
    try:
        plan = build_plan()
        write_outputs(plan)

        print("NOTHINGBUTA PUBLISH DRY-RUN PLAN:", plan["status"])
        print("staged_pages:", plan["staged_page_count"])
        print("would_create:", plan["summary"]["would_create"])
        print("would_skip_same_hash:", plan["summary"]["would_skip_same_hash"])
        print("would_overwrite_changed_file:", plan["summary"]["would_overwrite_changed_file"])
        print("existing_docs_pages_not_in_staging:", plan["summary"]["existing_docs_pages_not_in_staging"])
        print("json:", JSON_OUT)
        print("markdown:", MD_OUT)

        return 0 if plan["status"] == "PASS" else 1

    except Exception as exc:
        logger.exception("Publish dry-run plan failed")
        print("NOTHINGBUTA PUBLISH DRY-RUN PLAN: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())