from __future__ import annotations

import hashlib
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

PROPOSAL_PATH = DATA / "nothingbuta_staging_copy_proposal.json"
JSON_OUT = DATA / "nothingbuta_local_staging_copy_proof.json"
MD_OUT = REPORTS / "nothingbuta-local-staging-copy-proof.md"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def sha256_file(path: Path) -> str:
    """Return SHA256 for a local file so source/staged copies can be proven."""
    try:
        digest = hashlib.sha256()

        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)

        return digest.hexdigest()
    except Exception as exc:
        logging.exception("Failed to hash file: %s", path)
        raise SystemExit(1) from exc


def load_proposal() -> dict[str, Any]:
    """Load the approved local staging proposal."""
    try:
        if not PROPOSAL_PATH.exists():
            raise FileNotFoundError(f"Missing proposal: {PROPOSAL_PATH}")

        proposal = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))

        if not isinstance(proposal, dict):
            raise ValueError("Proposal JSON is not an object.")

        return proposal
    except Exception as exc:
        logging.exception("Failed to load staging proposal.")
        raise SystemExit(1) from exc


def validate_item_before_copy(item: dict[str, Any]) -> tuple[Path, Path, str]:
    """Validate source and checksum before any local copy happens."""
    try:
        source = Path(str(item.get("source_preview_path", "")))
        dest = Path(str(item.get("proposed_staging_path", "")))
        expected_hash = str(item.get("expected_sha256", ""))

        if not source.exists():
            raise FileNotFoundError(f"Missing source preview: {source}")

        actual_hash = sha256_file(source)

        if actual_hash != expected_hash:
            raise ValueError(
                f"Checksum mismatch for {source}. Expected {expected_hash}, got {actual_hash}"
            )

        if not str(dest).startswith(str(ROOT)):
            raise ValueError(f"Destination is outside project root: {dest}")

        if dest.name.lower() != "index.html":
            raise ValueError(f"Destination must be index.html: {dest}")

        return source, dest, actual_hash
    except Exception as exc:
        logging.exception("Pre-copy validation failed.")
        raise SystemExit(1) from exc


def copy_one(item: dict[str, Any]) -> dict[str, Any]:
    """Copy one validated source preview into local staging only."""
    try:
        source, dest, source_hash = validate_item_before_copy(item)

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)

        staged_hash = sha256_file(dest)

        if staged_hash != source_hash:
            raise ValueError(
                f"Staged checksum mismatch for {dest}. Source {source_hash}, staged {staged_hash}"
            )

        return {
            "name": item.get("name"),
            "slug": item.get("slug"),
            "source": str(source),
            "destination": str(dest),
            "source_sha256": source_hash,
            "staged_sha256": staged_hash,
            "copied": True,
            "verified": True,
        }
    except Exception as exc:
        logging.exception("Copy failed for item: %s", item.get("slug"))
        return {
            "name": item.get("name"),
            "slug": item.get("slug"),
            "source": item.get("source_preview_path"),
            "destination": item.get("proposed_staging_path"),
            "copied": False,
            "verified": False,
            "error": str(exc),
        }


def write_outputs(results: list[dict[str, Any]], blocked: list[dict[str, Any]]) -> None:
    """Write machine-readable and human-readable local staging proof."""
    try:
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        failed = [item for item in results if not item.get("verified")]

        payload = {
            "generated_at": now,
            "purpose": "Proof of local-only staging copy for NothingButA 24-ready batch.",
            "copied_count": len([item for item in results if item.get("copied")]),
            "verified_count": len([item for item in results if item.get("verified")]),
            "failed_count": len(failed),
            "blocked_count": len(blocked),
            "safety": {
                "local_staging_copy_completed": True,
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
            "results": results,
            "blocked_items": blocked,
        }

        JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Local Staging Copy Proof",
            "",
            f"Generated: {now}",
            "",
            "## Summary",
            "",
            f"- Copied: {payload['copied_count']}",
            f"- Verified: {payload['verified_count']}",
            f"- Failed: {payload['failed_count']}",
            f"- Blocked: {payload['blocked_count']}",
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
            "## Copied Items",
            "",
        ]

        for index, result in enumerate(results, start=1):
            lines.extend(
                [
                    f"### {index}. {result.get('name')}",
                    "",
                    f"- Slug: `{result.get('slug')}`",
                    f"- Copied: `{result.get('copied')}`",
                    f"- Verified: `{result.get('verified')}`",
                    f"- Source: `{result.get('source')}`",
                    f"- Destination: `{result.get('destination')}`",
                    f"- SHA256: `{result.get('staged_sha256')}`",
                    "",
                ]
            )

        lines.extend(
            [
                "## Next Gate",
                "",
                "Local staging copy is complete. Commit, push, publish, GitHub Pages changes, analytics, ads, affiliate links, lead capture, and outreach remain blocked until Chris explicitly approves that exact action.",
                "",
            ]
        )

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        logging.exception("Failed writing proof outputs.")
        raise SystemExit(1) from exc


def main() -> None:
    """Execute local-only staging copy for the validated 24-ready batch."""
    proposal = load_proposal()

    items = proposal.get("proposed_items", [])
    blocked = proposal.get("blocked_items", [])

    if not isinstance(items, list):
        logging.error("proposed_items is not a list.")
        raise SystemExit(1)

    results = [copy_one(item) for item in items]
    write_outputs(results, blocked)

    failed = [item for item in results if not item.get("verified")]

    print("NOTHINGBUTA LOCAL STAGING COPY: PASS" if not failed else "NOTHINGBUTA LOCAL STAGING COPY: FAIL")
    print(f"copied: {len([item for item in results if item.get('copied')])}")
    print(f"verified: {len([item for item in results if item.get('verified')])}")
    print(f"failed: {len(failed)}")
    print(f"blocked: {len(blocked)}")
    print(f"json: {JSON_OUT}")
    print(f"markdown: {MD_OUT}")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()