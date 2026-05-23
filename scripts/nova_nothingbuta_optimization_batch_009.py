from __future__ import annotations

import logging
import sys
from pathlib import Path


# Objective:
# Apply NothingButA Optimization Batch 009 to the churn rate calculator
# using the shared nothingbuta_optimizer core.
#
# State / Data Schema:
# - batch_id: stable identifier for this one-page optimization.
# - target_slug: keeps the patch scoped to one public page.
# - config: tells the shared optimizer what page, copy, schema, and related tools to add.
#
# This script DOES:
# - define one page optimization config
# - call the reusable optimizer
# - create backup/proof reports through the shared module
#
# This script DOES NOT:
# - change calculator math logic
# - commit
# - push
# - publish
# - change GitHub Pages settings
# - add analytics, ads, affiliate links, lead capture, or outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_optimization_batch_009")

ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from nothingbuta_optimizer import PageOptimizationConfig, RelatedTool, run_optimization


def build_config() -> PageOptimizationConfig:
    try:
        repo_root = ROOT / "nothingbuta" / "github" / "nothingbuta"
        docs_dir = repo_root / "docs"
        target_slug = "churn-rate-calculator"
        batch_number = "009"

        return PageOptimizationConfig(
            batch_id="nothingbuta-optimization-batch-009",
            batch_number=batch_number,
            target_slug=target_slug,
            target_path=docs_dir / target_slug / "index.html",
            backup_root=ROOT / "nothingbuta" / "docs_backups",
            data_dir=ROOT / "data",
            reports_dir=ROOT / "reports",
            json_out=ROOT / "data" / "nothingbuta_optimization_batch_009.json",
            md_out=ROOT / "reports" / "nothingbuta-optimization-batch-009.md",
            content_marker="nothingbuta-optimization-batch-009-content",
            schema_marker="nothingbuta-optimization-batch-009-schema",
            new_meta_description=(
                "Calculate churn rate from customers lost and starting customers so you can measure "
                "retention, customer loss, and business stability."
            ),
            app_name="NothingButA Churn Rate Calculator",
            app_url="https://cbw29512.github.io/nothingbuta/churn-rate-calculator/",
            application_category="BusinessApplication",
            section_label="churn-rate-growth-help",
            section_heading="Make the churn rate estimate useful",
            how_to_heading="How to use this calculator",
            how_to_body=(
                "Enter the number of customers, subscribers, or accounts you started with and how many "
                "were lost during the period. The calculator turns those numbers into a churn rate percentage."
            ),
            result_heading="What the result means",
            result_body=(
                "Treat the result as a retention signal, not the whole story. Churn can change because of "
                "pricing, onboarding, product quality, support, seasonality, competition, or the type of customer acquired."
            ),
            next_heading="Useful next checks",
            next_body=(
                "After calculating churn rate, compare it with conversion rate, ROI, break-even point, and the "
                "cost of replacing lost customers."
            ),
            related_tools=[
                RelatedTool(
                    slug="conversion-rate-calculator",
                    name="Conversion Rate Calculator",
                    why="Measure how many visitors or leads become customers.",
                ),
                RelatedTool(
                    slug="roi-calculator",
                    name="Simple ROI Calculator",
                    why="Estimate whether customer growth is worth the cost.",
                ),
                RelatedTool(
                    slug="break-even-calculator",
                    name="Break-Even Calculator",
                    why="See how many sales or customers may be needed to cover costs.",
                ),
                RelatedTool(
                    slug="freelance-rate-calculator",
                    name="Freelance Rate Calculator",
                    why="Compare retention work against the value of your time.",
                ),
            ],
        )

    except Exception as exc:
        logger.exception("Failed to build Batch 009 config")
        raise RuntimeError("Failed to build Batch 009 config") from exc


def main() -> int:
    try:
        return run_optimization(build_config())
    except Exception as exc:
        logger.exception("Batch 009 failed")
        print("NOTHINGBUTA OPTIMIZATION BATCH 009: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
