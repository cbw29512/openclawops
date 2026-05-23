from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path


# Objective:
# Add public visitor navigation to NothingButA docs pages.
#
# This script DOES:
# - add a compact dropdown to each public tool page
# - add a collapsed tool directory to the homepage
# - remove internal "candidate" wording from public pages
# - replace "dashboards" wording on the public homepage
# - write proof files
#
# This script DOES NOT:
# - commit
# - push
# - publish
# - change GitHub Pages settings
# - add analytics
# - add ads
# - add affiliate links
# - add lead capture
# - do outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_public_nav_polish")


# -----------------------------
# State / paths
# -----------------------------

ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DOCS_DIR = ROOT / "nothingbuta" / "github" / "nothingbuta" / "docs"
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

JSON_OUT = DATA_DIR / "nothingbuta_public_nav_polish_proof.json"
MD_OUT = REPORTS_DIR / "nothingbuta-public-nav-polish-proof.md"


# -----------------------------
# HTML marker IDs
# Important:
# These IDs must be checked as exact HTML ids.
# Do not check with plain substring matching because:
# "nothingbuta-tool-jump-style" contains "nothingbuta-tool-jump".
# -----------------------------

STYLE_MARKER = "nothingbuta-tool-jump-style"
NAV_MARKER = "nothingbuta-tool-jump"
HOME_MARKER = "nothingbuta-home-tool-directory"


SPECIAL_NAMES = {
    "roi-calculator": "Simple ROI Calculator",
    "paycheck-estimator": "Paycheck Take-Home Estimator",
    "hourly-to-salary-calculator": "Hourly to Salary Calculator",
}


BLOCKED_ACTIONS = {
    "commit_allowed": False,
    "push_allowed": False,
    "publish_allowed": False,
    "github_pages_changes_allowed": False,
    "analytics_allowed": False,
    "ads_allowed": False,
    "affiliate_links_allowed": False,
    "lead_capture_allowed": False,
    "outreach_allowed": False,
}


def html_id_exists(text: str, element_id: str) -> bool:
    """Return True only when the exact HTML id exists.

    Under the hood:
    - This avoids substring bugs.
    - Example bug avoided:
      id="nothingbuta-tool-jump-style" should NOT count as
      id="nothingbuta-tool-jump".
    """
    try:
        pattern = rf'id=["\']{re.escape(element_id)}["\']'
        return re.search(pattern, text, flags=re.IGNORECASE) is not None

    except Exception as exc:
        logger.exception("Failed while checking HTML id: %s", element_id)
        raise RuntimeError(f"Failed while checking HTML id: {element_id}") from exc


def friendly_name(slug: str) -> str:
    """Convert a URL slug into a clean visitor-facing tool name."""
    try:
        if slug in SPECIAL_NAMES:
            return SPECIAL_NAMES[slug]

        return slug.replace("-", " ").title().replace(" And ", " and ")

    except Exception as exc:
        logger.exception("Failed to create friendly name for slug: %s", slug)
        raise RuntimeError(f"Failed to create friendly name for slug: {slug}") from exc


def collect_tools() -> list[dict]:
    """Discover public tool folders from docs/*/index.html.

    Big picture:
    - The docs folder is the public site root.
    - Every folder under docs with an index.html is treated as a public tool page.
    - docs/index.html is the homepage and is not included here.
    """
    try:
        if not DOCS_DIR.exists():
            raise RuntimeError(f"Docs folder missing: {DOCS_DIR}")

        tools: list[dict] = []

        for index_path in sorted(DOCS_DIR.glob("*/index.html")):
            slug = index_path.parent.name
            tools.append(
                {
                    "slug": slug,
                    "name": friendly_name(slug),
                }
            )

        return sorted(tools, key=lambda item: item["name"])

    except Exception as exc:
        logger.exception("Failed to collect tools")
        raise RuntimeError("Failed to collect tools") from exc


def build_style() -> str:
    """Build shared compact public navigation CSS."""
    return f"""
<style id="{STYLE_MARKER}">
  .tool-jump, .home-tool-directory {{
    margin: 0 auto;
    padding: 0.85rem 1rem;
    max-width: 1120px;
  }}

  .tool-jump {{
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 0.65rem;
  }}

  .tool-jump label, .home-tool-directory summary {{
    font-size: 0.92rem;
    font-weight: 800;
    cursor: pointer;
  }}

  .tool-jump select {{
    max-width: 290px;
    width: 100%;
    padding: 0.65rem 0.8rem;
    border: 1px solid rgba(15, 23, 42, 0.18);
    border-radius: 999px;
    background: #ffffff;
    font: inherit;
  }}

  .tool-directory-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 0.65rem;
    margin-top: 0.9rem;
  }}

  .tool-directory-grid a {{
    display: block;
    padding: 0.7rem 0.8rem;
    border: 1px solid rgba(15, 23, 42, 0.12);
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.86);
    text-decoration: none;
    color: inherit;
    font-weight: 700;
  }}

  @media (max-width: 700px) {{
    .tool-jump {{
      justify-content: stretch;
      align-items: stretch;
      flex-direction: column;
    }}

    .tool-jump select {{
      max-width: none;
    }}
  }}
</style>
""".strip()


def build_tool_dropdown(current_slug: str, tools: list[dict]) -> str:
    """Build the compact dropdown for one public tool page."""
    try:
        options = [
            '<option value="">Jump to another tool...</option>',

        ]

        for tool in tools:
            selected = " selected" if tool["slug"] == current_slug else ""
            options.append(
                f'<option value="../{tool["slug"]}/"{selected}>{tool["name"]}</option>'
            )

        return f"""
<nav class="tool-jump" id="{NAV_MARKER}" aria-label="NothingButA tool navigation">
  <label for="tool-jump-select">More NothingButA tools</label>
  <select id="tool-jump-select" onchange="if (this.value) window.location.href = this.value;">
    {"".join(options)}
  </select>
</nav>
""".strip()

    except Exception as exc:
        logger.exception("Failed to build dropdown for slug: %s", current_slug)
        raise RuntimeError(f"Failed to build dropdown for slug: {current_slug}") from exc


def build_home_directory(tools: list[dict]) -> str:
    """Build a collapsed homepage directory.

    Why details/summary:
    - It is built into HTML.
    - It keeps the homepage clean.
    - It still exposes normal anchor links for visitors and crawlers.
    """
    try:
        links = "\n    ".join(
            f'<a href="{tool["slug"]}/">{tool["name"]}</a>'
            for tool in tools
        )

        return f"""
<details class="home-tool-directory" id="{HOME_MARKER}">
  <summary>Browse all NothingButA tools</summary>
  <div class="tool-directory-grid">
    {links}
  </div>
</details>
""".strip()

    except Exception as exc:
        logger.exception("Failed to build homepage directory")
        raise RuntimeError("Failed to build homepage directory") from exc


def inject_before_head_close_or_prepend(text: str, html: str) -> str:
    """Insert CSS before </head>; fallback to prepending if no head exists."""
    try:
        if re.search(r"</head>", text, flags=re.IGNORECASE):
            return re.sub(
                r"</head>",
                html + "\n</head>",
                text,
                count=1,
                flags=re.IGNORECASE,
            )

        return html + "\n" + text

    except Exception as exc:
        logger.exception("Failed to inject style block")
        raise RuntimeError("Failed to inject style block") from exc


def inject_after_body_or_prepend(text: str, html: str) -> str:
    """Insert navigation immediately after the opening <body> tag.

    Under the hood:
    - r"<body\\b[^>]*>" would search for a literal backslash.
    - r"<body\b[^>]*>" correctly means: match <body followed by a word boundary.
    """
    try:
        match = re.search(r"<body\b[^>]*>", text, flags=re.IGNORECASE)

        if match:
            insert_at = match.end()
            return text[:insert_at] + "\n" + html + "\n" + text[insert_at:]

        return html + "\n" + text

    except Exception as exc:
        logger.exception("Failed to inject HTML block")
        raise RuntimeError("Failed to inject HTML block") from exc


def clean_public_wording(text: str) -> tuple[str, list[str]]:
    """Remove internal workflow wording from public-facing pages."""
    try:
        changes: list[str] = []
        updated = text

        if "NothingButA tool candidate" in updated:
            updated = updated.replace("NothingButA tool candidate", "NothingButA tool")
            changes.append("removed_candidate_wording")

        if "No bloated dashboards." in updated:
            updated = updated.replace("No bloated dashboards.", "No bloated menus.")
            changes.append("removed_dashboard_wording")

        return updated, changes

    except Exception as exc:
        logger.exception("Failed to clean public wording")
        raise RuntimeError("Failed to clean public wording") from exc


def patch_page(index_path: Path, tools: list[dict]) -> dict:
    """Patch one public docs page and return proof details."""
    try:
        original = index_path.read_text(encoding="utf-8")
        text = original
        changes: list[str] = []

        is_home = index_path.parent == DOCS_DIR
        slug = None if is_home else index_path.parent.name

        text, wording_changes = clean_public_wording(text)
        changes.extend(wording_changes)

        if not html_id_exists(text, STYLE_MARKER):
            text = inject_before_head_close_or_prepend(text, build_style())
            changes.append("added_public_nav_style")

        if is_home:
            if not html_id_exists(text, HOME_MARKER):
                text = inject_after_body_or_prepend(text, build_home_directory(tools))
                changes.append("added_home_tool_directory")

        if slug:
            if not html_id_exists(text, NAV_MARKER):
                text = inject_after_body_or_prepend(text, build_tool_dropdown(slug, tools))
                changes.append("added_tool_dropdown")

        changed = text != original

        if changed:
            index_path.write_text(text, encoding="utf-8")

        return {
            "path": str(index_path),
            "slug": slug,
            "is_home": is_home,
            "changed": changed,
            "changes": changes,
        }

    except Exception as exc:
        logger.exception("Failed to patch page: %s", index_path)
        raise RuntimeError(f"Failed to patch page: {index_path}") from exc


def run_self_check(results: list[dict], tools: list[dict]) -> dict:
    """Verify the patch outcome before reporting PASS.

    This does a local read-back check:
    - Every tool page must have the exact dropdown id.
    - Homepage must have the exact directory id.
    """
    try:
        problems: list[dict] = []

        for result in results:
            path = Path(result["path"])
            text = path.read_text(encoding="utf-8")

            if result["is_home"]:
                if not html_id_exists(text, HOME_MARKER):
                    problems.append(
                        {
                            "path": str(path),
                            "problem": "homepage_missing_tool_directory",
                        }
                    )
            else:
                if not html_id_exists(text, NAV_MARKER):
                    problems.append(
                        {
                            "path": str(path),
                            "problem": "tool_page_missing_dropdown",
                        }
                    )

                option_count = len(re.findall(r"<option\s+", text, flags=re.IGNORECASE))

                if option_count < min(10, len(tools)):
                    problems.append(
                        {
                            "path": str(path),
                            "problem": "tool_dropdown_too_few_options",
                            "option_count": option_count,
                        }
                    )

        return {
            "passed": len(problems) == 0,
            "problems": problems,
        }

    except Exception as exc:
        logger.exception("Self-check failed")
        raise RuntimeError("Self-check failed") from exc


def write_reports(proof: dict) -> None:
    """Write JSON and Markdown proof reports."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        JSON_OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Public Nav Polish Proof",
            "",
            f"Generated: {proof['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: {proof['status']}",
            f"- Tools found: {proof['tools_found']}",
            f"- Pages checked: {proof['pages_checked']}",
            f"- Changed files: {proof['changed_files']}",
            f"- Self-check passed: `{proof['self_check']['passed']}`",
            "",
            "## Blocked External Actions",
            "",
        ]

        for key, value in proof["blocked_actions"].items():
            lines.append(f"- {key}: `{value}`")

        lines.extend(["", "## Changed Files", ""])

        for item in proof["results"]:
            if item["changed"]:
                lines.append(f"- `{item['path']}`: {', '.join(item['changes'])}")

        if proof["self_check"]["problems"]:
            lines.extend(["", "## Self-Check Problems", ""])
            for problem in proof["self_check"]["problems"]:
                lines.append(f"- `{problem}`")

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    except Exception as exc:
        logger.exception("Failed to write proof reports")
        raise RuntimeError("Failed to write proof reports") from exc


def main() -> int:
    """Run the public navigation polish patch."""
    try:
        if not DOCS_DIR.exists():
            raise RuntimeError(f"Docs folder missing: {DOCS_DIR}")

        tools = collect_tools()

        results = [
            patch_page(index_path, tools)
            for index_path in sorted(DOCS_DIR.rglob("index.html"))
        ]

        self_check = run_self_check(results, tools)

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "PASS" if self_check["passed"] else "FAILED",
            "docs_dir": str(DOCS_DIR),
            "tools_found": len(tools),
            "pages_checked": len(results),
            "changed_files": sum(1 for item in results if item["changed"]),
            "blocked_actions": BLOCKED_ACTIONS,
            "self_check": self_check,
            "results": results,
        }

        write_reports(proof)

        print("NOTHINGBUTA PUBLIC NAV POLISH:", proof["status"])
        print("tools_found:", proof["tools_found"])
        print("pages_checked:", proof["pages_checked"])
        print("changed_files:", proof["changed_files"])
        print("self_check_passed:", proof["self_check"]["passed"])
        print("json:", JSON_OUT)
        print("markdown:", MD_OUT)

        return 0 if proof["status"] == "PASS" else 1

    except Exception as exc:
        logger.exception("Public nav polish failed")
        print("NOTHINGBUTA PUBLIC NAV POLISH: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())