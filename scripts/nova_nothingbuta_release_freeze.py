from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

STAGING_PATH = ROOT / "nothingbuta" / "staging" / "nba-util-0001" / "index.html"
REGISTRY_PATH = DATA_DIR / "nothingbuta_release_registry.json"
AUDIT_JSON_PATH = REPORTS_DIR / "nothingbuta-enterprise-audit.json"
FREEZE_JSON_PATH = DATA_DIR / "nothingbuta_release_freeze.json"
FINAL_REVIEW_PATH = REPORTS_DIR / "nothingbuta-final-publish-review.md"


def now_iso() -> str:
    """Return an audit-friendly timestamp."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    """Read JSON with BOM tolerance and meaningful error messages."""
    try:
        if not path.exists():
            raise FileNotFoundError(f"Missing required file: {path}")
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise RuntimeError(f"Failed reading JSON {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    """Write clean UTF-8 JSON."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"Failed writing JSON {path}: {exc}") from exc


def write_text(path: Path, value: str) -> None:
    """Write clean UTF-8 text."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"Failed writing text {path}: {exc}") from exc


def sha256_file(path: Path) -> str:
    """Hash the frozen staging file so future edits can be detected."""
    digest = hashlib.sha256()

    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest().upper()
    except Exception as exc:
        raise RuntimeError(f"Failed hashing {path}: {exc}") from exc


def freeze_release() -> dict[str, Any]:
    """Freeze the enterprise-audited staging release."""
    if not STAGING_PATH.exists():
        raise FileNotFoundError(f"Missing staging file: {STAGING_PATH}")

    audit = read_json(AUDIT_JSON_PATH)
    registry = read_json(REGISTRY_PATH)

    if audit.get("status") != "pass":
        raise RuntimeError("Cannot freeze release: enterprise audit did not pass.")

    releases = registry.get("releases", [])
    if not releases:
        raise RuntimeError("Cannot freeze release: registry has no releases.")

    release = releases[0]

    if release.get("enterprise_audit_status") != "pass":
        raise RuntimeError("Cannot freeze release: registry does not show enterprise audit pass.")

    timestamp = now_iso()
    file_hash = sha256_file(STAGING_PATH)
    file_size = STAGING_PATH.stat().st_size

    freeze = {
        "freeze_id": "nothingbuta-release-freeze-nba-util-0001-v1",
        "created_at": timestamp,
        "release_id": release.get("release_id"),
        "candidate_id": release.get("candidate_id"),
        "site_name": release.get("site_name"),
        "state": "release_frozen",
        "staging_path": release.get("staging_path"),
        "sha256": file_hash,
        "file_size_bytes": file_size,
        "enterprise_audit_status": audit.get("status"),
        "audit_pass_count": int(audit.get("pass_count", 0)),
        "audit_warn_count": int(audit.get("warn_count", 0)),
        "audit_fail_count": int(audit.get("fail_count", 0)),
        "rollback_source": release.get("preview_source"),
        "final_chris_approval_required": True,
        "publish_allowed": False,
        "external_action_allowed": False,
        "domain_purchase_allowed": False,
        "ads_allowed": False,
        "affiliate_links_allowed": False,
        "lead_capture_allowed": False,
        "commit_push_allowed": False,
        "recommended_first_host": "GitHub Pages static hosting, after final Chris approval",
        "notes": [
            "Release is frozen locally.",
            "Any change to the staging HTML should require re-audit and a new checksum.",
            "Publishing remains blocked until explicit final approval."
        ],
    }

    release.update(
        {
            "state": "release_frozen",
            "release_freeze_status": "frozen",
            "release_freeze_at": timestamp,
            "release_sha256": file_hash,
            "final_chris_approval_required": True,
            "publish_allowed": False,
            "external_action_allowed": False,
            "domain_purchase_allowed": False,
            "ads_allowed": False,
            "affiliate_links_allowed": False,
            "lead_capture_allowed": False,
            "commit_push_allowed": False,
        }
    )

    registry["updated_at"] = timestamp
    registry["active_release_id"] = release.get("release_id")
    registry["releases"][0] = release

    write_json(FREEZE_JSON_PATH, freeze)
    write_json(REGISTRY_PATH, registry)

    final_review = f"""# NothingButA Final Publish Review

Generated: {timestamp}

## Status

RELEASE FROZEN — FINAL CHRIS APPROVAL REQUIRED

## Release

- Release ID: {release.get("release_id")}
- Candidate ID: {release.get("candidate_id")}
- Site: {release.get("site_name")}
- State: release_frozen
- Staging file: {STAGING_PATH}
- SHA256: {file_hash}
- File size: {file_size} bytes

## Enterprise Audit

- Status: {audit.get("status")}
- Pass: {audit.get("pass_count")}
- Warn: {audit.get("warn_count")}
- Fail: {audit.get("fail_count")}

## Safety Gates

- Publishing: disabled
- External actions: disabled
- Domain purchase: disabled
- Ads: disabled
- Affiliate links: disabled
- Lead capture: disabled
- Commits/pushes: disabled

## Final Approval Checklist

Before publishing, Chris must explicitly approve:

- Host target
- Final public URL/domain
- SEO title/meta
- Analytics plan, if any
- Whether this remains free/no-monetization for v1
- Final publish action

## Recommended First Host

GitHub Pages static hosting, because this is a single static HTML utility with no backend dependency.

## Rollback Plan

If anything breaks after publishing, revert to the frozen staging file matching this SHA256:

{file_hash}

## Important

Any edit to the staged file after this point requires a new enterprise audit and a new release freeze.
"""

    write_text(FINAL_REVIEW_PATH, final_review)

    return freeze


def main() -> None:
    """Run release freeze and print proof."""
    try:
        freeze = freeze_release()

        print("NOTHINGBUTA RELEASE FREEZE: PASS")
        print("Freeze JSON:", FREEZE_JSON_PATH)
        print("Final review:", FINAL_REVIEW_PATH)
        print("SHA256:", freeze["sha256"])
    except Exception as exc:
        print("NOTHINGBUTA RELEASE FREEZE: FAIL")
        print(str(exc))
        raise


if __name__ == "__main__":
    main()