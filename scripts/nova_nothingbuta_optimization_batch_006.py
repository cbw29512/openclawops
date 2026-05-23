from __future__ import annotations

import logging
import sys
from pathlib import Path


# Objective:
# Apply NothingButA Optimization Batch 006 to the ROI calculator using the
# shared nothingbuta_optimizer core.
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

ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from nothingbuta_optimizer import PageOptimizationConfig, RelatedTool, run_optimization


REPO_ROOT = ROOT / "nothingbuta" / "github" / "nothingbuta"
DOCS_DIR = REPO_ROOT / "docs"
TARGET_SLUG = "roi-calculator"
BATCH_NUMBER = "006"

config = PageOptimizationConfig(
    batch_id="nothingbuta-optimization-batch-006",
    batch_number=BATCH_NUMBER,
    target_slug=TARGET_SLUG,
    target_path=DOCS_DIR / TARGET_SLUG / "index.html",
    backup_root=ROOT / "nothingbuta" / "docs_backups",
    data_dir=ROOT / "data",
    reports_dir=ROOT / "reports",
    json_out=ROOT / "data" / "nothingbuta_optimization_batch_006.json",
    md_out=ROOT / "reports" / "nothingbuta-optimization-batch-006.md",
    content_marker="nothingbuta-optimization-batch-006-content",
    schema_marker="nothingbuta-optimization-batch-006-schema",
    new_meta_description=(
        "Estimate return on investment by comparing gain, cost, and profit so you can judge "
        "whether a project, campaign, or purchase is worth it."
    ),
    app_name="NothingButA Simple ROI Calculator",
    app_url="https://cbw29512.github.io/nothingbuta/roi-calculator/",
    application_category="BusinessApplication",
    section_label="roi-growth-help",
    section_heading="Make the ROI estimate useful",
    how_to_heading="How to use this calculator",
    how_to_body=(
        "Enter the cost of the investment and the return or gain you expect from it. "
        "The calculator estimates ROI so you can compare options using a simple percentage."
    ),
    result_heading="What the result means",
    result_body=(
        "Treat the result as a planning estimate, not a guaranteed outcome. ROI can change if "
        "costs rise, sales fall, timelines stretch, or the return is harder to measure than expected."
    ),
    next_heading="Useful next checks",
    next_body=(
        "After estimating ROI, compare it with break-even point, conversion rate, churn rate, "
        "and the time or labor required to get the return."
    ),
    related_tools=[
        RelatedTool(
            slug="break-even-calculator",
            name="Break-Even Calculator",
            why="See how much you need to sell before a project pays for itself.",
        ),
        RelatedTool(
            slug="conversion-rate-calculator",
            name="Conversion Rate Calculator",
            why="Measure how well traffic or leads turn into results.",
        ),
        RelatedTool(
            slug="churn-rate-calculator",
            name="Churn Rate Calculator",
            why="Account for customer loss when estimating return.",
        ),
        RelatedTool(
            slug="freelance-rate-calculator",
            name="Freelance Rate Calculator",
            why="Compare ROI against the value of your time.",
        ),
    ],
)

if __name__ == "__main__":
    raise SystemExit(run_optimization(config))
