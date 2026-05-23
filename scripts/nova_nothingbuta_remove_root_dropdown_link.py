from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path


# Objective:
# Remove public dropdown links that send users back to the root NothingButA page.
#
# This keeps public users moving between individual utility pages only.
#
# This script DOES:
# - remove <option value="../">All tools home</option> from public tool pages
# - remove the same option from the nav polish generator script
# - verify dropdowns still exist on tool pages
# - write a local proof report
#
# This script DOES NOT:
# - change GitHub Pages settings
# - add analytics
# - add ads
# - add affiliate links
# - add lead capture
# - do outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_remove_root_dropdown_link")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
REPO_ROOT = ROOT / "nothingbuta" / "github" / "nothingbuta"
DOCS_DIR = REPO_ROOT / "docs"
SCRIPT_PATH = ROOT / "scripts" / "nova_nothingbuta_public_nav_polish.py"

DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

JSON_OUT = DATA_DIR / "nothingbuta_remove_root_dropdown_link_proof.json"
MD_OUT = REPORTS_DIR / "nothingbuta-remove-root-dropdown-link-proof.md"

BAD_OPTION_HTML = '<option value="../">All tools home</option>'
BAD_OPTION_PY = '            \'<option value="../">All tools home</option>\','


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


def patch_file(path: Path, replacements: list[str]) -> dict:
    try:
        original = read_text(path)
        updated = original
        removed = []

        for value in replacements:
            if value in updated:
                updated = updated.replace(value, "")
                removed.append(value.strip())

        changed = updated != original

        if changed:
            write_text(path, updated)

        return {
            "path": str(path),
            "changed": changed,
            "removed": removed,
        }

    except Exception as exc:
        logger.exception("Failed to patch file: %s", path)
        raise RuntimeError(f"Failed to patch file: {path}") from exc


def patch_generator_script() -> dict:
    try:
        if not SCRIPT_PATH.exists():
            raise RuntimeError(f"Generator script missing: {SCRIPT_PATH}")

        return patch_file(SCRIPT_PATH, [BAD_OPTION_PY, BAD_OPTION_HTML])

    except Exception as exc:
        logger.exception("Failed to patch generator script")
        raise RuntimeError("Failed to patch generator script") from exc


def patch_public_tool_pages() -> list[dict]:
    try:
        if not DOCS_DIR.exists():
            raise RuntimeError(f"Docs directory missing: {DOCS_DIR}")

        results = []

        for index_path in sorted(DOCS_DIR.glob("*/index.html")):
            results.append(patch_file(index_path, [BAD_OPTION_HTML]))

        return results

    except Exception as exc:
        logger.exception("Failed to patch public tool pages")
        raise RuntimeError("Failed to patch public tool pages") from exc


def verify_public_tool_pages() -> dict:
    try:
        problems = []
        checked = 0

        for index_path in sorted(DOCS_DIR.glob("*/index.html")):
            checked += 1
            text = read_text(index_path)

            has_bad_root_option = BAD_OPTION_HTML in text
            has_dropdown = 'id="nothingbuta-tool-jump"' in text
            option_count = text.lower().count("<option ")

            if has_bad_root_option:
                problems.append(
                    {
                        "path": str(index_path),
                        "problem": "root_dropdown_option_still_present",
                    }
                )

            if not has_dropdown:
                problems.append(
                    {
                        "path": str(index_path),
                        "problem": "dropdown_missing",
                    }
                )

            if option_count < 10:
                problems.append(
                    {
                        "path": str(index_path),
                        "problem": "dropdown_option_count_too_low",
                        "option_count": option_count,
                    }
                )

        return {
            "checked": checked,
            "passed": len(problems) == 0,
            "problems": problems,
        }

    except Exception as exc:
        logger.exception("Verification failed")
        raise RuntimeError("Verification failed") from exc


def write_reports(proof: dict) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        JSON_OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Remove Root Dropdown Link Proof",
            "",
            f"Generated: {proof['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: {proof['status']}",
            f"- Tool pages checked: {proof['verification']['checked']}",
            f"- Verification passed: `{proof['verification']['passed']}`",
            f"- Changed files: {proof['changed_files']}",
            "",
            "## Changed Files",
            "",
        ]

        for item in proof["results"]:
            if item["changed"]:
                lines.append(f"- `{item['path']}`")

        if proof["verification"]["problems"]:
            lines.extend(["", "## Problems", ""])
            for problem in proof["verification"]["problems"]:
                lines.append(f"- `{problem}`")

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    except Exception as exc:
        logger.exception("Failed to write reports")
        raise RuntimeError("Failed to write reports") from exc


def main() -> int:
    try:
        results = []

        results.append(patch_generator_script())
        results.extend(patch_public_tool_pages())

        verification = verify_public_tool_pages()

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "PASS" if verification["passed"] else "FAILED",
            "changed_files": sum(1 for item in results if item["changed"]),
            "results": results,
            "verification": verification,
        }

        write_reports(proof)

        print("NOTHINGBUTA REMOVE ROOT DROPDOWN LINK:", proof["status"])
        print("changed_files:", proof["changed_files"])
        print("tool_pages_checked:", verification["checked"])
        print("verification_passed:", verification["passed"])
        print("json:", JSON_OUT)
        print("markdown:", MD_OUT)

        return 0 if proof["status"] == "PASS" else 1

    except Exception as exc:
        logger.exception("Remove root dropdown link failed")
        print("NOTHINGBUTA REMOVE ROOT DROPDOWN LINK: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
