from __future__ import annotations

import logging
import sys
from pathlib import Path


# Objective:
# Apply NothingButA Optimization Batch 008 to the conversion rate calculator
# using the shared nothingbuta_optimizer core.
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
logger = logging.getLogger("nothingbuta_optimization_batch_008")

ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from nothingbuta_optimizer import PageOptimizationConfig, RelatedTool, run_optimization


def build_config() -> PageOptimizationConfig:
    try:
        repo_root = ROOT / "nothingbuta" / "github" / "nothingbuta"
        docs_dir = repo_root / "docs"
        target_slug = "conversion-rate-calculator"
        batch_number = "008"

        return PageOptimizationConfig(
            batch_id="nothingbuta-optimization-batch-008",
            batch_number=batch_number,
            target_slug=target_slug,
            target_path=docs_dir / target_slug / "index.html",
            backup_root=ROOT / "nothingbuta" / "docs_backups",
            data_dir=ROOT / "data",
            reports_dir=ROOT / "reports",
            json_out=ROOT / "data" / "nothingbuta_optimization_batch_008.json",
            md_out=ROOT / "reports" / "nothingbuta-optimization-batch-008.md",
            content_marker="nothingbuta-optimization-batch-008-content",
            schema_marker="nothingbuta-optimization-batch-008-schema",
            new_meta_description=(
                "Calculate conversion rate from visitors, leads, signups, or sales so you can measure "
                "how well traffic turns into results."
            ),
            app_name="NothingButA Conversion Rate Calculator",
            app_url="https://cbw29512.github.io/nothingbuta/conversion-rate-calculator/",
            application_category="BusinessApplication",
            section_label="conversion-rate-growth-help",
            section_heading="Make the conversion rate estimate useful",
            how_to_heading="How to use this calculator",
            how_to_body=(
                "Enter the number of conversions and the total number of visitors, leads, views, or clicks. "
                "The calculator turns those numbers into a conversion rate percentage."
            ),
            result_heading="What the result means",
            result_body=(
                "Treat the result as a measurement signal, not a full diagnosis. A conversion rate can rise "
                "or fall because of offer quality, page speed, traffic source, pricing, trust, timing, or audience fit."
            ),
            next_heading="Useful next checks",
            next_body=(
                "After calculating conversion rate, compare it with break-even point, ROI, churn rate, and the "
                "cost or effort required to produce each conversion."
            ),
            related_tools=[
                RelatedTool(
                    slug="roi-calculator",
                    name="Simple ROI Calculator",
                    why="Estimate whether the conversions are worth the cost.",
                ),
                RelatedTool(
                    slug="break-even-calculator",
                    name="Break-Even Calculator",
                    why="See how many sales you may need to cover costs.",
                ),
                RelatedTool(
                    slug="churn-rate-calculator",
                    name="Churn Rate Calculator",
                    why="Measure how many customers you lose after converting them.",
                ),
                RelatedTool(
                    slug="freelance-rate-calculator",
                    name="Freelance Rate Calculator",
                    why="Compare conversion work against the value of your time.",
                ),
            ],
        )
    except Exception as exc:
        logger.exception("Failed to build Batch 008 config")
        raise RuntimeError("Failed to build Batch 008 config") from exc


def main() -> int:
    try:
        return run_optimization(build_config())
    except Exception as exc:
        logger.exception("Batch 008 failed")
        print("NOTHINGBUTA OPTIMIZATION BATCH 008: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
