from __future__ import annotations

import html
import logging
from datetime import datetime
from pathlib import Path


# Objective:
# Rebuild the public NothingButA root page as a clean tool directory.
#
# State logic:
# - docs/index.html is the GitHub Pages root page.
# - docs/*/index.html are public tool pages.
# - Root page should be public-safe because GitHub Pages can be accessed by URL.
#
# This script DOES:
# - discover all public tool folders
# - rebuild docs/index.html so it shows every tool
# - avoid admin/dashboard/internal wording
#
# This script DOES NOT:
# - commit
# - push
# - change GitHub Pages settings
# - add analytics
# - add ads
# - add affiliate links
# - add lead capture
# - do outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_rebuild_root_directory")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
REPO_ROOT = ROOT / "nothingbuta" / "github" / "nothingbuta"
DOCS_DIR = REPO_ROOT / "docs"
INDEX_PATH = DOCS_DIR / "index.html"


SPECIAL_NAMES = {
    "roi-calculator": "Simple ROI Calculator",
    "paycheck-estimator": "Paycheck Take-Home Estimator",
    "hourly-to-salary-calculator": "Hourly to Salary Calculator",
}


def friendly_name(slug: str) -> str:
    try:
        if slug in SPECIAL_NAMES:
            return SPECIAL_NAMES[slug]

        return slug.replace("-", " ").title().replace(" And ", " and ")

    except Exception as exc:
        logger.exception("Failed to create friendly name")
        raise RuntimeError(f"Failed to create friendly name for {slug}") from exc


def collect_tools() -> list[dict]:
    try:
        tools = []

        for index_file in sorted(DOCS_DIR.glob("*/index.html")):
            slug = index_file.parent.name
            tools.append(
                {
                    "slug": slug,
                    "name": friendly_name(slug),
                    "url": f"{slug}/",
                }
            )

        return sorted(tools, key=lambda item: item["name"])

    except Exception as exc:
        logger.exception("Failed to collect tools")
        raise RuntimeError("Failed to collect tools") from exc


def build_cards(tools: list[dict]) -> str:
    try:
        cards = []

        for tool in tools:
            name = html.escape(tool["name"])
            url = html.escape(tool["url"])

            cards.append(
                f"""
        <a class="tool-card" href="{url}">
          <span class="badge">Live</span>
          <strong>{name}</strong>
          <span>Open this simple utility.</span>
        </a>
""".rstrip()
            )

        return "\n".join(cards)

    except Exception as exc:
        logger.exception("Failed to build cards")
        raise RuntimeError("Failed to build cards") from exc


def build_page(tools: list[dict]) -> str:
    generated = datetime.now().astimezone().isoformat(timespec="seconds")
    cards = build_cards(tools)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NothingButA Tools</title>
  <meta name="description" content="A clean directory of simple NothingButA utility tools.">
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f8fc;
      --card: #ffffff;
      --ink: #0f172a;
      --muted: #475569;
      --line: rgba(15, 23, 42, 0.12);
      --blue: #2563eb;
      --blue-dark: #1e3a8a;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(circle at top left, #e0edff, transparent 28rem), var(--bg);
      color: var(--ink);
    }}

    main {{
      width: min(1120px, calc(100% - 2rem));
      margin: 0 auto;
      padding: 2rem 0 3rem;
    }}

    .hero {{
      display: grid;
      gap: 1rem;
      padding: 2rem;
      border-radius: 28px;
      background: linear-gradient(135deg, var(--blue-dark), var(--blue));
      color: white;
      box-shadow: 0 24px 60px rgba(37, 99, 235, 0.20);
    }}

    .eyebrow {{
      width: fit-content;
      padding: 0.35rem 0.7rem;
      border: 1px solid rgba(255,255,255,0.35);
      border-radius: 999px;
      font-size: 0.82rem;
      font-weight: 800;
      background: rgba(255,255,255,0.12);
    }}

    h1 {{
      max-width: 820px;
      margin: 0;
      font-size: clamp(2.25rem, 7vw, 5rem);
      line-height: 0.95;
      letter-spacing: -0.07em;
    }}

    .hero p {{
      max-width: 680px;
      margin: 0;
      font-size: 1.08rem;
      line-height: 1.65;
    }}

    .meta {{
      margin-top: 1rem;
      color: #64748b;
      font-size: 0.92rem;
    }}

    .section-head {{
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 1rem;
      margin: 2rem 0 1rem;
    }}

    h2 {{
      margin: 0;
      font-size: clamp(1.5rem, 3vw, 2.25rem);
      letter-spacing: -0.04em;
    }}

    .count {{
      color: var(--muted);
      font-weight: 700;
    }}

    .tool-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 0.85rem;
    }}

    .tool-card {{
      min-height: 145px;
      display: grid;
      align-content: start;
      gap: 0.65rem;
      padding: 1rem;
      border: 1px solid var(--line);
      border-radius: 20px;
      background: rgba(255,255,255,0.92);
      color: inherit;
      text-decoration: none;
      box-shadow: 0 14px 35px rgba(15, 23, 42, 0.06);
    }}

    .tool-card:hover {{
      transform: translateY(-1px);
      border-color: rgba(37, 99, 235, 0.35);
    }}

    .tool-card strong {{
      font-size: 1.05rem;
    }}

    .tool-card span:last-child {{
      color: var(--muted);
      line-height: 1.45;
    }}

    .badge {{
      width: fit-content;
      padding: 0.25rem 0.55rem;
      border-radius: 999px;
      background: #dbeafe;
      color: #1d4ed8;
      font-size: 0.78rem;
      font-weight: 900;
    }}

    footer {{
      margin-top: 2rem;
      padding-top: 1rem;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 0.9rem;
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <span class="eyebrow">NothingButA utility tools</span>
      <h1>One clear tool for one clear job.</h1>
      <p>Pick the calculator or utility you need. No account wall, no clutter, no long setup.</p>
    </section>

    <div class="section-head">
      <h2>Available tools</h2>
      <span class="count">{len(tools)} live tools</span>
    </div>

    <section class="tool-grid" aria-label="Available NothingButA tools">
{cards}
    </section>

    <footer>
      NothingButA tools directory. Last rebuilt locally: {html.escape(generated)}.
    </footer>
  </main>
</body>
</html>
"""


def main() -> int:
    try:
        if not DOCS_DIR.exists():
            raise RuntimeError(f"Docs directory missing: {DOCS_DIR}")

        tools = collect_tools()

        if len(tools) < 25:
            raise RuntimeError(f"Expected at least 25 tools, found {len(tools)}")

        INDEX_PATH.write_text(build_page(tools), encoding="utf-8")

        print("NOTHINGBUTA ROOT DIRECTORY REBUILD: PASS")
        print("tools_found:", len(tools))
        print("index:", INDEX_PATH)
        return 0

    except Exception as exc:
        logger.exception("Root directory rebuild failed")
        print("NOTHINGBUTA ROOT DIRECTORY REBUILD: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
