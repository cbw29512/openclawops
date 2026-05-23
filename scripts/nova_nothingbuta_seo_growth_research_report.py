from __future__ import annotations

import json
import logging
import re
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse


# Objective:
# Build a local-only SEO Growth Research Report for NothingButA.
#
# This script DOES:
# - fetch live NothingButA pages with cache-busting
# - inspect titles, descriptions, H1s, links, and visible text size
# - generate prioritized SEO/UX/content improvement recommendations
# - write JSON and Markdown reports
#
# This script DOES NOT:
# - edit files
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
logger = logging.getLogger("nothingbuta_seo_growth_research")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

JSON_OUT = DATA_DIR / "nothingbuta_seo_growth_research_report.json"
MD_OUT = REPORTS_DIR / "nothingbuta-seo-growth-research-report.md"

BASE_URL = "https://cbw29512.github.io/nothingbuta/"

ROOT_DROPDOWN_OPTION = '<option value="../">All tools home</option>'

SAFETY_GATES = {
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


TOOL_CLUSTERS = {
    "money": [
        "debt-payoff-calculator",
        "emergency-fund-calculator",
        "savings-goal-calculator",
        "paycheck-estimator",
        "hourly-to-salary-calculator",
        "rent-affordability-calculator",
    ],
    "business": [
        "break-even-calculator",
        "roi-calculator",
        "conversion-rate-calculator",
        "churn-rate-calculator",
        "freelance-rate-calculator",
    ],
    "shopping": [
        "unit-price-calculator",
        "discount-calculator",
        "sales-tax-calculator",
        "tip-calculator",
    ],
    "home": [
        "mortgage-payment-calculator",
        "car-payment-calculator",
        "flooring-calculator",
        "paint-coverage-calculator",
        "concrete-calculator",
    ],
    "time_food": [
        "time-card-calculator",
        "days-between-dates-calculator",
        "recipe-scale-calculator",
    ],
}


class SimplePageParser(HTMLParser):
    """Parse enough HTML for deterministic SEO growth recommendations."""

    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.in_h1 = False
        self.in_script = False
        self.in_style = False
        self.title = ""
        self.h1_values: list[str] = []
        self.meta: dict[str, str] = {}
        self.links: list[str] = []
        self.visible_text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_dict = {key.lower(): value or "" for key, value in attrs}

        if tag == "title":
            self.in_title = True

        if tag == "h1":
            self.in_h1 = True

        if tag == "script":
            self.in_script = True

        if tag == "style":
            self.in_style = True

        if tag == "meta":
            name = attrs_dict.get("name", "").lower()
            if name:
                self.meta[name] = attrs_dict.get("content", "")

        if tag == "a":
            href = attrs_dict.get("href", "")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag == "title":
            self.in_title = False

        if tag == "h1":
            self.in_h1 = False

        if tag == "script":
            self.in_script = False

        if tag == "style":
            self.in_style = False

    def handle_data(self, data: str) -> None:
        text = data.strip()

        if self.in_title:
            self.title += data

        if self.in_h1 and text:
            self.h1_values.append(text)

        if text and not self.in_script and not self.in_style:
            self.visible_text_parts.append(text)


def fetch_url(url: str) -> tuple[int, str]:
    """Fetch one live URL with cache-busting."""
    try:
        separator = "&" if "?" in url else "?"
        stamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        request_url = f"{url}{separator}v={stamp}"

        request = urllib.request.Request(
            request_url,
            headers={
                "User-Agent": "NothingButAGrowthResearch/1.0",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )

        with urllib.request.urlopen(request, timeout=25) as response:
            return int(response.status), response.read().decode("utf-8", errors="replace")

    except Exception as exc:
        logger.exception("Failed fetching URL: %s", url)
        raise RuntimeError(f"Failed fetching URL: {url}") from exc


def parse_page(html: str) -> SimplePageParser:
    """Turn HTML into a parser state object."""
    try:
        parser = SimplePageParser()
        parser.feed(html)
        return parser

    except Exception as exc:
        logger.exception("Failed parsing HTML")
        raise RuntimeError("Failed parsing HTML") from exc


def slug_from_url(url: str) -> str:
    """Extract a stable slug from a NothingButA URL."""
    try:
        path = urlparse(url).path.strip("/")
        parts = path.split("/")
        return parts[-1] if parts else "home"

    except Exception as exc:
        logger.exception("Failed extracting slug from URL: %s", url)
        raise RuntimeError(f"Failed extracting slug from URL: {url}") from exc


def discover_tool_urls(home_html: str) -> list[str]:
    """Find tool URLs from the root page directory cards."""
    try:
        parser = parse_page(home_html)
        urls = []

        for href in parser.links:
            if href.endswith("/") and not href.startswith(("http:", "https:", "#")):
                urls.append(urljoin(BASE_URL, href))

        unique_urls = sorted(set(urls))

        if len(unique_urls) < 25:
            raise RuntimeError(f"Expected at least 25 tool URLs, found {len(unique_urls)}")

        return unique_urls

    except Exception as exc:
        logger.exception("Failed discovering tool URLs")
        raise RuntimeError("Failed discovering tool URLs") from exc


def cluster_for_slug(slug: str) -> str:
    """Return the tool cluster name for internal linking recommendations."""
    for cluster_name, slugs in TOOL_CLUSTERS.items():
        if slug in slugs:
            return cluster_name

    return "general"


def related_slugs(slug: str) -> list[str]:
    """Return nearby tools that should be cross-linked from this page."""
    cluster_name = cluster_for_slug(slug)
    slugs = TOOL_CLUSTERS.get(cluster_name, [])
    return [item for item in slugs if item != slug][:5]


def build_opportunities(slug: str, url: str, html: str, parser: SimplePageParser) -> list[dict]:
    """Generate SEO/UX/content recommendations for one page."""
    try:
        opportunities: list[dict] = []

        title = parser.title.strip()
        description = parser.meta.get("description", "").strip()
        h1 = " ".join(parser.h1_values).strip()
        visible_text = " ".join(parser.visible_text_parts)
        word_count = len(re.findall(r"\b\w+\b", visible_text))
        is_home = url.rstrip("/") == BASE_URL.rstrip("/")

        if len(description) < 90 and not is_home:
            opportunities.append(
                {
                    "type": "meta_description_depth",
                    "severity": "medium",
                    "recommendation": "Expand the meta description to better explain the exact problem solved and expected output.",
                    "why_it_matters": "Clear descriptions improve search snippet quality and user confidence.",
                }
            )

        if len(title) > 60:
            opportunities.append(
                {
                    "type": "title_length",
                    "severity": "low",
                    "recommendation": "Consider shortening the title while keeping the tool keyword clear.",
                    "why_it_matters": "Shorter titles are easier to scan in browser tabs and search results.",
                }
            )

        if " To " in title or " To " in h1:
            opportunities.append(
                {
                    "type": "title_case_cleanup",
                    "severity": "low",
                    "recommendation": "Use natural title casing such as 'Hourly to Salary Calculator' instead of 'Hourly To Salary Calculator'.",
                    "why_it_matters": "Small copy polish makes the site feel more professionally edited.",
                }
            )

        if word_count < 220 and not is_home:
            opportunities.append(
                {
                    "type": "helpful_copy_depth",
                    "severity": "medium",
                    "recommendation": "Add a short 'How to use this calculator' and 'What the result means' section.",
                    "why_it_matters": "People-first tool pages should leave users with enough context to understand and act on the result.",
                }
            )

        related = related_slugs(slug)
        if related:
            missing_related = [
                item
                for item in related
                if f"../{item}/" not in html and f"/nothingbuta/{item}/" not in html
            ]

            if missing_related:
                opportunities.append(
                    {
                        "type": "internal_link_cluster",
                        "severity": "medium",
                        "recommendation": f"Add a small related-tools section linking to missing related tools: {', '.join(missing_related)}.",
                        "why_it_matters": "Relevant tool-to-tool links help users discover adjacent utilities without sending them to the root hub.",
                    }
                )

        if "application/ld+json" not in html.lower():
            opportunities.append(
                {
                    "type": "structured_data_candidate",
                    "severity": "low",
                    "recommendation": "Consider adding JSON-LD structured data for WebApplication or SoftwareApplication.",
                    "why_it_matters": "Structured data can help search engines understand page type and purpose.",
                }
            )

        if ROOT_DROPDOWN_OPTION in html:
            opportunities.append(
                {
                    "type": "root_link_regression",
                    "severity": "high",
                    "recommendation": "Remove the dropdown option that routes users to the root hub.",
                    "why_it_matters": "Public tool pages should keep visitors inside specific utility pages.",
                }
            )

        if 'id="nothingbuta-tool-jump"' not in html and not is_home:
            opportunities.append(
                {
                    "type": "missing_tool_navigation",
                    "severity": "high",
                    "recommendation": "Restore the public tool-to-tool dropdown navigation.",
                    "why_it_matters": "Navigation helps users discover other tools and prevents isolated dead-end pages.",
                }
            )

        return opportunities

    except Exception as exc:
        logger.exception("Failed building opportunities for %s", url)
        raise RuntimeError(f"Failed building opportunities for {url}") from exc


def priority_score(opportunities: list[dict]) -> int:
    """Convert opportunity severity into a rough priority score."""
    weights = {"high": 5, "medium": 3, "low": 1}
    return sum(weights.get(item.get("severity", "low"), 1) for item in opportunities)


def inspect_url(url: str) -> dict:
    """Fetch and inspect one URL."""
    try:
        status, html = fetch_url(url)

        if status != 200:
            return {
                "url": url,
                "slug": slug_from_url(url),
                "status": "FAIL",
                "http_status": status,
                "title": "",
                "meta_description": "",
                "h1": "",
                "word_count_estimate": 0,
                "opportunities": [
                    {
                        "type": "http_status",
                        "severity": "high",
                        "recommendation": f"Fix live HTTP status {status}.",
                        "why_it_matters": "Pages must be available before SEO or UX optimization matters.",
                    }
                ],
                "priority_score": 5,
            }

        parser = parse_page(html)
        slug = "home" if url.rstrip("/") == BASE_URL.rstrip("/") else slug_from_url(url)
        opportunities = build_opportunities(slug, url, html, parser)
        visible_text = " ".join(parser.visible_text_parts)

        return {
            "url": url,
            "slug": slug,
            "status": "PASS",
            "http_status": status,
            "cluster": cluster_for_slug(slug),
            "title": parser.title.strip(),
            "meta_description": parser.meta.get("description", "").strip(),
            "h1": " ".join(parser.h1_values).strip(),
            "word_count_estimate": len(re.findall(r"\b\w+\b", visible_text)),
            "opportunities": opportunities,
            "priority_score": priority_score(opportunities),
        }

    except Exception as exc:
        logger.exception("Failed inspecting URL: %s", url)
        raise RuntimeError(f"Failed inspecting URL: {url}") from exc


def write_reports(proof: dict) -> None:
    """Write machine-readable and human-readable growth reports."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        JSON_OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA SEO Growth Research Report",
            "",
            f"Generated: {proof['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: {proof['status']}",
            f"- Pages checked: {proof['pages_checked']}",
            f"- Total opportunities: {proof['total_opportunities']}",
            f"- High priority opportunities: {proof['high_priority_opportunities']}",
            "",
            "## Safety Gates",
            "",
        ]

        for key, value in SAFETY_GATES.items():
            lines.append(f"- {key}: `{value}`")

        lines.extend(["", "## Top Priority Pages", ""])

        for page in proof["top_priority_pages"]:
            lines.append(f"### {page['slug']}")
            lines.append("")
            lines.append(f"- URL: {page['url']}")
            lines.append(f"- Priority score: `{page['priority_score']}`")
            lines.append(f"- Cluster: `{page.get('cluster', 'general')}`")
            lines.append(f"- Title: `{page['title']}`")
            lines.append(f"- H1: `{page['h1']}`")
            lines.append(f"- Word count estimate: `{page['word_count_estimate']}`")
            lines.append("- Opportunities:")

            for item in page["opportunities"]:
                lines.append(
                    f"  - `{item['severity']}` / `{item['type']}`: {item['recommendation']}"
                )

            lines.append("")

        lines.extend(["## All Page Scores", ""])

        for page in proof["pages"]:
            lines.append(
                f"- `{page['slug']}` score=`{page['priority_score']}` opportunities=`{len(page['opportunities'])}`"
            )

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    except Exception as exc:
        logger.exception("Failed writing reports")
        raise RuntimeError("Failed writing reports") from exc


def main() -> int:
    """Run the SEO growth research report."""
    try:
        home_status, home_html = fetch_url(BASE_URL)

        if home_status != 200:
            raise RuntimeError(f"Homepage returned HTTP {home_status}")

        urls = [BASE_URL] + discover_tool_urls(home_html)
        pages = [inspect_url(url) for url in urls]

        total_opportunities = sum(len(page["opportunities"]) for page in pages)
        high_priority = sum(
            1
            for page in pages
            for item in page["opportunities"]
            if item.get("severity") == "high"
        )

        top_priority_pages = sorted(
            [page for page in pages if page["priority_score"] > 0],
            key=lambda item: item["priority_score"],
            reverse=True,
        )[:10]

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "PASS",
            "source": "live_site_cache_busted",
            "pages_checked": len(pages),
            "total_opportunities": total_opportunities,
            "high_priority_opportunities": high_priority,
            "safety_gates": SAFETY_GATES,
            "top_priority_pages": top_priority_pages,
            "pages": pages,
        }

        write_reports(proof)

        print("NOTHINGBUTA SEO GROWTH RESEARCH REPORT:", proof["status"])
        print("pages_checked:", proof["pages_checked"])
        print("total_opportunities:", proof["total_opportunities"])
        print("high_priority_opportunities:", proof["high_priority_opportunities"])
        print("json:", JSON_OUT)
        print("markdown:", MD_OUT)

        return 0

    except Exception as exc:
        logger.exception("SEO growth research failed")
        print("NOTHINGBUTA SEO GROWTH RESEARCH REPORT: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
