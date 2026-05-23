from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path


# Objective:
# Patch the two issues found by the NothingButA live quality monitor.
#
# This script DOES:
# - add accessible names to unlabeled debt payoff inputs
# - improve the unit price calculator meta description
# - write proof files
#
# This script DOES NOT:
# - commit
# - push
# - publish
# - change GitHub Pages settings
# - add analytics, ads, affiliate links, lead capture, or outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_quality_patch_001")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
REPO_ROOT = ROOT / "nothingbuta" / "github" / "nothingbuta"
DOCS_DIR = REPO_ROOT / "docs"

DEBT_PATH = DOCS_DIR / "debt-payoff-calculator" / "index.html"
UNIT_PRICE_PATH = DOCS_DIR / "unit-price-calculator" / "index.html"

DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

JSON_OUT = DATA_DIR / "nothingbuta_quality_patch_001_proof.json"
MD_OUT = REPORTS_DIR / "nothingbuta-quality-patch-001-proof.md"


DEBT_INPUT_LABELS = [
    "Current debt balance",
    "Annual interest rate",
    "Current monthly payment",
    "Extra monthly payment",
]


UNIT_PRICE_DESCRIPTION = (
    "Compare package sizes and prices with a simple unit price calculator. "
    "Enter quantity, size, and cost to see which option gives the better value."
)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.exception("Failed to read file: %s", path)
        raise RuntimeError(f"Failed to read file: {path}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.write_text(text, encoding="utf-8")
    except Exception as exc:
        logger.exception("Failed to write file: %s", path)
        raise RuntimeError(f"Failed to write file: {path}") from exc


def input_has_accessible_name(input_tag: str) -> bool:
    """Check whether an input tag already has an inline accessible name."""
    try:
        return bool(
            re.search(r'\saria-label\s*=', input_tag, flags=re.IGNORECASE)
            or re.search(r'\saria-labelledby\s*=', input_tag, flags=re.IGNORECASE)
            or re.search(r'\stitle\s*=', input_tag, flags=re.IGNORECASE)
        )
    except Exception as exc:
        logger.exception("Failed to inspect input tag")
        raise RuntimeError("Failed to inspect input tag") from exc


def add_aria_labels_to_debt_inputs(html: str) -> tuple[str, int]:
    """Add aria-label attributes to unlabeled debt payoff inputs.

    Under the hood:
    - This is a controlled static HTML patch.
    - It only modifies <input ...> tags that do not already have aria-label,
      aria-labelledby, or title.
    - Labels are applied in visible form order.
    """
    try:
        labels = iter(DEBT_INPUT_LABELS)
        changed_count = 0

        def replace_input(match: re.Match) -> str:
            nonlocal changed_count

            input_tag = match.group(0)

            if input_has_accessible_name(input_tag):
                return input_tag

            try:
                label = next(labels)
            except StopIteration:
                label = f"Debt payoff input {changed_count + 1}"

            changed_count += 1

            if input_tag.endswith("/>"):
                return input_tag[:-2].rstrip() + f' aria-label="{label}" />'

            return input_tag[:-1].rstrip() + f' aria-label="{label}">'

        updated = re.sub(
            r"<input\b[^>]*>",
            replace_input,
            html,
            flags=re.IGNORECASE,
        )

        return updated, changed_count

    except Exception as exc:
        logger.exception("Failed to add aria labels to debt inputs")
        raise RuntimeError("Failed to add aria labels to debt inputs") from exc


def patch_debt_payoff() -> dict:
    try:
        original = read_text(DEBT_PATH)
        updated, changed_count = add_aria_labels_to_debt_inputs(original)

        if updated != original:
            write_text(DEBT_PATH, updated)

        return {
            "path": str(DEBT_PATH),
            "changed": updated != original,
            "aria_labels_added": changed_count,
        }

    except Exception as exc:
        logger.exception("Debt payoff patch failed")
        raise RuntimeError("Debt payoff patch failed") from exc


def patch_unit_price_meta_description() -> dict:
    try:
        original = read_text(UNIT_PRICE_PATH)

        meta_pattern = re.compile(
            r'<meta\s+name=["\']description["\']\s+content=["\'][^"\']*["\']\s*/?>',
            flags=re.IGNORECASE,
        )

        replacement = (
            f'<meta name="description" content="{UNIT_PRICE_DESCRIPTION}">'
        )

        if meta_pattern.search(original):
            updated = meta_pattern.sub(replacement, original, count=1)
        else:
            updated = original.replace("</head>", f"  {replacement}\n</head>", 1)

        if updated != original:
            write_text(UNIT_PRICE_PATH, updated)

        return {
            "path": str(UNIT_PRICE_PATH),
            "changed": updated != original,
            "description_length": len(UNIT_PRICE_DESCRIPTION),
        }

    except Exception as exc:
        logger.exception("Unit price meta patch failed")
        raise RuntimeError("Unit price meta patch failed") from exc


def write_reports(proof: dict) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        JSON_OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Quality Patch 001 Proof",
            "",
            f"Generated: {proof['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: {proof['status']}",
            f"- Changed files: {proof['changed_files']}",
            "",
            "## Results",
            "",
        ]

        for result in proof["results"]:
            lines.append(f"- `{result['path']}` changed=`{result['changed']}`")

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    except Exception as exc:
        logger.exception("Failed to write reports")
        raise RuntimeError("Failed to write reports") from exc


def main() -> int:
    try:
        if not DEBT_PATH.exists():
            raise RuntimeError(f"Missing file: {DEBT_PATH}")

        if not UNIT_PRICE_PATH.exists():
            raise RuntimeError(f"Missing file: {UNIT_PRICE_PATH}")

        results = [
            patch_debt_payoff(),
            patch_unit_price_meta_description(),
        ]

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "PASS",
            "changed_files": sum(1 for item in results if item["changed"]),
            "results": results,
        }

        write_reports(proof)

        print("NOTHINGBUTA QUALITY PATCH 001:", proof["status"])
        print("changed_files:", proof["changed_files"])
        print("json:", JSON_OUT)
        print("markdown:", MD_OUT)

        for result in results:
            print(result)

        return 0

    except Exception as exc:
        logger.exception("Quality patch failed")
        print("NOTHINGBUTA QUALITY PATCH 001: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())