from __future__ import annotations

import json
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path


# Objective:
# Apply NothingButA Optimization Batch 004 to the paycheck estimator.
#
# State / Data Schema:
# - batch_id identifies this one-page optimization pass.
# - target_slug keeps the patch scoped to one public tool page.
# - backup_path preserves the exact pre-patch HTML.
# - changes records what the script added.
# - problems records self-check failures.
#
# This script DOES:
# - improve the meta description
# - add WebApplication JSON-LD structured data
# - add helpful user-facing copy
# - add related tool cards
# - create a backup
# - write JSON/Markdown proof reports
#
# This script DOES NOT:
# - change calculator math logic
# - commit
# - push
# - publish
# - change GitHub Pages settings
# - add analytics, ads, affiliate links, lead capture, or outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_optimization_batch_004")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
REPO_ROOT = ROOT / "nothingbuta" / "github" / "nothingbuta"
DOCS_DIR = REPO_ROOT / "docs"

TARGET_SLUG = "paycheck-estimator"
TARGET_PATH = DOCS_DIR / TARGET_SLUG / "index.html"

BACKUP_ROOT = ROOT / "nothingbuta" / "docs_backups"
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

BATCH_ID = "nothingbuta-optimization-batch-004"
CONTENT_MARKER = "nothingbuta-optimization-batch-004-content"
SCHEMA_MARKER = "nothingbuta-optimization-batch-004-schema"
ROOT_DROPDOWN_OPTION = '<option value="../">All tools home</option>'

JSON_OUT = DATA_DIR / "nothingbuta_optimization_batch_004.json"
MD_OUT = REPORTS_DIR / "nothingbuta-optimization-batch-004.md"

NEW_META_DESCRIPTION = (
    "Estimate take-home pay from gross income using pay frequency, taxes, deductions, "
    "and withholding assumptions before planning your budget."
)

RELATED_TOOLS = [
    {
        "slug": "hourly-to-salary-calculator",
        "name": "Hourly to Salary Calculator",
        "why": "Convert hourly wages into annual gross pay first.",
    },
    {
        "slug": "rent-affordability-calculator",
        "name": "Rent Affordability Calculator",
        "why": "Compare take-home pay against a realistic rent range.",
    },
    {
        "slug": "savings-goal-calculator",
        "name": "Savings Goal Calculator",
        "why": "Turn estimated paychecks into monthly savings targets.",
    },
    {
        "slug": "debt-payoff-calculator",
        "name": "Debt Payoff Calculator",
        "why": "See how income can support faster debt payoff.",
    },
]

STRUCTURED_DATA = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    "name": "NothingButA Paycheck Take-Home Estimator",
    "url": "https://cbw29512.github.io/nothingbuta/paycheck-estimator/",
    "applicationCategory": "FinanceApplication",
    "operatingSystem": "Any",
    "description": NEW_META_DESCRIPTION,
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
        logger.exception("Failed to read %s", path)
        raise RuntimeError(f"Failed to read {path}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.write_text(text, encoding="utf-8")
    except Exception as exc:
        logger.exception("Failed to write %s", path)
        raise RuntimeError(f"Failed to write {path}") from exc


def backup_target() -> Path:
    try:
        BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = BACKUP_ROOT / f"{TARGET_SLUG}-before-optimization-004-{stamp}.html"
        shutil.copy2(TARGET_PATH, backup_path)
        return backup_path
    except Exception as exc:
        logger.exception("Failed to back up target")
        raise RuntimeError("Failed to back up target") from exc


def replace_meta_description(html: str) -> tuple[str, bool]:
    try:
        pattern = re.compile(
            r'<meta\s+name=["\']description["\']\s+content=["\'][^"\']*["\']\s*/?>',
            flags=re.IGNORECASE,
        )
        replacement = f'<meta name="description" content="{NEW_META_DESCRIPTION}">'

        if pattern.search(html):
            return pattern.sub(replacement, html, count=1), True

        return re.sub(
            r"</head>",
            f"  {replacement}\n</head>",
            html,
            count=1,
            flags=re.IGNORECASE,
        ), True

    except Exception as exc:
        logger.exception("Failed to replace meta description")
        raise RuntimeError("Failed to replace meta description") from exc


def inject_structured_data(html: str) -> tuple[str, bool]:
    try:
        if SCHEMA_MARKER in html:
            return html, False

        schema_json = json.dumps(STRUCTURED_DATA, indent=2)
        block = (
            f'<script type="application/ld+json" id="{SCHEMA_MARKER}">\n'
            f"{schema_json}\n"
            "</script>"
        )

        return re.sub(
            r"</head>",
            block + "\n</head>",
            html,
            count=1,
            flags=re.IGNORECASE,
        ), True

    except Exception as exc:
        logger.exception("Failed to inject structured data")
        raise RuntimeError("Failed to inject structured data") from exc


def build_related_cards() -> str:
    try:
        cards = []

        for tool in RELATED_TOOLS:
            cards.append(
                f"""
      <a class="nba-related-card" href="../{tool['slug']}/">
        <strong>{tool['name']}</strong>
        <span>{tool['why']}</span>
      </a>
""".rstrip()
            )

        return "\n".join(cards)

    except Exception as exc:
        logger.exception("Failed to build related cards")
        raise RuntimeError("Failed to build related cards") from exc


def build_content_section() -> str:
    try:
        related_cards = build_related_cards()

        return f"""
<section class="nba-growth-section" id="{CONTENT_MARKER}" aria-labelledby="paycheck-growth-help">
  <style>
    .nba-growth-section {{
      margin: 1.5rem auto 2rem;
      padding: 1.2rem;
      border: 1px solid rgba(15, 23, 42, 0.12);
      border-radius: 24px;
      background: rgba(255,255,255,0.94);
      box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
    }}
    .nba-growth-section h2 {{
      margin: 0 0 0.7rem;
      font-size: clamp(1.35rem, 3vw, 2rem);
      letter-spacing: -0.04em;
    }}
    .nba-growth-section h3 {{
      margin: 1rem 0 0.4rem;
      font-size: 1.05rem;
    }}
    .nba-growth-section p {{
      color: #475569;
      line-height: 1.65;
      margin: 0.35rem 0;
    }}
    .nba-related-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 0.75rem;
      margin-top: 0.85rem;
    }}
    .nba-related-card {{
      display: grid;
      gap: 0.35rem;
      padding: 0.85rem;
      border: 1px solid rgba(15, 23, 42, 0.12);
      border-radius: 16px;
      background: rgba(248, 250, 252, 0.92);
      text-decoration: none;
      color: inherit;
    }}
    .nba-related-card:hover {{
      border-color: rgba(37, 99, 235, 0.35);
      transform: translateY(-1px);
    }}
    .nba-related-card span {{
      color: #475569;
      line-height: 1.45;
    }}
  </style>

  <h2 id="paycheck-growth-help">Make the paycheck estimate useful</h2>

  <h3>How to use this estimator</h3>
  <p>
    Enter your gross pay, pay frequency, tax assumptions, and recurring deductions.
    The estimator helps you turn headline income into a rough take-home number
    before you build a monthly budget.
  </p>

  <h3>What the result means</h3>
  <p>
    Treat the result as a planning estimate, not a payroll guarantee. Actual take-home
    pay can change based on federal and state taxes, benefits, retirement contributions,
    insurance premiums, withholding choices, bonuses, overtime, and employer payroll rules.
  </p>

  <h3>Useful next checks</h3>
  <p>
    After estimating take-home pay, compare it with rent, savings, debt payments,
    groceries, transportation, and emergency fund goals. A budget should be based on
    money that actually reaches your account, not only gross pay.
  </p>

  <h3>Related tools</h3>
  <div class="nba-related-grid">
{related_cards}
  </div>
</section>
""".strip()

    except Exception as exc:
        logger.exception("Failed to build content section")
        raise RuntimeError("Failed to build content section") from exc


def inject_content_section(html: str) -> tuple[str, bool]:
    try:
        if CONTENT_MARKER in html:
            return html, False

        section = build_content_section()

        if re.search(r"</main>", html, flags=re.IGNORECASE):
            return re.sub(
                r"</main>",
                section + "\n</main>",
                html,
                count=1,
                flags=re.IGNORECASE,
            ), True

        return re.sub(
            r"</body>",
            section + "\n</body>",
            html,
            count=1,
            flags=re.IGNORECASE,
        ), True

    except Exception as exc:
        logger.exception("Failed to inject content section")
        raise RuntimeError("Failed to inject content section") from exc


def self_check(html: str) -> list[str]:
    problems: list[str] = []

    try:
        if ROOT_DROPDOWN_OPTION in html:
            problems.append("root_dropdown_option_present")

        description_match = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
            html,
            flags=re.IGNORECASE,
        )

        if not description_match:
            problems.append("missing_meta_description")
        elif len(description_match.group(1)) < 90:
            problems.append("meta_description_still_too_short")

        if SCHEMA_MARKER not in html:
            problems.append("missing_structured_data")

        if CONTENT_MARKER not in html:
            problems.append("missing_growth_content_section")

        for tool in RELATED_TOOLS:
            expected = f'../{tool["slug"]}/'
            if expected not in html:
                problems.append(f"missing_related_link:{tool['slug']}")

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
            "# NothingButA Optimization Batch 004",
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
        ]

        for change in proof["changes"]:
            lines.append(f"- {change}")

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
        if not TARGET_PATH.exists():
            raise RuntimeError(f"Missing target page: {TARGET_PATH}")

        backup_path = backup_target()
        original = read_text(TARGET_PATH)

        updated = original
        changes: list[str] = []

        updated, meta_changed = replace_meta_description(updated)
        if meta_changed:
            changes.append("expanded_meta_description")

        updated, schema_changed = inject_structured_data(updated)
        if schema_changed:
            changes.append("added_webapplication_json_ld")

        updated, content_changed = inject_content_section(updated)
        if content_changed:
            changes.append("added_helpful_copy_and_related_links")

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
            "changed": updated != original and not problems,
            "changes": changes,
            "problems": problems,
        }

        write_reports(proof)

        print("NOTHINGBUTA OPTIMIZATION BATCH 004:", proof["status"])
        print("target:", TARGET_SLUG)
        print("changed:", proof["changed"])
        print("backup:", backup_path)
        print("json:", JSON_OUT)
        print("markdown:", MD_OUT)

        if problems:
            print("problems:", problems)

        return 0 if proof["status"] == "PASS" else 1

    except Exception as exc:
        logger.exception("Optimization batch failed")
        print("NOTHINGBUTA OPTIMIZATION BATCH 004: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
