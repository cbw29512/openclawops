from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path


# Objective:
# Automatically optimize every remaining NothingButA page that still has an SEO score > 0.
#
# State:
# - We already proved the one-page optimizer loop works.
# - The shared nothingbuta_optimizer core is installed and tested.
# - This script uses the current SEO report as the source of truth.
#
# This script DOES:
# - read the current SEO growth report
# - select every page with priority_score > 0
# - generate config for each target
# - run the shared optimizer for each target
# - write a bulk proof report
#
# This script DOES NOT:
# - commit
# - push
# - publish
# - change GitHub Pages settings
# - add analytics, ads, affiliate links, lead capture, or outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_bulk_optimize_remaining")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS_DIR = ROOT / "scripts"
REPO_ROOT = ROOT / "nothingbuta" / "github" / "nothingbuta"
DOCS_DIR = REPO_ROOT / "docs"

REPORT_PATH = ROOT / "data" / "nothingbuta_seo_growth_research_report.json"
BULK_JSON_OUT = ROOT / "data" / "nothingbuta_bulk_optimization_remaining.json"
BULK_MD_OUT = ROOT / "reports" / "nothingbuta-bulk-optimization-remaining.md"

BATCH_START = 11

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from nothingbuta_optimizer import PageOptimizationConfig, RelatedTool, run_optimization


FOCUS_BY_SLUG = {
    "loan-early-payoff-calculator": "compare extra payments, payoff timing, and interest savings",
    "sales-tax-calculator": "estimate tax, subtotal, and final price before checkout",
    "time-card-calculator": "add work hours, breaks, and totals for a pay period",
    "recipe-scale-calculator": "resize ingredients when changing servings or batch size",
    "percentage-change-calculator": "measure increase, decrease, and percent difference between values",
    "paint-coverage-calculator": "estimate paint needs from room size, coats, and coverage",
    "concrete-calculator": "estimate concrete volume for slabs, posts, or small projects",
    "car-payment-calculator": "estimate monthly auto payments from price, rate, term, and down payment",
    "flooring-calculator": "estimate flooring material needs from room size and waste allowance",
    "discount-calculator": "calculate sale price, discount amount, and final cost",
    "tip-calculator": "split a tip and bill total quickly and clearly",
    "days-between-dates-calculator": "count days between two dates for planning or deadlines",
    "emergency-fund-calculator": "estimate how much emergency savings may cover monthly expenses",
    "unit-price-calculator": "compare package prices by unit cost before buying",
}

GROUPS = {
    "money": [
        "loan-early-payoff-calculator", "car-payment-calculator", "emergency-fund-calculator",
        "savings-goal-calculator", "debt-payoff-calculator", "paycheck-estimator",
    ],
    "shopping": [
        "sales-tax-calculator", "discount-calculator", "tip-calculator",
        "unit-price-calculator", "percentage-change-calculator",
    ],
    "home": [
        "paint-coverage-calculator", "concrete-calculator", "flooring-calculator",
    ],
    "time": [
        "time-card-calculator", "days-between-dates-calculator",
    ],
    "kitchen": [
        "recipe-scale-calculator", "unit-price-calculator",
    ],
}


def load_report() -> dict:
    try:
        if not REPORT_PATH.exists():
            raise RuntimeError(f"Missing SEO report: {REPORT_PATH}")

        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.exception("Failed to load SEO report")
        raise RuntimeError("Failed to load SEO report") from exc


def clean_title(title: str, slug: str) -> str:
    try:
        if title:
            return title.replace("NothingButA ", "").strip()

        return " ".join(part.capitalize() for part in slug.split("-"))
    except Exception as exc:
        logger.exception("Failed to clean title")
        raise RuntimeError("Failed to clean title") from exc


def find_group(slug: str) -> str:
    try:
        for group_name, slugs in GROUPS.items():
            if slug in slugs:
                return group_name

        return "general"
    except Exception as exc:
        logger.exception("Failed to find group")
        raise RuntimeError("Failed to find group") from exc


def related_for(slug: str) -> list[RelatedTool]:
    try:
        group = find_group(slug)
        group_slugs = GROUPS.get(group, [])

        tools: list[RelatedTool] = []

        for related_slug in group_slugs:
            if related_slug == slug:
                continue

            related_path = DOCS_DIR / related_slug / "index.html"
            if not related_path.exists():
                continue

            name = clean_title("", related_slug)
            tools.append(
                RelatedTool(
                    slug=related_slug,
                    name=name,
                    why="Use this next when comparing related numbers or planning the next step.",
                )
            )

            if len(tools) >= 4:
                break

        return tools
    except Exception as exc:
        logger.exception("Failed to build related tools")
        raise RuntimeError("Failed to build related tools") from exc


def category_for(slug: str) -> str:
    try:
        group = find_group(slug)

        if group in {"money"}:
            return "FinanceApplication"

        if group in {"shopping", "home", "time", "kitchen"}:
            return "UtilitiesApplication"

        return "UtilitiesApplication"
    except Exception as exc:
        logger.exception("Failed to build application category")
        raise RuntimeError("Failed to build application category") from exc


def build_config(page: dict, batch_number: int) -> PageOptimizationConfig:
    try:
        slug = page["slug"]
        title = clean_title(page.get("title", ""), slug)
        focus = FOCUS_BY_SLUG.get(slug, f"estimate and compare values with the {title.lower()}")

        batch_text = f"{batch_number:03d}"

        return PageOptimizationConfig(
            batch_id=f"nothingbuta-optimization-batch-{batch_text}",
            batch_number=batch_text,
            target_slug=slug,
            target_path=DOCS_DIR / slug / "index.html",
            backup_root=ROOT / "nothingbuta" / "docs_backups",
            data_dir=ROOT / "data",
            reports_dir=ROOT / "reports",
            json_out=ROOT / "data" / f"nothingbuta_optimization_batch_{batch_text}.json",
            md_out=ROOT / "reports" / f"nothingbuta-optimization-batch-{batch_text}.md",
            content_marker=f"nothingbuta-optimization-batch-{batch_text}-content",
            schema_marker=f"nothingbuta-optimization-batch-{batch_text}-schema",
            new_meta_description=(
                f"Use the {title} to {focus}. Enter your numbers to get a clearer result "
                f"for planning, comparison, or budgeting."
            ),
            app_name=f"NothingButA {title}",
            app_url=f"https://cbw29512.github.io/nothingbuta/{slug}/",
            application_category=category_for(slug),
            section_label=f"{slug}-growth-help",
            section_heading=f"Make the {title.lower()} useful",
            how_to_heading="How to use this calculator",
            how_to_body=(
                f"Enter the requested numbers for the {title.lower()}. The calculator uses those "
                f"inputs to produce a clear estimate you can use for planning or comparison."
            ),
            result_heading="What the result means",
            result_body=(
                "Treat the result as a planning estimate, not a guarantee. Real-world totals can change "
                "because of fees, timing, taxes, rounding, usage, price changes, or missing inputs."
            ),
            next_heading="Useful next checks",
            next_body=(
                "After reviewing the result, compare it with your budget, timeline, other costs, "
                "and any related tools that help complete the decision."
            ),
            related_tools=related_for(slug),
        )
    except Exception as exc:
        logger.exception("Failed to build config for page")
        raise RuntimeError("Failed to build config for page") from exc


def select_targets(report: dict) -> list[dict]:
    try:
        pages = report.get("pages", [])

        targets = [
            page
            for page in pages
            if int(page.get("priority_score", 0)) > 0
            and page.get("slug") in FOCUS_BY_SLUG
        ]

        return sorted(targets, key=lambda item: int(item.get("priority_score", 0)), reverse=True)
    except Exception as exc:
        logger.exception("Failed to select targets")
        raise RuntimeError("Failed to select targets") from exc


def write_bulk_report(proof: dict) -> None:
    try:
        BULK_JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
        BULK_MD_OUT.parent.mkdir(parents=True, exist_ok=True)

        BULK_JSON_OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Bulk Optimization Remaining",
            "",
            f"Generated: {proof['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: `{proof['status']}`",
            f"- Targets attempted: `{proof['targets_attempted']}`",
            f"- Targets passed: `{proof['targets_passed']}`",
            f"- Targets failed: `{proof['targets_failed']}`",
            "",
            "## Results",
            "",
        ]

        for item in proof["results"]:
            lines.append(
                f"- `{item['slug']}` batch `{item['batch_number']}` status `{item['status']}`"
            )

        BULK_MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        logger.exception("Failed to write bulk report")
        raise RuntimeError("Failed to write bulk report") from exc


def main() -> int:
    try:
        report = load_report()
        targets = select_targets(report)

        if not targets:
            print("NOTHINGBUTA BULK OPTIMIZATION REMAINING: PASS")
            print("No remaining known targets with priority_score > 0.")
            return 0

        results = []

        for index, page in enumerate(targets):
            batch_number = BATCH_START + index
            config = build_config(page, batch_number)
            exit_code = run_optimization(config)

            results.append(
                {
                    "slug": config.target_slug,
                    "batch_number": config.batch_number,
                    "status": "PASS" if exit_code == 0 else "FAILED",
                    "exit_code": exit_code,
                }
            )

            if exit_code != 0:
                break

        failed = [item for item in results if item["status"] != "PASS"]

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "PASS" if not failed else "FAILED",
            "targets_attempted": len(results),
            "targets_passed": len([item for item in results if item["status"] == "PASS"]),
            "targets_failed": len(failed),
            "results": results,
            "blocked_actions": [
                "commit", "push", "publish", "github_pages_changes",
                "analytics", "ads", "affiliate_links", "lead_capture", "outreach",
            ],
        }

        write_bulk_report(proof)

        print("NOTHINGBUTA BULK OPTIMIZATION REMAINING:", proof["status"])
        print("targets_attempted:", proof["targets_attempted"])
        print("targets_passed:", proof["targets_passed"])
        print("targets_failed:", proof["targets_failed"])
        print("json:", BULK_JSON_OUT)
        print("markdown:", BULK_MD_OUT)

        return 0 if proof["status"] == "PASS" else 1

    except Exception as exc:
        logger.exception("Bulk optimization failed")
        print("NOTHINGBUTA BULK OPTIMIZATION REMAINING: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
