from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "showcase" / "portfolio_manifest.json"
REPORT_PATH = ROOT / "showcase-validation-report.json"


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8-sig")


def read_json(relative_path: str) -> dict[str, Any]:
    return json.loads(read_text(relative_path))


def require_contains(errors: list[str], path: str, phrases: list[str]) -> None:
    text = read_text(path).lower()
    for phrase in phrases:
        if phrase.lower() not in text:
            errors.append(f"{path} is missing required policy language: {phrase}")


def validate() -> dict[str, Any]:
    manifest = read_json("showcase/portfolio_manifest.json")
    errors: list[str] = []
    checked_files: list[str] = []

    if manifest.get("runtime_scope") != "local_only":
        errors.append("Showcase runtime_scope must remain local_only")

    required_paths = [
        *manifest.get("required_policy_files", []),
        *manifest.get("required_product_files", []),
    ]
    for relative_path in required_paths:
        path = ROOT / relative_path
        if not path.is_file():
            errors.append(f"Required showcase file is missing: {relative_path}")
        else:
            checked_files.append(relative_path)

    system_manifest = read_json("data/system_manifest.json")
    for flag, expected in manifest.get("required_flags", {}).items():
        actual = system_manifest.get(flag)
        if actual is not expected:
            errors.append(f"data/system_manifest.json {flag} must be {expected!r}, found {actual!r}")

    quality_policy = read_json("data/nothingbuta_quality_policy.json")
    for field, minimum in manifest.get("quality_gate_minimums", {}).items():
        actual = quality_policy.get(field)
        if not isinstance(actual, int) or actual < minimum:
            errors.append(f"Quality gate {field} must be at least {minimum}, found {actual!r}")

    blocked_before_approval = set(quality_policy.get("blocked_before_approval", []))
    required_quality_blocks = {
        "publishing",
        "domain_purchase",
        "ads",
        "affiliate_links",
        "lead_capture",
        "git_commit",
        "git_push",
    }
    missing_quality_blocks = sorted(required_quality_blocks - blocked_before_approval)
    if missing_quality_blocks:
        errors.append(f"Quality policy is missing approval blocks: {', '.join(missing_quality_blocks)}")

    public_policy = read_json("data/nothingbuta_public_page_policy.json")
    if not public_policy.get("banned_public_terms"):
        errors.append("Public-page policy must define banned internal terms")
    if not public_policy.get("required_public_markers"):
        errors.append("Public-page policy must define required visitor-facing markers")

    require_contains(
        errors,
        "APPROVAL_POLICY.md",
        [
            "spending money",
            "publishing content",
            "performing outreach",
            "using credentials",
            "committing code",
            "pushing to github",
            "destructive commands",
            "prepare first",
        ],
    )
    require_contains(
        errors,
        "money_scout/AUTONOMY_AND_ESCALATION_POLICY.md",
        [
            "chris required",
            "publishing",
            "selling",
            "outreach",
            "spending money",
            "using credentials",
            "stop and escalate",
        ],
    )
    require_contains(
        errors,
        "money_scout/DASHBOARD_APPROVAL_MODEL.md",
        [
            "data/opportunity_index.json",
            "v1 must not write",
            "live websites",
            "github",
            "payment systems",
            "outreach queues",
        ],
    )

    dashboard_state = read_text("dashboard/app/state.py")
    required_state_markers = [
        '"external_actions_enabled": False',
        '"spending_enabled": False',
        '"outreach_enabled": False',
        '"publishing_enabled": False',
        'if vote not in {"approve", "disapprove"}',
        'if not item_id.startswith("idx-")',
    ]
    for marker in required_state_markers:
        if marker not in dashboard_state:
            errors.append(f"dashboard/app/state.py is missing safety marker: {marker}")

    dashboard_readme = read_text("dashboard/README.md").lower()
    if "127.0.0.1" not in dashboard_readme:
        errors.append("Dashboard runbook must bind to 127.0.0.1")
    if "boost/bury local opportunity priority only" not in dashboard_readme:
        errors.append("Dashboard runbook must preserve local-priority-only voting")

    report = {
        "project": manifest.get("project"),
        "schema_version": manifest.get("schema_version"),
        "status": "pass" if not errors else "fail",
        "runtime_executed": False,
        "checked_file_count": len(checked_files),
        "required_flags": manifest.get("required_flags", {}),
        "allowed_dashboard_mutations": manifest.get("allowed_dashboard_mutations", []),
        "blocked_external_action_count": len(manifest.get("blocked_external_actions", [])),
        "errors": errors,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    try:
        report = validate()
    except Exception as error:
        print(f"Showcase validation could not complete: {error}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
