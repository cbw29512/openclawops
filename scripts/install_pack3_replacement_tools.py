from __future__ import annotations

import ast
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
MODULE_DIR = SCRIPTS / "nothingbuta_factory"
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
CANDIDATES_DIR = ROOT / "nothingbuta" / "factory" / "candidates"

LEGACY_PATH = MODULE_DIR / "legacy_factory.py"
CATALOG_PATH = MODULE_DIR / "renderer_catalog_v2.py"
REGISTRY_PATH = DATA / "nothingbuta_candidate_registry.json"
REPORT_PATH = REPORTS / "nothingbuta-pack3-replacement-install.md"

ENTRYPOINT_PATH = SCRIPTS / "nova_nothingbuta_local_factory_loop.py"

PACK3_CONFIG_MARKER = "RENDERER_EXPANSION_PACK_3_CONFIGS"
PACK3_FORMULA_MARKER = "RENDERER_EXPANSION_PACK_3_FORMULAS"

OLD_TO_NEW = {
    "calories-per-serving-calculator": "conversion-rate-calculator",
    "age-calculator": "churn-rate-calculator",
}

PACK3_CONFIGS: dict[str, dict[str, Any]] = {
    "conversion-rate-calculator": {
        "name": "Conversion Rate Calculator",
        "description": "Calculate conversion rate from visitors and completed actions.",
        "category": "business",
        "formula": "conversionrate",
        "inputs": [
            ["visitors", "Visitors", "Total visitors, clicks, leads, or opportunities", "1000"],
            ["conversions", "Conversions", "Purchases, signups, leads, or completed actions", "50"],
        ],
        "faq": [
            ["What is conversion rate?", "Conversion rate is the percentage of visitors or opportunities that complete a desired action."],
            ["Is this a forecast?", "No. This is an estimate-only calculator based on the numbers you enter."],
        ],
    },
    "churn-rate-calculator": {
        "name": "Churn Rate Calculator",
        "description": "Calculate customer churn rate from starting customers and customers lost.",
        "category": "business",
        "formula": "churnrate",
        "inputs": [
            ["starting", "Customers at start", "Customers at the beginning of the period", "1000"],
            ["lost", "Customers lost", "Customers lost or cancelled during the period", "40"],
        ],
        "faq": [
            ["What is churn rate?", "Churn rate is the percentage of customers lost during a period compared with the starting customer count."],
            ["Is this business advice?", "No. This is an estimate-only calculator for quick planning and reporting."],
        ],
    },
}

PACK3_JS_ESCAPED = '''
        // === RENDERER_EXPANSION_PACK_3_FORMULAS START ===
        if (FORMULA === "conversionrate") {{
          const visitors = num("visitors");
          const conversions = num("conversions");
          if (visitors <= 0) {{
            html = '<div class="warn">Enter visitors above zero.</div>';
          }} else {{
            const rate = (conversions / visitors) * 100;
            html = block(`${{rate.toFixed(2)}}%`, "Conversion rate") + block(conversions.toLocaleString(), "Conversions") + block(visitors.toLocaleString(), "Visitors") + block((visitors - conversions).toLocaleString(), "Non-converting visitors");
          }}
        }}

        if (FORMULA === "churnrate") {{
          const starting = num("starting");
          const lost = num("lost");
          if (starting <= 0) {{
            html = '<div class="warn">Enter starting customers above zero.</div>';
          }} else {{
            const churn = (lost / starting) * 100;
            const retained = Math.max(starting - lost, 0);
            const retention = (retained / starting) * 100;
            html = block(`${{churn.toFixed(2)}}%`, "Churn rate") + block(`${{retention.toFixed(2)}}%`, "Retention rate") + block(lost.toLocaleString(), "Customers lost") + block(retained.toLocaleString(), "Customers retained");
          }}
        }}
        // === RENDERER_EXPANSION_PACK_3_FORMULAS END ===
'''

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def backup_file(path: Path, label: str) -> Path:
    try:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = path.with_name(f"{path.name}.bak-{label}-{stamp}")
        shutil.copy2(path, backup_path)
        return backup_path
    except Exception as exc:
        logging.exception("Backup failed: %s", path)
        raise SystemExit(1) from exc


def compile_file(path: Path) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout.strip():
        print(result.stdout)
    if result.stderr.strip():
        print(result.stderr)
    return result.returncode == 0


def load_registry() -> dict[str, Any]:
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logging.exception("Failed loading registry.")
        raise SystemExit(1) from exc


def save_registry(data: dict[str, Any]) -> None:
    try:
        REGISTRY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:
        logging.exception("Failed saving registry.")
        raise SystemExit(1) from exc


def preflight_parse(label: str, source: str) -> None:
    try:
        ast.parse(source)
    except SyntaxError as exc:
        logging.error("Preflight parse failed for %s: %s", label, exc)
        raise SystemExit(1) from exc


def patch_catalog() -> Path:
    source = CATALOG_PATH.read_text(encoding="utf-8")

    if PACK3_CONFIG_MARKER in source:
        logging.error("Pack 3 configs already installed.")
        raise SystemExit(1)

    sys.path.insert(0, str(SCRIPTS))
    from nothingbuta_factory.renderer_catalog_v2 import TOOL_CONFIGS

    existing = sorted(slug for slug in PACK3_CONFIGS if slug in TOOL_CONFIGS)
    if existing:
        logging.error("Pack 3 slug(s) already in catalog: %s", existing)
        raise SystemExit(1)

    append_block = [
        "",
        "",
        "# === RENDERER_EXPANSION_PACK_3_CONFIGS START ===",
        "TOOL_CONFIGS.update(",
        json.dumps(PACK3_CONFIGS, indent=4),
        ")",
        "# === RENDERER_EXPANSION_PACK_3_CONFIGS END ===",
        "",
    ]

    patched = source.rstrip() + "\n" + "\n".join(append_block)
    preflight_parse("renderer_catalog_v2.py", patched)

    backup = backup_file(CATALOG_PATH, "pack3-configs")
    CATALOG_PATH.write_text(patched, encoding="utf-8")
    return backup


def patch_legacy_formulas() -> Path:
    source = LEGACY_PATH.read_text(encoding="utf-8")

    if PACK3_FORMULA_MARKER in source:
        logging.error("Pack 3 formulas already installed.")
        raise SystemExit(1)

    anchor = '        document.getElementById("out").innerHTML = html || \'<div class="warn">This tool needs a stricter formula before it can pass.</div>\';'

    if anchor not in source:
        logging.error("Formula insertion anchor not found.")
        raise SystemExit(1)

    patched = source.replace(anchor, PACK3_JS_ESCAPED.rstrip() + "\n\n" + anchor, 1)
    preflight_parse("legacy_factory.py", patched)

    backup = backup_file(LEGACY_PATH, "pack3-formulas")
    LEGACY_PATH.write_text(patched, encoding="utf-8")
    return backup


def render_and_audit_pack3() -> list[dict[str, Any]]:
    sys.path.insert(0, str(SCRIPTS))

    from nothingbuta_factory.renderer_catalog_v2 import TOOL_CONFIGS
    from nothingbuta_factory.legacy_factory import audit_html, html_shell, strict_score

    results: list[dict[str, Any]] = []

    for slug, config in PACK3_CONFIGS.items():
        real_config = TOOL_CONFIGS.get(slug)
        if real_config is None:
            results.append({"slug": slug, "status": "missing_catalog_config", "score": 0, "problems": ["missing catalog config"]})
            continue

        html_value = html_shell(real_config)
        problems = audit_html(html_value, {"slug": slug, "name": real_config["name"]}, real_config)
        score = strict_score(problems)

        preview_dir = CANDIDATES_DIR / slug
        preview_path = preview_dir / "index.html"

        if score == 100 and not problems:
            preview_dir.mkdir(parents=True, exist_ok=True)
            preview_path.write_text(html_value, encoding="utf-8")
            status = "rendered"
        else:
            status = "blocked"

        results.append(
            {
                "slug": slug,
                "name": real_config["name"],
                "status": status,
                "score": score,
                "problems": problems,
                "preview_path": str(preview_path),
            }
        )

    return results


def update_registry(render_results: list[dict[str, Any]]) -> None:
    registry = load_registry()
    items = registry.get("generated_candidates", [])

    if not isinstance(items, list):
        logging.error("generated_candidates is not a list.")
        raise SystemExit(1)

    by_slug = {item.get("slug"): item for item in items}
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    for old_slug, new_slug in OLD_TO_NEW.items():
        old_item = by_slug.get(old_slug)
        if old_item is None:
            logging.error("Missing old blocked registry item: %s", old_slug)
            raise SystemExit(1)

        result = next((item for item in render_results if item["slug"] == new_slug), None)
        config = PACK3_CONFIGS[new_slug]

        if result is None or result["status"] != "rendered" or result["score"] != 100:
            logging.error("Pack 3 render did not pass for %s.", new_slug)
            raise SystemExit(1)

        old_item["tool_id"] = f"nba-pack3-{new_slug}"
        old_item["name"] = config["name"]
        old_item["slug"] = new_slug
        old_item["state"] = "local_preview_ready"
        old_item["local_preview_path"] = result["preview_path"]
        old_item["audit_status"] = "PASS"
        old_item["audit_problems"] = []
        old_item["strict_quality_score"] = 100
        old_item["replaced_slug"] = old_slug
        old_item["replacement_reason"] = "Evidence-backed Pack 3 replacement for weak/blocked slot."
        old_item["updated_at"] = now

        old_item["publish_allowed"] = False
        old_item["push_allowed"] = False
        old_item["commit_allowed"] = False
        old_item["external_action_allowed"] = False

    registry["updated_at"] = now
    save_registry(registry)


def run_safe_report_chain() -> list[dict[str, Any]]:
    commands = [
        ["python", str(SCRIPTS / "nova_nothingbuta_local_factory_loop.py")],
        ["python", str(SCRIPTS / "nova_nothingbuta_release_batch_picker.py")],
        ["python", str(SCRIPTS / "nova_nothingbuta_release_freeze_packet.py")],
        ["python", str(SCRIPTS / "nova_nothingbuta_local_preview_review_page.py")],
        ["python", str(SCRIPTS / "nova_nothingbuta_staging_copy_proposal.py")],
        ["python", str(SCRIPTS / "nova_nothingbuta_local_staging_copy.py")],
        ["python", str(SCRIPTS / "nova_nothingbuta_hourly_optimizer_report.py")],
    ]

    results = []

    for command in commands:
        result = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        results.append(
            {
                "command": " ".join(command),
                "exit_code": result.returncode,
                "passed": result.returncode == 0,
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
    registry = load_registry()
    items = registry.get("generated_candidates", [])
    states: dict[str, int] = {}
    audits: dict[str, int] = {}

    for item in items:
        state = str(item.get("state", "missing"))
        audit = str(item.get("audit_status", "missing"))
        states[state] = states.get(state, 0) + 1
        audits[audit] = audits.get(audit, 0) + 1

    blocked = [
        {
            "name": item.get("name"),
            "slug": item.get("slug"),
            "state": item.get("state"),
            "audit_status": item.get("audit_status"),
            "audit_problems": item.get("audit_problems"),
        }
        for item in items
        if item.get("state") != "local_preview_ready"
    ]

    return {"items": len(items), "states": states, "audits": audits, "blocked": blocked}


def write_report(
    catalog_backup: Path,
    legacy_backup: Path,
    registry_backup: Path,
    render_results: list[dict[str, Any]],
    chain_results: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    lines = [
        "# NothingButA Pack 3 Replacement Install",
        "",
        f"Generated: {now}",
        "",
        "## Backups",
        "",
        f"- Catalog backup: `{catalog_backup}`",
        f"- Legacy backup: `{legacy_backup}`",
        f"- Registry backup: `{registry_backup}`",
        "",
        "## Replacement Result",
        "",
    ]

    for result in render_results:
        lines.extend(
            [
                f"### {result['name']}",
                "",
                f"- Slug: `{result['slug']}`",
                f"- Status: `{result['status']}`",
                f"- Score: `{result['score']}`",
                f"- Problems: `{result['problems']}`",
                f"- Preview: `{result['preview_path']}`",
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
            "## Safe Report Chain",
            "",
        ]
    )

    for result in chain_results:
        lines.extend(
            [
                f"### `{result['command']}`",
                "",
                f"- Passed: `{result['passed']}`",
                f"- Exit code: `{result['exit_code']}`",
                "",
            ]
        )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    registry_backup = backup_file(REGISTRY_PATH, "pack3-registry")

    catalog_backup = patch_catalog()
    legacy_backup = patch_legacy_formulas()

    compile_ok = all(
        [
            compile_file(CATALOG_PATH),
            compile_file(LEGACY_PATH),
            compile_file(MODULE_DIR / "reports_v2.py"),
            compile_file(MODULE_DIR / "audit_rules_v2.py"),
            compile_file(MODULE_DIR / "renderer_specials_v2.py"),
            compile_file(ENTRYPOINT_PATH),
        ]
    )

    if not compile_ok:
        logging.error("Compile failed. Restore backups before continuing.")
        raise SystemExit(1)

    render_results = render_and_audit_pack3()
    update_registry(render_results)
    chain_results = run_safe_report_chain()
    summary = registry_summary()

    write_report(
        catalog_backup=catalog_backup,
        legacy_backup=legacy_backup,
        registry_backup=registry_backup,
        render_results=render_results,
        chain_results=chain_results,
        summary=summary,
    )

    chain_ok = all(item["passed"] for item in chain_results)
    reached_24 = summary["states"].get("local_preview_ready") == 24 and not summary["blocked"]

    print("NOTHINGBUTA PACK 3 REPLACEMENT INSTALL")
    print(f"compile_ok: {compile_ok}")
    print(f"chain_ok: {chain_ok}")
    print(f"reached_24_ready: {reached_24}")
    print(f"summary: {json.dumps(summary, indent=2)}")
    print(f"report: {REPORT_PATH}")

    if not chain_ok or not reached_24:
        logging.error("Pack 3 install did not reach expected 24-ready state.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()