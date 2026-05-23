from __future__ import annotations

import json
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path


# Objective:
# Apply NothingButA Optimization Batch 001 to one pilot page:
# hourly-to-salary-calculator.
#
# This script DOES:
# - improve title casing
# - improve meta description depth
# - add helpful explanatory content
# - add related tool links
# - add JSON-LD structured data
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
logger = logging.getLogger("nothingbuta_optimization_batch_001")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
REPO_ROOT = ROOT / "nothingbuta" / "github" / "nothingbuta"
DOCS_DIR = REPO_ROOT / "docs"
TARGET_SLUG = "hourly-to-salary-calculator"
TARGET_PATH = DOCS_DIR / TARGET_SLUG / "index.html"

BACKUP_ROOT = ROOT / "nothingbuta" / "docs_backups"
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

BATCH_ID = "nothingbuta-optimization-batch-001"
CONTENT_MARKER = "nothingbuta-optimization-batch-001-content"
SCHEMA_MARKER = "nothingbuta-optimization-batch-001-schema"
ROOT_DROPDOWN_OPTION = '<option value="../">All tools home</option>'

JSON_OUT = DATA_DIR / "nothingbuta_optimization_batch_001.json"
MD_OUT = REPORTS_DIR / "nothingbuta-optimization-batch-001.md"

NEW_META_DESCRIPTION = (
    "Convert an hourly wage into an estimated yearly salary. "
    "Enter your hourly rate, weekly hours, and weeks worked to see annual pay before taxes."
)

RELATED_TOOLS = [
    {
        "slug": "paycheck-estimator",
        "name": "Paycheck Take-Home Estimator",
        "why": "Estimate what your pay may look like after deductions.",
    },
    {
        "slug": "debt-payoff-calculator",
        "name": "Debt Payoff Calculator",
        "why": "Plan how your income can support faster debt payoff.",
    },
    {
        "slug": "savings-goal-calculator",
        "name": "Savings Goal Calculator",
        "why": "Turn salary estimates into savings targets.",
    },
    {
        "slug": "rent-affordability-calculator",
        "name": "Rent Affordability Calculator",
        "why": "Compare income against a realistic rent budget.",
    },
]


STRUCTURED_DATA = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    "name": "NothingButA Hourly to Salary Calculator",
    "url": "https://cbw29512.github.io/nothingbuta/hourly-to-salary-calculator/",
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
        logger.exception("Failed to read file: %s", path)
        raise RuntimeError(f"Failed to read file: {path}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.write_text(text, encoding="utf-8")
    except Exception as exc:
        logger.exception("Failed to write file: %s", path)
        raise RuntimeError(f"Failed to write file: {path}") from exc


def backup_target() -> Path:
    try:
        BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = BACKUP_ROOT / f"{TARGET_SLUG}-before-optimization-001-{stamp}.html"
        shutil.copy2(TARGET_PATH, backup_path)
        return backup_path
    except Exception as exc:
        logger.exception("Failed to back up target page")
        raise RuntimeError("Failed to back up target page") from exc


def replace_title_and_h1(html: str) -> tuple[str, list[str]]:
    try:
        changes: list[str] = []
        updated = html

        replacements = {
            "NothingButA Hourly To Salary Calculator": "NothingButA Hourly to Salary Calculator",
            "Hourly To Salary Calculator": "Hourly to Salary Calculator",
        }

        for old, new in replacements.items():
            if old in updated:
                updated = updated.replace(old, new)
                changes.append(f"replaced:{old}")

        return updated, changes

    except Exception as exc:
        logger.exception("Failed to replace title/H1 casing")
        raise RuntimeError("Failed to replace title/H1 casing") from exc


def replace_meta_description(html: str) -> tuple[str, bool]:
    try:
        pattern = re.compile(
            r'<meta\s+name=["\']description["\']\s+content=["\'][^"\']*["\']\s*/?>',
            flags=re.IGNORECASE,
        )
        replacement = f'<meta name="description" content="{NEW_META_DESCRIPTION}">'

        if pattern.search(html):
            return pattern.sub(replacement, html, count=1), True

        if re.search(r"</head>", html, flags=re.IGNORECASE):
            return re.sub(
                r"</head>",
                f"  {replacement}\n</head>",
                html,
                count=1,
                flags=re.IGNORECASE,
            ), True

        return replacement + "\n" + html, True

    except Exception as exc:
        logger.exception("Failed to replace meta description")
        raise RuntimeError("Failed to replace meta description") from exc


def build_related_links_html() -> str:
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

        return f"""
<section class="nba-growth-section" id="{CONTENT_MARKER}" aria-labelledby="salary-growth-help">
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

  <h2 id="salary-growth-help">Make the salary estimate useful</h2>

  <h3>How to use this calculator</h3>
  <p>
    Enter your hourly wage, the number of hours you usually work each week,
    and how many weeks you expect to work in a year. The calculator turns
    those inputs into an estimated annual salary before taxes and deductions.
  </p>

  <h3>What the result means</h3>
  <p>
    Use the result as a planning number, not a final paycheck promise.
    Overtime, unpaid time off, taxes, benefits, retirement contributions,
    and irregular schedules can all change your actual take-home pay.
  </p>

  <h3>Related tools</h3>
  <p>
    After you estimate annual pay, these tools can help turn that number into
    a budget, savings plan, or payoff plan.
  </p>

  <div class="nba-related-grid">
{chr(10).join(cards)}
  </div>
</section>
""".strip()

    except Exception as exc:
        logger.exception("Failed to build related links HTML")
        raise RuntimeError("Failed to build related links HTML") from exc


def inject_content_section(html: str) -> tuple[str, bool]:
    try:
        if CONTENT_MARKER in html:
            return html, False

        section = build_related_links_html()

        if re.search(r"</main>", html, flags=re.IGNORECASE):
            return re.sub(
                r"</main>",
                section + "\n</main>",
                html,
                count=1,
                flags=re.IGNORECASE,
            ), True

        if re.search(r"</body>", html, flags=re.IGNORECASE):
            return re.sub(
                r"</body>",
                section + "\n</body>",
                html,
                count=1,
                flags=re.IGNORECASE,
            ), True

        return html + "\n" + section, True

    except Exception as exc:
        logger.exception("Failed to inject content section")
        raise RuntimeError("Failed to inject content section") from exc


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

        if re.search(r"</head>", html, flags=re.IGNORECASE):
            return re.sub(
                r"</head>",
                block + "\n</head>",
                html,
                count=1,
                flags=re.IGNORECASE,
            ), True

        return block + "\n" + html, True

    except Exception as exc:
        logger.exception("Failed to inject structured data")
        raise RuntimeError("Failed to inject structured data") from exc


def self_check(html: str) -> list[str]:
    try:
        problems: list[str] = []

        if ROOT_DROPDOWN_OPTION in html:
            problems.append("root_dropdown_option_present")

        if "Hourly To Salary" in html:
            problems.append("old_title_case_still_present")

        description_match = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
            html,
            flags=re.IGNORECASE,
        )

        if not description_match:
            problems.append("missing_meta_description")
        elif len(description_match.group(1)) < 90:
            problems.append("meta_description_still_too_short")

        if CONTENT_MARKER not in html:
            problems.append("missing_growth_content_section")

        if SCHEMA_MARKER not in html:
            problems.append("missing_structured_data")

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
            "# NothingButA Optimization Batch 001",
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

        updated, title_changes = replace_title_and_h1(updated)
        changes.extend(title_changes)

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

        print("NOTHINGBUTA OPTIMIZATION BATCH 001:", proof["status"])
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
        print("NOTHINGBUTA OPTIMIZATION BATCH 001: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
