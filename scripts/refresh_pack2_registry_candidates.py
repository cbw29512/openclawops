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
SCRIPTS_DIR = ROOT / "scripts"
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
CANDIDATES_DIR = ROOT / "nothingbuta" / "factory" / "candidates"

REGISTRY_PATH = DATA_DIR / "nothingbuta_candidate_registry.json"
REPORT_PATH = REPORTS_DIR / "nothingbuta-pack2-registry-refresh.md"
ENTRYPOINT_PATH = SCRIPTS_DIR / "nova_nothingbuta_local_factory_loop.py"

APPROVED_SLUGS = [
    "roi-calculator",
    "recipe-scale-calculator",
    "paint-coverage-calculator",
    "flooring-calculator",
    "concrete-calculator",
]

PARKED_SLUGS = [
    "calories-per-serving-calculator",
    "age-calculator",
]

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


def load_registry() -> dict[str, Any]:
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logging.exception("Could not load registry.")
        raise SystemExit(1) from exc


def save_registry(data: dict[str, Any]) -> None:
    try:
        REGISTRY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:
        logging.exception("Could not save registry.")
        raise SystemExit(1) from exc


def run_compile_check() -> bool:
    paths = [
        SCRIPTS_DIR / "nova_nothingbuta_local_factory_loop.py",
        SCRIPTS_DIR / "nothingbuta_factory" / "legacy_factory.py",
        SCRIPTS_DIR / "nothingbuta_factory" / "reports_v2.py",
        SCRIPTS_DIR / "nothingbuta_factory" / "audit_rules_v2.py",
        SCRIPTS_DIR / "nothingbuta_factory" / "renderer_catalog_v2.py",
        SCRIPTS_DIR / "nothingbuta_factory" / "renderer_specials_v2.py",
    ]

    for path in paths:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            return False

    return True


def run_factory_check() -> bool:
    result = subprocess.run(
        [sys.executable, str(ENTRYPOINT_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )

    print(result.stdout)
    if result.stderr.strip():
        print(result.stderr)

    return result.returncode == 0 and "PASS" in result.stdout


def main() -> None:
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from nothingbuta_factory.renderer_catalog_v2 import TOOL_CONFIGS
        from nothingbuta_factory.legacy_factory import audit_html, html_shell, strict_score

        registry = load_registry()
        candidates = registry.get("generated_candidates", [])

        if not isinstance(candidates, list):
            raise ValueError("generated_candidates is not a list")

        registry_backup = backup_file(REGISTRY_PATH, "pack2-registry-refresh")

        now = datetime.now().astimezone().isoformat(timespec="seconds")
        results: list[dict[str, Any]] = []

        by_slug = {item.get("slug"): item for item in candidates}

        for slug in APPROVED_SLUGS:
            item = by_slug.get(slug)
            config = TOOL_CONFIGS.get(slug)

            if item is None:
                results.append({"slug": slug, "status": "missing_registry_entry"})
                continue

            if config is None:
                results.append({"slug": slug, "status": "missing_catalog_config"})
                continue

            html_value = html_shell(config)
            problems = audit_html(html_value, item, config)
            score = strict_score(problems)

            preview_dir = CANDIDATES_DIR / slug
            preview_path = preview_dir / "index.html"

            if score == 100 and not problems:
                preview_dir.mkdir(parents=True, exist_ok=True)
                preview_path.write_text(html_value, encoding="utf-8")

                item["state"] = "local_preview_ready"
                item["local_preview_path"] = str(preview_path)
                item["audit_status"] = "PASS"
                item["audit_problems"] = []
                item["strict_quality_score"] = 100
                item["updated_at"] = now

                item["publish_allowed"] = False
                item["push_allowed"] = False
                item["commit_allowed"] = False
                item["external_action_allowed"] = False

                results.append(
                    {
                        "slug": slug,
                        "status": "refreshed",
                        "score": score,
                        "preview_path": str(preview_path),
                    }
                )
            else:
                item["state"] = "template_required"
                item["audit_status"] = "BLOCKED"
                item["audit_problems"] = problems
                item["strict_quality_score"] = score
                item["updated_at"] = now

                results.append(
                    {
                        "slug": slug,
                        "status": "still_blocked",
                        "score": score,
                        "problems": problems,
                    }
                )

        for slug in PARKED_SLUGS:
            item = by_slug.get(slug)
            if item:
                item["state"] = "template_required"
                item["audit_status"] = "BLOCKED"
                item["audit_problems"] = ["not approved by evidence gate yet"]
                item["updated_at"] = now
                item["publish_allowed"] = False
                item["push_allowed"] = False
                item["commit_allowed"] = False
                item["external_action_allowed"] = False

        registry["updated_at"] = now
        save_registry(registry)

        compile_ok = run_compile_check()
        factory_ok = run_factory_check() if compile_ok else False

        refreshed = [r for r in results if r.get("status") == "refreshed"]
        blocked = [r for r in results if r.get("status") != "refreshed"]

        report_lines = [
            "# NothingButA Pack 2 Registry Refresh",
            "",
            f"Generated: {now}",
            "",
            f"- Registry backup: `{registry_backup}`",
            f"- Compile OK: {compile_ok}",
            f"- Factory OK: {factory_ok}",
            f"- Refreshed: {len(refreshed)}",
            f"- Not refreshed: {len(blocked)}",
            "",
            "## Results",
            "",
        ]

        for result in results:
            report_lines.append(f"- `{result['slug']}`: {result['status']}")

        report_lines.extend(
            [
                "",
                "## Safety",
                "",
                "- Commit allowed: false",
                "- Push allowed: false",
                "- Publish allowed: false",
                "- GitHub Pages changes: false",
                "- Analytics: false",
                "- Ads: false",
                "- Affiliate links: false",
                "- Lead capture: false",
            ]
        )

        REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")

        print("=== Pack 2 Registry Refresh Result ===")
        print(f"registry_backup: {registry_backup}")
        print(f"report_path: {REPORT_PATH}")
        print(f"compile_ok: {compile_ok}")
        print(f"factory_ok: {factory_ok}")
        print(json.dumps(results, indent=2))

        if not compile_ok or not factory_ok:
            logging.error("Validation failed. Registry backup is available.")
            raise SystemExit(1)

    except Exception as exc:
        logging.exception("Pack 2 registry refresh failed.")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()