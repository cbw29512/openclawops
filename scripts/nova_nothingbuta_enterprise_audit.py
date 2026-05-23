from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

POLICY_PATH = DATA_DIR / "nothingbuta_enterprise_production_policy.json"
REGISTRY_PATH = DATA_DIR / "nothingbuta_release_registry.json"
AUDIT_JSON_PATH = REPORTS_DIR / "nothingbuta-enterprise-audit.json"
AUDIT_MD_PATH = REPORTS_DIR / "nothingbuta-enterprise-audit.md"


def now_iso() -> str:
    """Return an audit-friendly timestamp."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    """Read JSON with BOM tolerance."""
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise RuntimeError(f"Failed to read JSON {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    """Write clean UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    """Write clean UTF-8 text."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def count_h1(html: str) -> int:
    """Count H1 tags without requiring a full HTML parser."""
    return len(re.findall(r"<h1\b", html, flags=re.IGNORECASE))


def make_check(name: str, passed: bool, severity: str, detail: str) -> dict[str, Any]:
    """Create one audit check record."""
    return {
        "name": name,
        "passed": bool(passed),
        "severity": severity,
        "detail": detail,
    }


def audit_release() -> dict[str, Any]:
    """Run enterprise production-readiness checks."""
    policy = read_json(POLICY_PATH)
    registry = read_json(REGISTRY_PATH)

    release = registry["releases"][0]
    staging_path = ROOT / release["staging_path"]

    if not staging_path.exists():
        raise FileNotFoundError(f"Missing staging page: {staging_path}")

    html = staging_path.read_text(encoding="utf-8-sig", errors="replace")
    html_lower = html.lower()
    lines = html.splitlines()

    checks: list[dict[str, Any]] = []

    # Required markers.
    for marker in policy.get("required_html_markers", []):
        checks.append(
            make_check(
                f"required_marker::{marker}",
                marker.lower() in html_lower,
                "fail",
                f"Required marker must exist: {marker}",
            )
        )

    # Blocked public terms.
    for term in policy.get("blocked_public_terms", []):
        checks.append(
            make_check(
                f"blocked_public_term::{term}",
                term.lower() not in html_lower,
                "fail",
                f"Public page must not contain internal/system term: {term}",
            )
        )

    # Blocked HTML markers.
    for marker in policy.get("blocked_html_markers", []):
        checks.append(
            make_check(
                f"blocked_html_marker::{marker}",
                marker.lower() not in html_lower,
                "fail",
                f"Public v1 must not contain blocked marker: {marker}",
            )
        )

    # Structural checks.
    checks.append(make_check("single_h1", count_h1(html) == 1, "fail", "Page should have exactly one H1."))
    checks.append(make_check("line_count_under_limit", len(lines) <= int(policy.get("max_html_lines", 150)), "warn", "HTML file should stay under the line limit or be split."))
    checks.append(make_check("has_button", "<button" in html_lower, "fail", "Calculator should have a clear action button."))
    checks.append(make_check("has_inputs", html_lower.count("<input") >= 3, "fail", "Calculator should have enough inputs for the tool."))
    checks.append(make_check("no_external_script", "<script src=" not in html_lower, "fail", "V1 should avoid external scripts."))
    checks.append(make_check("static_only", "fetch(" not in html_lower and "xmlhttprequest" not in html_lower, "fail", "V1 should be static-only."))
    checks.append(make_check("no_storage_or_cookie", "localstorage" not in html_lower and "sessionstorage" not in html_lower and "document.cookie" not in html_lower, "fail", "V1 should not store visitor data."))

    fail_count = sum(1 for check in checks if not check["passed"] and check["severity"] == "fail")
    warn_count = sum(1 for check in checks if not check["passed"] and check["severity"] == "warn")
    pass_count = sum(1 for check in checks if check["passed"])

    audit_status = "pass" if fail_count == 0 else "fail"

    release["enterprise_audit_status"] = audit_status
    release["enterprise_audit_at"] = now_iso()
    release["publish_allowed"] = False
    release["external_action_allowed"] = False

    registry["updated_at"] = now_iso()
    write_json(REGISTRY_PATH, registry)

    result = {
        "audit_id": "nothingbuta-enterprise-audit-nba-util-0001-v1",
        "created_at": now_iso(),
        "status": audit_status,
        "release_id": release["release_id"],
        "site_name": release["site_name"],
        "staging_path": str(staging_path),
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "line_count": len(lines),
        "publish_allowed": False,
        "external_action_allowed": False,
        "final_chris_approval_required": True,
        "checks": checks,
    }

    write_json(AUDIT_JSON_PATH, result)
    write_markdown_report(result)

    return result


def write_markdown_report(result: dict[str, Any]) -> None:
    """Write a human-readable enterprise audit report."""
    failed = [check for check in result["checks"] if not check["passed"]]
    failed_text = "\n".join(f"- {check['name']}: {check['detail']}" for check in failed) if failed else "- None"

    report = f"""# NothingButA Enterprise Audit

Generated: {result['created_at']}

## Status

{result['status'].upper()}

## Release

- ID: {result['release_id']}
- Site: {result['site_name']}
- Staging path: {result['staging_path']}

## Score

- Pass: {result['pass_count']}
- Warn: {result['warn_count']}
- Fail: {result['fail_count']}
- Line count: {result['line_count']}

## Failed / Warning Checks

{failed_text}

## Safety

- Publishing allowed: false
- External actions allowed: false
- Final Chris approval required: true
"""
    write_text(AUDIT_MD_PATH, report)


def main() -> None:
    """Run audit and print result."""
    try:
        result = audit_release()

        print("NOTHINGBUTA ENTERPRISE AUDIT:", result["status"].upper())
        print("Pass:", result["pass_count"])
        print("Warn:", result["warn_count"])
        print("Fail:", result["fail_count"])
        print("Report:", AUDIT_MD_PATH)
    except Exception as exc:
        print("NOTHINGBUTA ENTERPRISE AUDIT: ERROR")
        print(str(exc))
        raise


if __name__ == "__main__":
    main()