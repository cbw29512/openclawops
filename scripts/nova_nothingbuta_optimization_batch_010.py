from __future__ import annotations

import json
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path


# Objective:
# Apply NothingButA Optimization Batch 010 to freelance-rate-calculator.
#
# State:
# - SEO score is already 1.
# - The only remaining opportunity is structured_data_candidate.
#
# This script DOES:
# - add WebApplication JSON-LD only
# - create a backup
# - write JSON/Markdown proof reports
#
# This script DOES NOT:
# - change calculator math logic
# - change visible page copy
# - commit
# - push
# - publish
# - change GitHub Pages settings
# - add analytics, ads, affiliate links, lead capture, or outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_optimization_batch_010")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
REPO_ROOT = ROOT / "nothingbuta" / "github" / "nothingbuta"
TARGET_SLUG = "freelance-rate-calculator"
TARGET_PATH = REPO_ROOT / "docs" / TARGET_SLUG / "index.html"

BACKUP_ROOT = ROOT / "nothingbuta" / "docs_backups"
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

BATCH_ID = "nothingbuta-optimization-batch-010"
SCHEMA_MARKER = "nothingbuta-optimization-batch-010-schema"
ROOT_DROPDOWN_OPTION = '<option value="../">All tools home</option>'

JSON_OUT = DATA_DIR / "nothingbuta_optimization_batch_010.json"
MD_OUT = REPORTS_DIR / "nothingbuta-optimization-batch-010.md"

STRUCTURED_DATA = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    "name": "NothingButA Freelance Rate Calculator",
    "url": "https://cbw29512.github.io/nothingbuta/freelance-rate-calculator/",
    "applicationCategory": "BusinessApplication",
    "operatingSystem": "Any",
    "description": (
        "Estimate a freelance hourly rate from income goals, billable hours, expenses, "
        "taxes, and time off so pricing is easier to plan."
    ),
    "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD",
    },
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.exception("Failed to read target page")
        raise RuntimeError(f"Failed to read target page: {path}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.write_text(text, encoding="utf-8")
    except Exception as exc:
        logger.exception("Failed to write target page")
        raise RuntimeError(f"Failed to write target page: {path}") from exc


def backup_target() -> Path:
    try:
        if not TARGET_PATH.exists():
            raise RuntimeError(f"Missing target page: {TARGET_PATH}")

        BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = BACKUP_ROOT / f"{TARGET_SLUG}-before-optimization-010-{stamp}.html"
        shutil.copy2(TARGET_PATH, backup_path)
        return backup_path
    except Exception as exc:
        logger.exception("Failed to back up target page")
        raise RuntimeError("Failed to back up target page") from exc


def inject_schema(html: str) -> tuple[str, bool]:
    try:
        if SCHEMA_MARKER in html:
            return html, False

        block = (
            f'<script type="application/ld+json" id="{SCHEMA_MARKER}">\n'
            f"{json.dumps(STRUCTURED_DATA, indent=2)}\n"
            "</script>"
        )

        if not re.search(r"</head>", html, flags=re.IGNORECASE):
            raise RuntimeError("Cannot find closing </head> tag")

        updated = re.sub(
            r"</head>",
            block + "\n</head>",
            html,
            count=1,
            flags=re.IGNORECASE,
        )

        return updated, True

    except Exception as exc:
        logger.exception("Failed to inject schema")
        raise RuntimeError("Failed to inject schema") from exc


def self_check(html: str) -> list[str]:
    try:
        problems: list[str] = []

        if ROOT_DROPDOWN_OPTION in html:
            problems.append("root_dropdown_option_present")

        if SCHEMA_MARKER not in html:
            problems.append("missing_batch_schema_marker")

        if 'type="application/ld+json"' not in html:
            problems.append("missing_json_ld_script")

        return problems

    except Exception as exc:
        logger.exception("Self-check failed")
        raise RuntimeError("Self-check failed") from exc


def write_reports(proof: dict) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        JSON_OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Optimization Batch 010",
            "",
            f"Generated: {proof['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: {proof['status']}",
            f"- Target slug: `{proof['target_slug']}`",
            f"- Changed: `{proof['changed']}`",
            f"- Backup: `{proof['backup_path']}`",
            "",
            "## Changes",
            "",
            "- added_webapplication_json_ld_only",
        ]

        if proof["problems"]:
            lines.extend(["", "## Problems", ""])
            for problem in proof["problems"]:
                lines.append(f"- `{problem}`")

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    except Exception as exc:
        logger.exception("Failed to write reports")
        raise RuntimeError("Failed to write reports") from exc


def main() -> int:
    try:
        backup_path = backup_target()
        original = read_text(TARGET_PATH)

        updated, schema_changed = inject_schema(original)
        problems = self_check(updated)

        if not problems and updated != original:
            write_text(TARGET_PATH, updated)

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "batch_id": BATCH_ID,
            "target_slug": TARGET_SLUG,
            "target_path": str(TARGET_PATH),
            "backup_path": str(backup_path),
            "status": "PASS" if not problems else "FAILED",
            "changed": schema_changed and not problems,
            "problems": problems,
        }

        write_reports(proof)

        print("NOTHINGBUTA OPTIMIZATION BATCH 010:", proof["status"])
        print("target:", TARGET_SLUG)
        print("changed:", proof["changed"])
        print("backup:", backup_path)
        print("json:", JSON_OUT)
        print("markdown:", MD_OUT)

        if problems:
            print("problems:", problems)

        return 0 if proof["status"] == "PASS" else 1

    except Exception as exc:
        logger.exception("Batch 010 failed")
        print("NOTHINGBUTA OPTIMIZATION BATCH 010: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
