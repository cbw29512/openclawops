from __future__ import annotations

import hashlib
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path


# Objective:
# Copy the frozen 24 NothingButA staged pages into the local Git repo docs folder.
#
# This script DOES:
# - create a timestamped backup of docs
# - copy 24 staged page folders into docs
# - verify copied index.html hashes
# - write local proof reports
#
# This script DOES NOT:
# - commit
# - push
# - publish
# - change GitHub Pages settings
# - add analytics
# - add ads
# - add affiliate links
# - add lead capture
# - do outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_local_docs_copy")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
STAGING_DIR = ROOT / "nothingbuta" / "staging"
REPO_ROOT = ROOT / "nothingbuta" / "github" / "nothingbuta"
DOCS_DIR = REPO_ROOT / "docs"
BACKUP_ROOT = ROOT / "nothingbuta" / "docs_backups"
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

JSON_OUT = DATA_DIR / "nothingbuta_local_docs_copy_proof.json"
MD_OUT = REPORTS_DIR / "nothingbuta-local-docs-copy-proof.md"

EXPECTED_PAGE_COUNT = 24

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
    """Hash one file so source and copied target can be compared exactly."""
    try:
        digest = hashlib.sha256()

        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)

        return digest.hexdigest()

    except Exception as exc:
        logger.exception("Hash failed for %s", path)
        raise RuntimeError(f"Hash failed for {path}") from exc


def collect_staged_pages() -> list[dict]:
    """Collect staged page folders that contain index.html."""
    try:
        pages = []

        for source_index in sorted(STAGING_DIR.glob("*/index.html")):
            slug = source_index.parent.name
            pages.append(
                {
                    "slug": slug,
                    "source_dir": source_index.parent,
                    "source_index": source_index,
                    "target_dir": DOCS_DIR / slug,
                    "target_index": DOCS_DIR / slug / "index.html",
                    "source_sha256": sha256_file(source_index),
                }
            )

        return pages

    except Exception as exc:
        logger.exception("Failed to collect staged pages")
        raise RuntimeError("Failed to collect staged pages") from exc


def validate_preflight(pages: list[dict]) -> None:
    """Fail closed before touching docs if anything looks unsafe."""
    try:
        if len(pages) != EXPECTED_PAGE_COUNT:
            raise RuntimeError(f"Expected 24 staged pages, found {len(pages)}")

        if not REPO_ROOT.exists():
            raise RuntimeError(f"Repo root missing: {REPO_ROOT}")

        if not DOCS_DIR.exists():
            raise RuntimeError(f"Docs folder missing: {DOCS_DIR}")

        existing_targets = [
            str(page["target_dir"])
            for page in pages
            if page["target_dir"].exists()
        ]

        if existing_targets:
            raise RuntimeError(
                "Refusing to overwrite existing docs folders: "
                + json.dumps(existing_targets, indent=2)
            )

    except Exception as exc:
        logger.exception("Preflight failed")
        raise RuntimeError("Preflight failed") from exc


def backup_docs() -> Path:
    """Create a timestamped backup before local repo files are changed."""
    try:
        BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = BACKUP_ROOT / f"docs-before-24-copy-{timestamp}"

        shutil.copytree(DOCS_DIR, backup_dir)

        return backup_dir

    except Exception as exc:
        logger.exception("Docs backup failed")
        raise RuntimeError("Docs backup failed") from exc


def copy_and_verify_pages(pages: list[dict]) -> list[dict]:
    """Copy staged folders into docs and verify index.html hash matches."""
    results = []

    try:
        for page in pages:
            shutil.copytree(page["source_dir"], page["target_dir"])

            target_sha256 = sha256_file(page["target_index"])
            verified = target_sha256 == page["source_sha256"]

            results.append(
                {
                    "slug": page["slug"],
                    "source": str(page["source_index"]),
                    "target": str(page["target_index"]),
                    "source_sha256": page["source_sha256"],
                    "target_sha256": target_sha256,
                    "copied": True,
                    "verified": verified,
                }
            )

            if not verified:
                raise RuntimeError(f"Hash verification failed for {page['slug']}")

        return results

    except Exception as exc:
        logger.exception("Copy or verification failed")
        raise RuntimeError("Copy or verification failed") from exc


def write_reports(backup_dir: Path, results: list[dict]) -> dict:
    """Write machine-readable and human-readable proof reports."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "project": "NothingButA",
            "status": "PASS" if all(item["verified"] for item in results) else "FAILED",
            "copied": len(results),
            "verified": sum(1 for item in results if item["verified"]),
            "repo_root": str(REPO_ROOT),
            "docs_dir": str(DOCS_DIR),
            "backup_dir": str(backup_dir),
            "blocked_actions": BLOCKED_ACTIONS,
            "results": results,
        }

        JSON_OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Local Docs Copy Proof",
            "",
            f"Generated: {proof['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: {proof['status']}",
            f"- Copied: {proof['copied']}",
            f"- Verified: {proof['verified']}",
            f"- Repo root: `{proof['repo_root']}`",
            f"- Docs directory: `{proof['docs_dir']}`",
            f"- Backup directory: `{proof['backup_dir']}`",
            "",
            "## Blocked External Actions",
            "",
        ]

        for key, value in BLOCKED_ACTIONS.items():
            lines.append(f"- {key}: `{value}`")

        lines.extend(["", "## Copied Pages", ""])

        for item in results:
            lines.extend(
                [
                    f"### {item['slug']}",
                    "",
                    f"- Copied: `{item['copied']}`",
                    f"- Verified: `{item['verified']}`",
                    f"- Source: `{item['source']}`",
                    f"- Target: `{item['target']}`",
                    f"- SHA256: `{item['target_sha256']}`",
                    "",
                ]
            )

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")
        return proof

    except Exception as exc:
        logger.exception("Writing proof reports failed")
        raise RuntimeError("Writing proof reports failed") from exc


def main() -> int:
    """Run the local-only docs copy gate."""
    try:
        pages = collect_staged_pages()
        validate_preflight(pages)

        backup_dir = backup_docs()
        results = copy_and_verify_pages(pages)
        proof = write_reports(backup_dir, results)

        print("NOTHINGBUTA LOCAL DOCS COPY:", proof["status"])
        print("copied:", proof["copied"])
        print("verified:", proof["verified"])
        print("backup:", backup_dir)
        print("json:", JSON_OUT)
        print("markdown:", MD_OUT)

        return 0 if proof["status"] == "PASS" else 1

    except Exception as exc:
        logger.exception("Local docs copy failed")
        print("NOTHINGBUTA LOCAL DOCS COPY: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())