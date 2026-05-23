from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any


# -----------------------------
# State schema:
# ROOT: local project root.
# POLICY_PATH: machine-readable hourly optimization policy.
# FREEZE_PACKET_PATH: frozen source of approved local preview pages.
# JSON_OUT / MD_OUT: local-only optimizer report outputs.
#
# This script does not:
# - edit pages
# - copy files
# - commit
# - push
# - publish
# - change GitHub Pages
# - add analytics
# - add ads
# - add affiliate links
# - add lead capture
# - do outreach
# -----------------------------
ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

POLICY_PATH = DATA / "nothingbuta_hourly_optimization_policy.json"
FREEZE_PACKET_PATH = DATA / "nothingbuta_release_freeze_packet.json"

JSON_OUT = DATA / "nothingbuta_hourly_optimizer_report.json"
MD_OUT = REPORTS / "nothingbuta-hourly-optimizer-report.md"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file and fail clearly if it is missing or invalid."""
    try:
        if not path.exists():
            raise FileNotFoundError(f"Missing required file: {path}")

        value = json.loads(path.read_text(encoding="utf-8"))

        if not isinstance(value, dict):
            raise ValueError(f"Expected JSON object in {path}")

        return value
    except Exception as exc:
        logging.exception("Failed to load JSON: %s", path)
        raise SystemExit(1) from exc


def read_html(path: Path) -> str:
    """Read one local preview HTML file."""
    try:
        if not path.exists():
            raise FileNotFoundError(f"Missing local preview file: {path}")

        return path.read_text(encoding="utf-8")
    except Exception as exc:
        logging.exception("Failed to read local preview: %s", path)
        raise SystemExit(1) from exc


def extract_text(pattern: str, html: str) -> str:
    """Extract a small HTML text value with regex for local static preview checks."""
    try:
        match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return ""

        text = re.sub(r"\s+", " ", match.group(1)).strip()
        return text
    except Exception:
        logging.exception("Regex extraction failed.")
        return ""


def has_any(html_lower: str, markers: list[str]) -> bool:
    """Return true when any marker exists in lowercase HTML."""
    return any(marker.lower() in html_lower for marker in markers)


def score_page(item: dict[str, Any]) -> dict[str, Any]:
    """Inspect one frozen local preview and produce a local-only improvement record."""
    try:
        path = Path(str(item.get("local_preview_path", "")))
        html = read_html(path)
        lower = html.lower()

        title = extract_text(r"<title>(.*?)</title>", html)
        meta_description = extract_text(
            r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
            html,
        )
        h1 = extract_text(r"<h1[^>]*>(.*?)</h1>", html)

        checks = {
            "has_doctype": "<!doctype html>" in lower,
            "has_viewport": 'name="viewport"' in lower or "name='viewport'" in lower,
            "has_title": bool(title),
            "has_meta_description": bool(meta_description),
            "has_h1": bool(h1),
            "has_inputs": "<input" in lower,
            "has_labels": "<label" in lower,
            "has_button": "<button" in lower,
            "has_result_area": "aria-live" in lower and "result" in lower,
            "has_faq": "faq" in lower,
            "has_media_query": "@media" in lower,
            "blocks_network_calls": not has_any(lower, ["fetch(", "xmlhttprequest", "<script src="]),
            "blocks_visitor_storage": not has_any(lower, ["document.cookie", "localstorage", "sessionstorage"]),
        }

        improvement_notes: list[str] = []

        if len(title) < 35:
            improvement_notes.append("SEO title may be too short; consider a clearer search-intent title.")
        if len(title) > 65:
            improvement_notes.append("SEO title may be too long; consider tightening it.")
        if len(meta_description) < 80:
            improvement_notes.append("Meta description may be thin; add a clearer benefit and use case.")
        if len(meta_description) > 165:
            improvement_notes.append("Meta description may be too long; tighten for search snippets.")
        if not checks["has_faq"]:
            improvement_notes.append("Add FAQ section for long-tail search intent.")
        if not checks["has_media_query"]:
            improvement_notes.append("Add mobile responsive CSS check.")
        if not checks["has_result_area"]:
            improvement_notes.append("Make result area clearer and screen-reader friendly.")
        if "nothingbuta tool candidate" in lower:
            improvement_notes.append("Remove internal candidate wording before public release.")
        if "local-only" in lower:
            improvement_notes.append("Remove local-only wording from public visitor page.")
        if item.get("slug") in {"roi-calculator", "mortgage-payment-calculator", "paycheck-estimator"}:
            if "not financial" not in lower and "not payroll" not in lower and "estimate only" not in lower:
                improvement_notes.append("Add stronger finance/payroll estimate-only disclaimer.")
        if item.get("slug") in {"concrete-calculator", "paint-coverage-calculator", "flooring-calculator"}:
            if "estimate" not in lower:
                improvement_notes.append("Add home-project estimate-only wording.")

        passed_count = sum(1 for value in checks.values() if value)
        possible_count = len(checks)
        base_score = round((passed_count / possible_count) * 100)

        penalty = min(30, len(improvement_notes) * 5)
        optimizer_score = max(0, base_score - penalty)

        decision = "keep_and_monitor"
        if optimizer_score < 80:
            decision = "needs_improvement_packet"
        if optimizer_score < 65:
            decision = "consider_replacement_or_major_rework"

        return {
            "name": item.get("name"),
            "slug": item.get("slug"),
            "local_preview_path": str(path),
            "title": title,
            "meta_description": meta_description,
            "h1": h1,
            "checks": checks,
            "passed_checks": passed_count,
            "possible_checks": possible_count,
            "optimizer_score": optimizer_score,
            "decision": decision,
            "improvement_notes": improvement_notes,
            "external_actions_allowed": False,
        }
    except Exception as exc:
        logging.exception("Failed to score page.")
        return {
            "name": item.get("name"),
            "slug": item.get("slug"),
            "local_preview_path": item.get("local_preview_path"),
            "optimizer_score": 0,
            "decision": "error_needs_review",
            "improvement_notes": [str(exc)],
            "external_actions_allowed": False,
        }


def write_outputs(policy: dict[str, Any], results: list[dict[str, Any]], blocked: list[dict[str, Any]]) -> None:
    """Write JSON and Markdown optimizer reports."""
    try:
        now = datetime.now().astimezone().isoformat(timespec="seconds")

        summary = {
            "generated_at": now,
            "policy_id": policy.get("policy_id"),
            "mission": policy.get("mission"),
            "ready_checked": len(results),
            "blocked_count": len(blocked),
            "needs_improvement_count": len([r for r in results if r["decision"] != "keep_and_monitor"]),
            "locked_safety_gates": policy.get("locked_safety_gates", {}),
            "results": results,
            "blocked_items": blocked,
        }

        JSON_OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Hourly Optimizer Report",
            "",
            f"Generated: {now}",
            "",
            "## Mission",
            "",
            str(policy.get("mission", "")),
            "",
            "## Summary",
            "",
            f"- Ready pages checked: {len(results)}",
            f"- Blocked / held back: {len(blocked)}",
            f"- Needs improvement packet: {summary['needs_improvement_count']}",
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
            "## Page Scores",
            "",
        ]

        for result in sorted(results, key=lambda r: (r["optimizer_score"], str(r["name"]))):
            lines.extend(
                [
                    f"### {result['name']}",
                    "",
                    f"- Slug: `{result['slug']}`",
                    f"- Optimizer score: `{result['optimizer_score']}`",
                    f"- Decision: `{result['decision']}`",
                    f"- Title: `{result.get('title', '')}`",
                    f"- H1: `{result.get('h1', '')}`",
                    "- Improvement notes:",
                ]
            )

            notes = result.get("improvement_notes", [])
            if not notes:
                lines.append("  - None")
            else:
                for note in notes:
                    lines.append(f"  - {note}")

            lines.append("")

        lines.extend(["## Blocked / Held Back", ""])

        for item in blocked:
            lines.extend(
                [
                    f"### {item.get('name')}",
                    "",
                    f"- Slug: `{item.get('slug')}`",
                    f"- Problems: `{item.get('audit_problems')}`",
                    "",
                ]
            )

        lines.extend(
            [
                "## Next Rule",
                "",
                "This report may recommend local-only improvement packets. It may not publish, commit, push, change GitHub Pages, add analytics, ads, affiliate links, lead capture, or outreach.",
                "",
            ]
        )

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        logging.exception("Failed to write optimizer outputs.")
        raise SystemExit(1) from exc


def main() -> None:
    """Run local-only hourly optimization inspection."""
    policy = load_json(POLICY_PATH)
    freeze = load_json(FREEZE_PACKET_PATH)

    frozen_items = freeze.get("frozen_items", [])
    blocked_items = freeze.get("blocked_items", [])

    if not isinstance(frozen_items, list):
        logging.error("frozen_items is not a list.")
        raise SystemExit(1)

    results = [score_page(item) for item in frozen_items]

    write_outputs(policy=policy, results=results, blocked=blocked_items)

    needs = [item for item in results if item["decision"] != "keep_and_monitor"]

    print("NOTHINGBUTA HOURLY OPTIMIZER REPORT: PASS")
    print(f"checked: {len(results)}")
    print(f"blocked: {len(blocked_items)}")
    print(f"needs_improvement: {len(needs)}")
    print(f"json: {JSON_OUT}")
    print(f"markdown: {MD_OUT}")


if __name__ == "__main__":
    main()