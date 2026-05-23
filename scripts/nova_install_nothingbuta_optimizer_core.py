from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path


# Objective:
# Install a reusable NothingButA optimizer core so future optimization batches
# are small config files instead of 300-500 line duplicate scripts.
#
# This installer DOES:
# - create scripts/nothingbuta_optimizer/
# - write small module files
# - back up an existing module folder if one already exists
# - import-test the new module
# - audit line counts
# - write JSON/Markdown proof reports
#
# This installer DOES NOT:
# - edit public docs pages
# - commit
# - push
# - publish
# - change GitHub Pages
# - add analytics, ads, affiliate links, lead capture, or outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("install_nothingbuta_optimizer_core")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS_DIR = ROOT / "scripts"
MODULE_DIR = SCRIPTS_DIR / "nothingbuta_optimizer"
BACKUP_DIR = ROOT / "nothingbuta" / "optimizer_backups"
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

JSON_OUT = DATA_DIR / "nothingbuta_optimizer_core_install.json"
MD_OUT = REPORTS_DIR / "nothingbuta-optimizer-core-install.md"


MODULE_FILES = {
    "__init__.py": r'''
from .models import PageOptimizationConfig, RelatedTool
from .runner import run_optimization

__all__ = ["PageOptimizationConfig", "RelatedTool", "run_optimization"]
'''.strip(),

    "models.py": r'''
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RelatedTool:
    slug: str
    name: str
    why: str


@dataclass(frozen=True)
class PageOptimizationConfig:
    batch_id: str
    batch_number: str
    target_slug: str
    target_path: Path
    backup_root: Path
    data_dir: Path
    reports_dir: Path
    json_out: Path
    md_out: Path
    content_marker: str
    schema_marker: str
    new_meta_description: str
    app_name: str
    app_url: str
    application_category: str
    section_label: str
    section_heading: str
    how_to_heading: str
    how_to_body: str
    result_heading: str
    result_body: str
    next_heading: str
    next_body: str
    related_tools: list[RelatedTool]


def config_summary(config: PageOptimizationConfig) -> dict:
    try:
        return {
            "batch_id": config.batch_id,
            "batch_number": config.batch_number,
            "target_slug": config.target_slug,
            "target_path": str(config.target_path),
            "related_tools": [tool.slug for tool in config.related_tools],
        }
    except Exception as exc:
        logger.exception("Failed to summarize config")
        raise RuntimeError("Failed to summarize config") from exc
'''.strip(),

    "io_ops.py": r'''
from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path


logger = logging.getLogger(__name__)


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


def backup_target(target_path: Path, backup_root: Path, target_slug: str, batch_number: str) -> Path:
    try:
        if not target_path.exists():
            raise RuntimeError(f"Missing target page: {target_path}")

        backup_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = backup_root / f"{target_slug}-before-optimization-{batch_number}-{stamp}.html"
        shutil.copy2(target_path, backup_path)
        return backup_path
    except Exception as exc:
        logger.exception("Failed to back up target page")
        raise RuntimeError("Failed to back up target page") from exc
'''.strip(),

    "html_injection.py": r'''
from __future__ import annotations

import json
import logging
import re

from .models import PageOptimizationConfig, RelatedTool


logger = logging.getLogger(__name__)


def replace_meta_description(html: str, description: str) -> tuple[str, bool]:
    try:
        pattern = re.compile(
            r'<meta\s+name=["\']description["\']\s+content=["\'][^"\']*["\']\s*/?>',
            flags=re.IGNORECASE,
        )
        replacement = f'<meta name="description" content="{description}">'

        if pattern.search(html):
            return pattern.sub(replacement, html, count=1), True

        return re.sub(r"</head>", f"  {replacement}\n</head>", html, count=1, flags=re.IGNORECASE), True
    except Exception as exc:
        logger.exception("Failed to replace meta description")
        raise RuntimeError("Failed to replace meta description") from exc


def inject_structured_data(html: str, config: PageOptimizationConfig) -> tuple[str, bool]:
    try:
        if config.schema_marker in html:
            return html, False

        data = {
            "@context": "https://schema.org",
            "@type": "WebApplication",
            "name": config.app_name,
            "url": config.app_url,
            "applicationCategory": config.application_category,
            "operatingSystem": "Any",
            "description": config.new_meta_description,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        }
        block = (
            f'<script type="application/ld+json" id="{config.schema_marker}">\n'
            f"{json.dumps(data, indent=2)}\n"
            "</script>"
        )

        return re.sub(r"</head>", block + "\n</head>", html, count=1, flags=re.IGNORECASE), True
    except Exception as exc:
        logger.exception("Failed to inject structured data")
        raise RuntimeError("Failed to inject structured data") from exc


def build_related_cards(tools: list[RelatedTool]) -> str:
    try:
        cards = []
        for tool in tools:
            cards.append(
                f"""
      <a class="nba-related-card" href="../{tool.slug}/">
        <strong>{tool.name}</strong>
        <span>{tool.why}</span>
      </a>
""".rstrip()
            )
        return "\n".join(cards)
    except Exception as exc:
        logger.exception("Failed to build related cards")
        raise RuntimeError("Failed to build related cards") from exc


def build_content_section(config: PageOptimizationConfig) -> str:
    try:
        related_cards = build_related_cards(config.related_tools)

        return f"""
<section class="nba-growth-section" id="{config.content_marker}" aria-labelledby="{config.section_label}">
  <style>
    .nba-growth-section {{
      margin: 1.5rem auto 2rem;
      padding: 1.2rem;
      border: 1px solid rgba(15, 23, 42, 0.12);
      border-radius: 24px;
      background: rgba(255,255,255,0.94);
      box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
    }}
    .nba-growth-section h2 {{ margin: 0 0 0.7rem; font-size: clamp(1.35rem, 3vw, 2rem); }}
    .nba-growth-section h3 {{ margin: 1rem 0 0.4rem; font-size: 1.05rem; }}
    .nba-growth-section p {{ color: #475569; line-height: 1.65; margin: 0.35rem 0; }}
    .nba-related-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 0.75rem; margin-top: 0.85rem; }}
    .nba-related-card {{ display: grid; gap: 0.35rem; padding: 0.85rem; border: 1px solid rgba(15, 23, 42, 0.12); border-radius: 16px; background: rgba(248, 250, 252, 0.92); text-decoration: none; color: inherit; }}
    .nba-related-card span {{ color: #475569; line-height: 1.45; }}
  </style>

  <h2 id="{config.section_label}">{config.section_heading}</h2>
  <h3>{config.how_to_heading}</h3>
  <p>{config.how_to_body}</p>
  <h3>{config.result_heading}</h3>
  <p>{config.result_body}</p>
  <h3>{config.next_heading}</h3>
  <p>{config.next_body}</p>
  <h3>Related tools</h3>
  <div class="nba-related-grid">
{related_cards}
  </div>
</section>
""".strip()
    except Exception as exc:
        logger.exception("Failed to build content section")
        raise RuntimeError("Failed to build content section") from exc


def inject_content_section(html: str, config: PageOptimizationConfig) -> tuple[str, bool]:
    try:
        if config.content_marker in html:
            return html, False

        section = build_content_section(config)

        if re.search(r"</main>", html, flags=re.IGNORECASE):
            return re.sub(r"</main>", section + "\n</main>", html, count=1, flags=re.IGNORECASE), True

        return re.sub(r"</body>", section + "\n</body>", html, count=1, flags=re.IGNORECASE), True
    except Exception as exc:
        logger.exception("Failed to inject content section")
        raise RuntimeError("Failed to inject content section") from exc
'''.strip(),

    "validation.py": r'''
from __future__ import annotations

import logging
import re

from .models import PageOptimizationConfig


logger = logging.getLogger(__name__)

ROOT_DROPDOWN_OPTION = '<option value="../">All tools home</option>'


def self_check(html: str, config: PageOptimizationConfig) -> list[str]:
    try:
        problems: list[str] = []

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

        if config.schema_marker not in html:
            problems.append("missing_structured_data")

        if config.content_marker not in html:
            problems.append("missing_growth_content_section")

        for tool in config.related_tools:
            expected = f'../{tool.slug}/'
            if expected not in html:
                problems.append(f"missing_related_link:{tool.slug}")

        return problems
    except Exception as exc:
        logger.exception("Self-check failed")
        raise RuntimeError("Self-check failed") from exc
'''.strip(),

    "reporting.py": r'''
from __future__ import annotations

import json
import logging

from .models import PageOptimizationConfig


logger = logging.getLogger(__name__)


def write_reports(proof: dict, config: PageOptimizationConfig) -> None:
    try:
        config.data_dir.mkdir(parents=True, exist_ok=True)
        config.reports_dir.mkdir(parents=True, exist_ok=True)

        config.json_out.write_text(json.dumps(proof, indent=2), encoding="utf-8")

        lines = [
            f"# NothingButA Optimization Batch {config.batch_number}",
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

        config.md_out.write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        logger.exception("Failed to write reports")
        raise RuntimeError("Failed to write reports") from exc
'''.strip(),

    "runner.py": r'''
from __future__ import annotations

import logging
from datetime import datetime

from .html_injection import inject_content_section, inject_structured_data, replace_meta_description
from .io_ops import backup_target, read_text, write_text
from .models import PageOptimizationConfig
from .reporting import write_reports
from .validation import self_check


logger = logging.getLogger(__name__)


def run_optimization(config: PageOptimizationConfig) -> int:
    try:
        backup_path = backup_target(config.target_path, config.backup_root, config.target_slug, config.batch_number)
        original = read_text(config.target_path)

        updated = original
        changes: list[str] = []

        updated, meta_changed = replace_meta_description(updated, config.new_meta_description)
        if meta_changed:
            changes.append("expanded_meta_description")

        updated, schema_changed = inject_structured_data(updated, config)
        if schema_changed:
            changes.append("added_webapplication_json_ld")

        updated, content_changed = inject_content_section(updated, config)
        if content_changed:
            changes.append("added_helpful_copy_and_related_links")

        problems = self_check(updated, config)

        if not problems and updated != original:
            write_text(config.target_path, updated)

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "batch_id": config.batch_id,
            "target_slug": config.target_slug,
            "target_path": str(config.target_path),
            "backup_path": str(backup_path),
            "status": "PASS" if not problems else "FAILED",
            "changed": updated != original and not problems,
            "changes": changes,
            "problems": problems,
        }

        write_reports(proof, config)

        print(f"NOTHINGBUTA OPTIMIZATION BATCH {config.batch_number}: {proof['status']}")
        print("target:", config.target_slug)
        print("changed:", proof["changed"])
        print("backup:", backup_path)
        print("json:", config.json_out)
        print("markdown:", config.md_out)

        if problems:
            print("problems:", problems)

        return 0 if proof["status"] == "PASS" else 1
    except Exception as exc:
        logger.exception("Optimization batch failed")
        print(f"NOTHINGBUTA OPTIMIZATION BATCH {config.batch_number}: FAILED")
        print(str(exc))
        return 1
'''.strip(),
}


def write_module_files() -> list[dict]:
    try:
        if MODULE_DIR.exists():
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = BACKUP_DIR / f"nothingbuta_optimizer-{stamp}"
            shutil.copytree(MODULE_DIR, backup_path)
            backup_value = str(backup_path)
        else:
            backup_value = ""

        MODULE_DIR.mkdir(parents=True, exist_ok=True)

        written = []
        for relative_name, content in MODULE_FILES.items():
            path = MODULE_DIR / relative_name
            path.write_text(content + "\n", encoding="utf-8")
            written.append(
                {
                    "file": str(path),
                    "lines": len(content.splitlines()),
                    "over_150": len(content.splitlines()) > 150,
                }
            )

        return [{"module_backup": backup_value}, *written]
    except Exception as exc:
        logger.exception("Failed to write module files")
        raise RuntimeError("Failed to write module files") from exc


def import_test() -> None:
    try:
        import sys

        scripts_path = str(SCRIPTS_DIR)
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)

        from nothingbuta_optimizer import PageOptimizationConfig, RelatedTool, run_optimization

        if not PageOptimizationConfig or not RelatedTool or not run_optimization:
            raise RuntimeError("Import test returned empty symbols")
    except Exception as exc:
        logger.exception("Import test failed")
        raise RuntimeError("Import test failed") from exc


def write_reports(proof: dict) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        JSON_OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Optimizer Core Install",
            "",
            f"Generated: {proof['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: {proof['status']}",
            f"- Files written: `{proof['files_written']}`",
            f"- Files over 150 lines: `{proof['files_over_150']}`",
            f"- Import test passed: `{proof['import_test_passed']}`",
            "",
            "## File Line Counts",
            "",
        ]

        for item in proof["written_files"]:
            if "file" in item:
                lines.append(f"- `{item['file']}` lines=`{item['lines']}` over_150=`{item['over_150']}`")

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        logger.exception("Failed to write install reports")
        raise RuntimeError("Failed to write install reports") from exc


def main() -> int:
    try:
        written_files = write_module_files()
        import_test()

        file_rows = [item for item in written_files if "file" in item]
        files_over_150 = [item for item in file_rows if item["over_150"]]

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "PASS" if not files_over_150 else "NEEDS_REVIEW",
            "module_dir": str(MODULE_DIR),
            "files_written": len(file_rows),
            "files_over_150": len(files_over_150),
            "import_test_passed": True,
            "written_files": written_files,
            "blocked_actions": [
                "public_page_edits",
                "commit",
                "push",
                "publish",
                "github_pages_changes",
                "analytics",
                "ads",
                "affiliate_links",
                "lead_capture",
                "outreach",
            ],
        }

        write_reports(proof)

        print("NOTHINGBUTA OPTIMIZER CORE INSTALL:", proof["status"])
        print("files_written:", proof["files_written"])
        print("files_over_150:", proof["files_over_150"])
        print("import_test_passed:", proof["import_test_passed"])
        print("json:", JSON_OUT)
        print("markdown:", MD_OUT)

        return 0 if proof["status"] == "PASS" else 1
    except Exception as exc:
        logger.exception("Install failed")
        print("NOTHINGBUTA OPTIMIZER CORE INSTALL: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
