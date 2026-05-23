from __future__ import annotations

import json
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path


# Objective:
# Apply Visual Polish Pass 001 to NothingButA public docs pages.
#
# This script DOES:
# - add a reusable visual polish CSS layer to every public page
# - improve cards, forms, buttons, result areas, dropdowns, focus states, and mobile spacing
# - create a timestamped docs backup before editing
# - write JSON and Markdown proof reports
#
# This script DOES NOT:
# - change calculator JavaScript logic
# - commit
# - push
# - publish
# - change GitHub Pages settings
# - add analytics, ads, affiliate links, lead capture, or outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_visual_polish_pass_001")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
REPO_ROOT = ROOT / "nothingbuta" / "github" / "nothingbuta"
DOCS_DIR = REPO_ROOT / "docs"
BACKUP_ROOT = ROOT / "nothingbuta" / "docs_backups"
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

JSON_OUT = DATA_DIR / "nothingbuta_visual_polish_pass_001.json"
MD_OUT = REPORTS_DIR / "nothingbuta-visual-polish-pass-001.md"

STYLE_MARKER = "nothingbuta-visual-polish-pass-001"
ROOT_DROPDOWN_OPTION = '<option value="../">All tools home</option>'


VISUAL_POLISH_STYLE = f"""
<style id="{STYLE_MARKER}">
  :root {{
    --nba-bg-soft: #f6f8fc;
    --nba-panel: rgba(255, 255, 255, 0.94);
    --nba-ink: #0f172a;
    --nba-muted: #475569;
    --nba-line: rgba(15, 23, 42, 0.12);
    --nba-blue: #2563eb;
    --nba-blue-dark: #1e3a8a;
    --nba-green: #16a34a;
    --nba-shadow: 0 18px 45px rgba(15, 23, 42, 0.10);
    --nba-focus: 0 0 0 4px rgba(37, 99, 235, 0.22);
  }}

  html {{
    scroll-behavior: smooth;
  }}

  body {{
    min-height: 100vh;
    background:
      radial-gradient(circle at top left, rgba(37, 99, 235, 0.16), transparent 30rem),
      radial-gradient(circle at bottom right, rgba(22, 163, 74, 0.10), transparent 28rem),
      var(--nba-bg-soft) !important;
    color: var(--nba-ink);
  }}

  main, .wrap, .container, .page, .shell {{
    width: min(1120px, calc(100% - 2rem));
    margin-left: auto;
    margin-right: auto;
  }}

  h1 {{
    letter-spacing: -0.055em;
  }}

  h1 + p, .hero p, header p {{
    color: var(--nba-muted);
    font-size: clamp(1rem, 2vw, 1.12rem);
    line-height: 1.65;
  }}

  .tool-jump {{
    position: sticky;
    top: 0;
    z-index: 20;
    backdrop-filter: blur(14px);
    background: rgba(246, 248, 252, 0.82);
    border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  }}

  .tool-jump select {{
    border: 1px solid rgba(37, 99, 235, 0.22) !important;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.07);
  }}

  .card, section.card, .calculator, .panel, form {{
    border: 1px solid var(--nba-line) !important;
    border-radius: 24px !important;
    background: var(--nba-panel) !important;
    box-shadow: var(--nba-shadow) !important;
  }}

  form, .calculator, .card {{
    overflow: hidden;
  }}

  label {{
    font-weight: 750;
    color: var(--nba-ink);
  }}

  input, select, textarea {{
    width: 100%;
    border: 1px solid rgba(15, 23, 42, 0.18) !important;
    border-radius: 14px !important;
    padding: 0.78rem 0.9rem !important;
    background: #ffffff !important;
    color: var(--nba-ink) !important;
    box-shadow: inset 0 1px 0 rgba(15, 23, 42, 0.03);
  }}

  input:focus, select:focus, textarea:focus, button:focus-visible, a:focus-visible {{
    outline: none !important;
    box-shadow: var(--nba-focus) !important;
    border-color: rgba(37, 99, 235, 0.65) !important;
  }}

  button, .button, .btn, input[type="submit"] {{
    border: 0 !important;
    border-radius: 16px !important;
    padding: 0.85rem 1rem !important;
    background: linear-gradient(135deg, var(--nba-blue-dark), var(--nba-blue)) !important;
    color: #ffffff !important;
    font-weight: 850 !important;
    cursor: pointer;
    box-shadow: 0 14px 30px rgba(37, 99, 235, 0.22) !important;
    transition: transform 140ms ease, box-shadow 140ms ease, filter 140ms ease;
  }}

  button:hover, .button:hover, .btn:hover {{
    transform: translateY(-1px);
    filter: brightness(1.03);
    box-shadow: 0 18px 38px rgba(37, 99, 235, 0.28) !important;
  }}

  [id*="result"], [class*="result"], [id*="output"], [class*="output"], [aria-live] {{
    border-radius: 22px !important;
    border: 1px solid rgba(22, 163, 74, 0.20) !important;
    background:
      linear-gradient(135deg, rgba(22, 163, 74, 0.10), rgba(37, 99, 235, 0.08)),
      rgba(255, 255, 255, 0.94) !important;
    box-shadow: 0 16px 38px rgba(15, 23, 42, 0.08) !important;
  }}

  .tool-card {{
    transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
  }}

  .tool-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 20px 46px rgba(15, 23, 42, 0.12);
  }}

  @media (max-width: 720px) {{
    main, .wrap, .container, .page, .shell {{
      width: min(100% - 1rem, 1120px);
    }}

    .card, section.card, .calculator, .panel, form {{
      border-radius: 20px !important;
    }}

    button, .button, .btn {{
      width: 100%;
    }}
  }}
</style>
""".strip()


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


def backup_docs() -> Path:
    try:
        BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = BACKUP_ROOT / f"docs-before-visual-polish-001-{stamp}"
        shutil.copytree(DOCS_DIR, backup_dir)
        return backup_dir
    except Exception as exc:
        logger.exception("Failed to back up docs")
        raise RuntimeError("Failed to back up docs") from exc


def inject_style(html: str) -> tuple[str, bool]:
    try:
        if STYLE_MARKER in html:
            return html, False

        if re.search(r"</head>", html, flags=re.IGNORECASE):
            updated = re.sub(
                r"</head>",
                VISUAL_POLISH_STYLE + "\n</head>",
                html,
                count=1,
                flags=re.IGNORECASE,
            )
            return updated, True

        return VISUAL_POLISH_STYLE + "\n" + html, True

    except Exception as exc:
        logger.exception("Failed to inject visual polish style")
        raise RuntimeError("Failed to inject visual polish style") from exc


def patch_page(path: Path) -> dict:
    try:
        original = read_text(path)

        if ROOT_DROPDOWN_OPTION in original:
            raise RuntimeError(f"Root dropdown option regression found in {path}")

        updated, changed = inject_style(original)

        if changed:
            write_text(path, updated)

        return {
            "path": str(path),
            "changed": changed,
            "style_marker_present": STYLE_MARKER in updated,
            "root_option_present": ROOT_DROPDOWN_OPTION in updated,
        }

    except Exception as exc:
        logger.exception("Failed to patch page %s", path)
        raise RuntimeError(f"Failed to patch page {path}") from exc


def write_reports(proof: dict) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        JSON_OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Visual Polish Pass 001",
            "",
            f"Generated: {proof['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: {proof['status']}",
            f"- Pages checked: {proof['pages_checked']}",
            f"- Changed files: {proof['changed_files']}",
            f"- Backup: `{proof['backup_dir']}`",
            "",
            "## Changed Pages",
            "",
        ]

        for item in proof["results"]:
            if item["changed"]:
                lines.append(f"- `{item['path']}`")

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    except Exception as exc:
        logger.exception("Failed to write reports")
        raise RuntimeError("Failed to write reports") from exc


def main() -> int:
    try:
        if not DOCS_DIR.exists():
            raise RuntimeError(f"Docs directory missing: {DOCS_DIR}")

        pages = sorted(DOCS_DIR.rglob("index.html"))
        if len(pages) != 26:
            raise RuntimeError(f"Expected 26 index.html pages, found {len(pages)}")

        backup_dir = backup_docs()
        results = [patch_page(path) for path in pages]

        failed = [
            item for item in results
            if not item["style_marker_present"] or item["root_option_present"]
        ]

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "PASS" if not failed else "FAILED",
            "pages_checked": len(results),
            "changed_files": sum(1 for item in results if item["changed"]),
            "backup_dir": str(backup_dir),
            "results": results,
            "failed": failed,
        }

        write_reports(proof)

        print("NOTHINGBUTA VISUAL POLISH PASS 001:", proof["status"])
        print("pages_checked:", proof["pages_checked"])
        print("changed_files:", proof["changed_files"])
        print("backup:", backup_dir)
        print("json:", JSON_OUT)
        print("markdown:", MD_OUT)

        return 0 if proof["status"] == "PASS" else 1

    except Exception as exc:
        logger.exception("Visual polish pass failed")
        print("NOTHINGBUTA VISUAL POLISH PASS 001: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
