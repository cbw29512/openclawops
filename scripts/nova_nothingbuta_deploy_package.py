from __future__ import annotations

import hashlib
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_deploy_package")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

STAGING_PATH = ROOT / "nothingbuta" / "staging" / "nba-util-0001" / "index.html"
DEPLOY_DIR = ROOT / "nothingbuta" / "deploy_packages" / "nba-util-0001-v1"
DEPLOY_INDEX_PATH = DEPLOY_DIR / "index.html"
MANIFEST_PATH = DEPLOY_DIR / "deploy-manifest.json"
REVIEW_PATH = REPORTS_DIR / "nothingbuta-deploy-package-review.md"

FREEZE_PATH = DATA_DIR / "nothingbuta_release_freeze.json"
REGISTRY_PATH = DATA_DIR / "nothingbuta_release_registry.json"


def now_iso() -> str:
    """Return an audit-friendly timestamp."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    """Read JSON safely and tolerate UTF-8 BOM files."""
    try:
        if not path.exists():
            raise FileNotFoundError(f"Missing required file: {path}")
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        logger.exception("JSON read failed: %s", path)
        raise RuntimeError(f"Failed reading JSON {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    """Write clean UTF-8 JSON."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.exception("JSON write failed: %s", path)
        raise RuntimeError(f"Failed writing JSON {path}: {exc}") from exc


def write_text(path: Path, value: str) -> None:
    """Write clean UTF-8 text."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
    except Exception as exc:
        logger.exception("Text write failed: %s", path)
        raise RuntimeError(f"Failed writing text {path}: {exc}") from exc


def sha256_file(path: Path) -> str:
    """Hash a file so deployment artifacts can be proven unchanged."""
    digest = hashlib.sha256()

    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest().upper()
    except Exception as exc:
        logger.exception("Hash failed: %s", path)
        raise RuntimeError(f"Failed hashing {path}: {exc}") from exc


def build_deploy_package() -> dict[str, Any]:
    """Create a local deploy package from the frozen staging file."""
    if not STAGING_PATH.exists():
        raise FileNotFoundError(f"Missing staging file: {STAGING_PATH}")

    freeze = read_json(FREEZE_PATH)
    registry = read_json(REGISTRY_PATH)

    if freeze.get("state") != "release_frozen":
        raise RuntimeError("Cannot package: release freeze state is not release_frozen.")

    releases = registry.get("releases", [])
    if not releases:
        raise RuntimeError("Cannot package: registry has no releases.")

    release = releases[0]

    if release.get("state") != "release_frozen":
        raise RuntimeError(f"Cannot package: registry release state is {release.get('state')}, expected release_frozen.")

    staging_hash = sha256_file(STAGING_PATH)

    if staging_hash != freeze.get("sha256"):
        raise RuntimeError("Cannot package: staging hash does not match frozen SHA256.")

    DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STAGING_PATH, DEPLOY_INDEX_PATH)

    deploy_hash = sha256_file(DEPLOY_INDEX_PATH)

    if deploy_hash != freeze.get("sha256"):
        raise RuntimeError("Cannot package: deploy hash does not match frozen SHA256.")

    timestamp = now_iso()
    deploy_size = DEPLOY_INDEX_PATH.stat().st_size

    manifest = {
        "manifest_id": "nothingbuta-deploy-package-nba-util-0001-v1",
        "created_at": timestamp,
        "release_id": freeze.get("release_id"),
        "candidate_id": freeze.get("candidate_id"),
        "site_name": freeze.get("site_name"),
        "state": "deploy_package_ready",
        "deploy_path": "nothingbuta/deploy_packages/nba-util-0001-v1/index.html",
        "frozen_sha256": freeze.get("sha256"),
        "deploy_sha256": deploy_hash,
        "file_size_bytes": deploy_size,
        "recommended_first_host": "GitHub Pages",
        "recommended_public_path": "/nothingbuta/debt-payoff-calculator/",
        "publish_allowed": False,
        "external_action_allowed": False,
        "commit_push_allowed": False,
        "final_chris_approval_required": True,
        "notes": [
            "Local deploy package created from frozen staging file.",
            "No publishing, commit, push, domain, ads, affiliate links, or lead capture occurred.",
            "Any edit requires re-audit and new freeze."
        ],
    }

    release.update(
        {
            "state": "deploy_package_ready",
            "deploy_package_status": "ready",
            "deploy_package_at": timestamp,
            "deploy_package_path": manifest["deploy_path"],
            "deploy_sha256": deploy_hash,
            "publish_allowed": False,
            "external_action_allowed": False,
            "commit_push_allowed": False,
            "final_chris_approval_required": True,
        }
    )

    registry["updated_at"] = timestamp
    registry["active_release_id"] = release.get("release_id")
    registry["releases"][0] = release

    write_json(MANIFEST_PATH, manifest)
    write_json(REGISTRY_PATH, registry)

    review = f"""# NothingButA Deploy Package Review

Generated: {timestamp}

## Status

DEPLOY PACKAGE READY — NOT PUBLISHED

## Release

- Release ID: {freeze.get("release_id")}
- Candidate ID: {freeze.get("candidate_id")}
- Site: {freeze.get("site_name")}
- State: deploy_package_ready

## Files

- Frozen staging file: {STAGING_PATH}
- Deploy package file: {DEPLOY_INDEX_PATH}
- Manifest: {MANIFEST_PATH}

## Hash Proof

- Frozen SHA256: {freeze.get("sha256")}
- Deploy SHA256: {deploy_hash}

## Recommended Host

GitHub Pages

## Recommended Public Path

/nothingbuta/debt-payoff-calculator/

## Safety

- Publishing: disabled
- External actions: disabled
- Domain purchase: disabled
- Ads: disabled
- Affiliate links: disabled
- Lead capture: disabled
- Commits/pushes: disabled
- Final Chris approval required: true

## Next Gate

Chris must explicitly approve the host, repo/path, and publish action before any Git commit, push, or deployment.
"""
    write_text(REVIEW_PATH, review)

    return manifest


def main() -> None:
    """Run deploy packaging and print proof."""
    try:
        manifest = build_deploy_package()

        print("NOTHINGBUTA DEPLOY PACKAGE: PASS")
        print("Deploy file:", DEPLOY_INDEX_PATH)
        print("Manifest:", MANIFEST_PATH)
        print("Review:", REVIEW_PATH)
        print("SHA256:", manifest["deploy_sha256"])
    except Exception as exc:
        print("NOTHINGBUTA DEPLOY PACKAGE: FAIL")
        print(str(exc))
        raise


if __name__ == "__main__":
    main()