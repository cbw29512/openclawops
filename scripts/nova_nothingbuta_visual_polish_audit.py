from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path


# Objective:
# Build a local-only visual polish audit for the NothingButA public docs pages.
#
# This script DOES:
# - inspect current live repo docs HTML
# - identify common UI structure
# - report visual polish opportunities
# - write JSON and Markdown reports
#
# This script DOES NOT:
# - edit files
# - commit
# - push
# - publish
# - change GitHub Pages
# - add analytics, ads, affiliate links, lead capture, or outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_visual_polish_audit")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
REPO_ROOT = ROOT / "nothingbuta" / "github" / "nothingbuta"
DOCS_DIR = REPO_ROOT / "docs"
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

JSON_OUT = DATA_DIR / "nothingbuta_visual_polish_audit.json"
MD_OUT = REPORTS_DIR / "nothingbuta-visual-polish-audit.md"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.exception("Failed to read file: %s", path)
        raise RuntimeError(f"Failed to read file: {path}") from exc


def inspect_page(path: Path) -> dict:
    try:
        html = read_text(path)
        relative = str(path.relative_to(DOCS_DIR))

        title_match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.IGNORECASE | re.DOTALL)

        style_count = len(re.findall(r"<style\b", html, flags=re.IGNORECASE))
        input_count = len(re.findall(r"<input\b", html, flags=re.IGNORECASE))
        button_count = len(re.findall(r"<button\b", html, flags=re.IGNORECASE))
        card_mentions = len(re.findall(r"class=[\"'][^\"']*card", html, flags=re.IGNORECASE))
        result_mentions = len(re.findall(r"result|answer|output", html, flags=re.IGNORECASE))
        has_dropdown = 'id="nothingbuta-tool-jump"' in html
        has_root_option = '<option value="../">All tools home</option>' in html

        opportunities = []

        if input_count > 0 and button_count == 0:
            opportunities.append("calculator_has_inputs_but_no_button")

        if card_mentions < 2:
            opportunities.append("could_use_stronger_card_layout")

        if result_mentions < 2:
            opportunities.append("could_make_result_area_more_prominent")

        if style_count == 0:
            opportunities.append("missing_inline_style_block")

        if has_root_option:
            opportunities.append("root_dropdown_option_regression")

        if path.parent != DOCS_DIR and not has_dropdown:
            opportunities.append("missing_tool_dropdown")

        return {
            "path": str(path),
            "relative": relative,
            "title": title_match.group(1).strip() if title_match else "",
            "h1": re.sub(r"<[^>]+>", "", h1_match.group(1)).strip() if h1_match else "",
            "style_count": style_count,
            "input_count": input_count,
            "button_count": button_count,
            "card_mentions": card_mentions,
            "result_mentions": result_mentions,
            "has_dropdown": has_dropdown,
            "has_root_option": has_root_option,
            "opportunities": opportunities,
        }

    except Exception as exc:
        logger.exception("Failed to inspect page: %s", path)
        raise RuntimeError(f"Failed to inspect page: {path}") from exc


def main() -> int:
    try:
        if not DOCS_DIR.exists():
            raise RuntimeError(f"Docs directory missing: {DOCS_DIR}")

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        pages = sorted(DOCS_DIR.rglob("index.html"))
        results = [inspect_page(path) for path in pages]

        opportunity_counts = {}
        for result in results:
            for item in result["opportunities"]:
                opportunity_counts[item] = opportunity_counts.get(item, 0) + 1

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "PASS",
            "pages_checked": len(results),
            "opportunity_counts": opportunity_counts,
            "recommended_pass": {
                "name": "Visual Polish Pass 001",
                "scope": [
                    "Improve shared calculator shell styling",
                    "Make result panels more prominent",
                    "Add stronger CTA/microcopy around each tool",
                    "Improve mobile spacing and focus states",
                    "Keep dropdown navigation and accessibility checks intact",
                ],
                "blocked_actions": [
                    "commit",
                    "push",
                    "publish",
                    "analytics",
                    "ads",
                    "affiliate_links",
                    "lead_capture",
                    "outreach",
                ],
            },
            "results": results,
        }

        JSON_OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Visual Polish Audit",
            "",
            f"Generated: {proof['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: {proof['status']}",
            f"- Pages checked: {proof['pages_checked']}",
            f"- Opportunity counts: `{proof['opportunity_counts']}`",
            "",
            "## Recommended Visual Polish Pass 001",
            "",
        ]

        for item in proof["recommended_pass"]["scope"]:
            lines.append(f"- {item}")

        lines.extend(["", "## Page Notes", ""])

        for result in results:
            lines.append(f"### {result['relative']}")
            lines.append("")
            lines.append(f"- Title: `{result['title']}`")
            lines.append(f"- H1: `{result['h1']}`")
            lines.append(f"- Inputs: `{result['input_count']}`")
            lines.append(f"- Buttons: `{result['button_count']}`")
            lines.append(f"- Card mentions: `{result['card_mentions']}`")
            lines.append(f"- Result mentions: `{result['result_mentions']}`")
            lines.append(f"- Dropdown: `{result['has_dropdown']}`")
            lines.append(f"- Root option present: `{result['has_root_option']}`")
            lines.append(f"- Opportunities: `{result['opportunities']}`")
            lines.append("")

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")

        print("NOTHINGBUTA VISUAL POLISH AUDIT:", proof["status"])
        print("pages_checked:", proof["pages_checked"])
        print("opportunity_counts:", proof["opportunity_counts"])
        print("json:", JSON_OUT)
        print("markdown:", MD_OUT)
        return 0

    except Exception as exc:
        logger.exception("Visual polish audit failed")
        print("NOTHINGBUTA VISUAL POLISH AUDIT: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
