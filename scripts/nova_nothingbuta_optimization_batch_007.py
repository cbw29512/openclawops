from __future__ import annotations

import logging
import sys
from pathlib import Path


# Objective:
# Apply NothingButA Optimization Batch 007 to the break-even calculator using
# the shared nothingbuta_optimizer core.
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
TARGET_SLUG = "break-even-calculator"
BATCH_NUMBER = "007"

config = PageOptimizationConfig(
    batch_id="nothingbuta-optimization-batch-007",
    batch_number=BATCH_NUMBER,
    target_slug=TARGET_SLUG,
    target_path=DOCS_DIR / TARGET_SLUG / "index.html",
    backup_root=ROOT / "nothingbuta" / "docs_backups",
    data_dir=ROOT / "data",
    reports_dir=ROOT / "reports",
    json_out=ROOT / "data" / "nothingbuta_optimization_batch_007.json",
    md_out=ROOT / "reports" / "nothingbuta-optimization-batch-007.md",
    content_marker="nothingbuta-optimization-batch-007-content",
    schema_marker="nothingbuta-optimization-batch-007-schema",
    new_meta_description=(
        "Calculate the break-even point for a product, service, or project by comparing fixed costs, "
        "variable costs, and price per sale."
    ),
    app_name="NothingButA Break-Even Calculator",
    app_url="https://cbw29512.github.io/nothingbuta/break-even-calculator/",
    application_category="BusinessApplication",
    section_label="break-even-growth-help",
    section_heading="Make the break-even estimate useful",
    how_to_heading="How to use this calculator",
    how_to_body=(
        "Enter your fixed costs, variable cost per unit, and price per sale. The calculator estimates "
        "how many sales you may need before revenue covers the costs."
    ),
    result_heading="What the result means",
    result_body=(
        "Treat the result as a planning estimate. The real break-even point can change if pricing, "
        "supplies, labor, platform fees, refunds, or marketing costs shift."
    ),
    next_heading="Useful next checks",
    next_body=(
        "After finding break-even, compare the result with ROI, conversion rate, churn rate, and the "
        "amount of traffic or sales volume needed to make the project worthwhile."
    ),
    related_tools=[
        RelatedTool(
            slug="roi-calculator",
            name="Simple ROI Calculator",
            why="Estimate whether the project return is worth the cost.",
        ),
        RelatedTool(
            slug="conversion-rate-calculator",
            name="Conversion Rate Calculator",
            why="Estimate how many visitors or leads may turn into sales.",
        ),
        RelatedTool(
            slug="churn-rate-calculator",
            name="Churn Rate Calculator",
            why="Account for customer loss when planning recurring revenue.",
        ),
        RelatedTool(
            slug="freelance-rate-calculator",
            name="Freelance Rate Calculator",
            why="Compare break-even against the value of your time.",
        ),
    ],
)

if __name__ == "__main__":
    raise SystemExit(run_optimization(config))
