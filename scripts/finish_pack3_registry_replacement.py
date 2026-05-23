from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
CANDIDATES_DIR = ROOT / "nothingbuta" / "factory" / "candidates"

REGISTRY_PATH = DATA / "nothingbuta_candidate_registry.json"
REPORT_PATH = REPORTS / "nothingbuta-pack3-registry-finish.md"

OLD_TO_NEW = {
    "calories-per-serving-calculator": "conversion-rate-calculator",
    "age-calculator": "churn-rate-calculator",
}

SAFE_CHAIN = [
    "nova_nothingbuta_local_factory_loop.py",
    "nova_nothingbuta_release_batch_picker.py",
    "nova_nothingbuta_release_freeze_packet.py",
    "nova_nothingbuta_local_preview_review_page.py",
    "nova_nothingbuta_staging_copy_proposal.py",
    "nova_nothingbuta_local_staging_copy.py",
    "nova_nothingbuta_hourly_optimizer_report.py",
]

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def backup_file(path: Path, label: str) -> Path:
    """Back up the registry before replacing the two weak slots."""
    try:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = path.with_name(f"{path.name}.bak-{label}-{stamp}")
        shutil.copy2(path, backup_path)
        return backup_path
    except Exception as exc:
        logging.exception("Backup failed: %s", path)
        raise SystemExit(1) from exc


def load_registry() -> dict[str, Any]:
    """Load the candidate registry."""
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logging.exception("Failed to load registry.")
        raise SystemExit(1) from exc


def save_registry(registry: dict[str, Any]) -> None:
    """Save the updated candidate registry."""
    try:
        REGISTRY_PATH.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    except Exception as exc:
        logging.exception("Failed to save registry.")
        raise SystemExit(1) from exc


def render_and_audit_new_tools() -> list[dict[str, Any]]:
    """Render the two Pack 3 tools and verify strict audit score 100."""
    try:
        sys.path.insert(0, str(SCRIPTS))

        from nothingbuta_factory.renderer_catalog_v2 import TOOL_CONFIGS
        from nothingbuta_factory.legacy_factory import audit_html, html_shell, strict_score

        results: list[dict[str, Any]] = []

        for new_slug in OLD_TO_NEW.values():
            config = TOOL_CONFIGS.get(new_slug)

            if config is None:
                results.append(
                    {
                        "slug": new_slug,
                        "status": "missing_catalog_config",
                        "score": 0,
                        "problems": ["missing catalog config"],
                    }
                )
                continue

            html_value = html_shell(config)
            problems = audit_html(html_value, {"slug": new_slug, "name": config.get("name")}, config)
            score = strict_score(problems)

            preview_dir = CANDIDATES_DIR / new_slug
            preview_path = preview_dir / "index.html"

            if score == 100 and not problems:
                preview_dir.mkdir(parents=True, exist_ok=True)
                preview_path.write_text(html_value, encoding="utf-8")
                status = "rendered"
            else:
                status = "blocked"

            results.append(
                {
                    "slug": new_slug,
                    "name": config.get("name"),
                    "status": status,
                    "score": score,
                    "problems": problems,
                    "preview_path": str(preview_path),
                }
            )

        return results
    except Exception as exc:
        logging.exception("Render/audit failed.")
        raise SystemExit(1) from exc


def update_registry(render_results: list[dict[str, Any]]) -> None:
    """Replace the two blocked slots with the two Pack 3 tools."""
    registry = load_registry()
    items = registry.get("generated_candidates", [])

    if not isinstance(items, list):
        logging.error("generated_candidates is not a list.")
        raise SystemExit(1)

    by_slug = {item.get("slug"): item for item in items}
    by_result = {item["slug"]: item for item in render_results}
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    sys.path.insert(0, str(SCRIPTS))
    from nothingbuta_factory.renderer_catalog_v2 import TOOL_CONFIGS

    for old_slug, new_slug in OLD_TO_NEW.items():
        item = by_slug.get(old_slug)

        if item is None:
            logging.error("Could not find old blocked registry item: %s", old_slug)
            raise SystemExit(1)

        result = by_result.get(new_slug)
        config = TOOL_CONFIGS.get(new_slug)

        if result is None or config is None:
            logging.error("Missing result/config for %s", new_slug)
            raise SystemExit(1)

        if result["status"] != "rendered" or result["score"] != 100 or result["problems"]:
            logging.error("New tool did not pass strict audit: %s", new_slug)
            raise SystemExit(1)

        item["tool_id"] = f"nba-pack3-{new_slug}"
        item["name"] = config["name"]
        item["slug"] = new_slug
        item["state"] = "local_preview_ready"
        item["local_preview_path"] = result["preview_path"]
        item["audit_status"] = "PASS"
        item["audit_problems"] = []
        item["strict_quality_score"] = 100
        item["replaced_slug"] = old_slug
        item["replacement_reason"] = "Evidence-backed Pack 3 replacement for weak/blocked slot."
        item["updated_at"] = now

        item["publish_allowed"] = False
        item["push_allowed"] = False
        item["commit_allowed"] = False
        item["external_action_allowed"] = False

    registry["updated_at"] = now
    save_registry(registry)


def run_safe_chain() -> list[dict[str, Any]]:
    """Regenerate all local-only review/report artifacts after registry replacement."""
    results: list[dict[str, Any]] = []

    for script_name in SAFE_CHAIN:
        command = ["python", str(SCRIPTS / script_name)]
        result = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

        results.append(
            {
                "script": script_name,
                "passed": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        )

        print(result.stdout)

        if result.stderr.strip():
            print(result.stderr)

        if result.returncode != 0:
            break

    return results


def registry_summary() -> dict[str, Any]:
    """Return a compact summary of the current registry state."""
    registry = load_registry()
    items = registry.get("generated_candidates", [])

    states: dict[str, int] = {}
    audits: dict[str, int] = {}
    blocked: list[dict[str, Any]] = []

    for item in items:
        state = str(item.get("state", "missing"))
        audit = str(item.get("audit_status", "missing"))

        states[state] = states.get(state, 0) + 1
        audits[audit] = audits.get(audit, 0) + 1

        if state != "local_preview_ready":
            blocked.append(
                {
                    "name": item.get("name"),
                    "slug": item.get("slug"),
                    "state": item.get("state"),
                    "audit_status": item.get("audit_status"),
                    "audit_problems": item.get("audit_problems"),
                }
            )

    return {
        "items": len(items),
        "states": states,
        "audits": audits,
        "blocked": blocked,
    }


def write_report(
    registry_backup: Path,
    render_results: list[dict[str, Any]],
    chain_results: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    """Write a human-readable finish report."""
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    lines = [
        "# NothingButA Pack 3 Registry Finish",
        "",
        f"Generated: {now}",
        "",
        "## Registry Backup",
        "",
        f"- `{registry_backup}`",
        "",
        "## Render/Audit Results",
        "",
    ]

    for result in render_results:
        lines.extend(
            [
                f"### {result.get('name')}",
                "",
                f"- Slug: `{result.get('slug')}`",
                f"- Status: `{result.get('status')}`",
                f"- Score: `{result.get('score')}`",
                f"- Problems: `{result.get('problems')}`",
                f"- Preview: `{result.get('preview_path')}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Registry Summary",
            "",
            f"- Items: {summary['items']}",
            f"- States: `{summary['states']}`",
            f"- Audits: `{summary['audits']}`",
            f"- Blocked: `{summary['blocked']}`",
            "",
            "## Safe Report Chain",
            "",
        ]
    )

    for result in chain_results:
        lines.extend(
            [
                f"### {result['script']}",
                "",
                f"- Passed: `{result['passed']}`",
                f"- Exit code: `{result['exit_code']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Safety",
            "",
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
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    registry_backup = backup_file(REGISTRY_PATH, "pack3-registry-finish")

    render_results = render_and_audit_new_tools()
    update_registry(render_results)

    chain_results = run_safe_chain()
    summary = registry_summary()

    write_report(
        registry_backup=registry_backup,
        render_results=render_results,
        chain_results=chain_results,
        summary=summary,
    )

    chain_ok = all(item["passed"] for item in chain_results)
    reached_24 = summary["states"].get("local_preview_ready") == 24 and not summary["blocked"]

    print("NOTHINGBUTA PACK 3 REGISTRY FINISH")
    print(f"chain_ok: {chain_ok}")
    print(f"reached_24_ready: {reached_24}")
    print(json.dumps(summary, indent=2))
    print(f"report: {REPORT_PATH}")

    if not chain_ok or not reached_24:
        logging.error("Pack 3 finish did not reach 24-ready state.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()