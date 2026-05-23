from __future__ import annotations

import json
import logging
import re
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin


# Objective:
# Monitor the live NothingButA GitHub Pages site for basic SEO,
# accessibility, and public-surface regressions.
#
# This script DOES:
# - fetch the live homepage
# - discover public tool links
# - fetch each live tool page
# - run deterministic static checks
# - write JSON and Markdown reports
#
# This script DOES NOT:
# - claim legal ADA certification
# - change files
# - commit
# - push
# - publish
# - add analytics, ads, affiliate links, lead capture, or outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_live_quality_monitor")


# -----------------------------
# State / Data Schema
# -----------------------------

ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

JSON_OUT = DATA_DIR / "nothingbuta_live_quality_monitor.json"
MD_OUT = REPORTS_DIR / "nothingbuta-live-quality-monitor.md"

BASE_URL = "https://cbw29512.github.io/nothingbuta/"

BAD_PUBLIC_TERMS = [
    "OpenClaw",
    "Nova",
    "factory",
    "staging",
    "internal",
    "candidate",
    "approval",
    "Chris",
]

ROOT_DROPDOWN_OPTION = '<option value="../">All tools home</option>'


class PageParser(HTMLParser):
    """Small HTML parser for static SEO/accessibility checks."""

    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.current_heading = None
        self.title_text = ""
        self.h1_texts: list[str] = []
        self.meta: dict[str, str] = {}
        self.html_lang = ""
        self.links: list[str] = []
        self.images: list[dict] = []
        self.controls: list[dict] = []
        self.labels_for: set[str] = set()
        self.button_text_stack: list[int] = []
        self.button_text: dict[int, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()

        if tag == "html":
            self.html_lang = attrs_dict.get("lang", "")

        if tag == "title":
            self.in_title = True

        if tag == "meta":
            name = attrs_dict.get("name", "").lower()
            if name:
                self.meta[name] = attrs_dict.get("content", "")

        if tag == "h1":
            self.current_heading = "h1"

        if tag == "a":
            href = attrs_dict.get("href", "")
            if href:
                self.links.append(href)

        if tag == "img":
            self.images.append(attrs_dict)

        if tag in {"input", "select", "textarea", "button"}:
            self.controls.append({"tag": tag, "attrs": attrs_dict})

        if tag == "label":
            label_for = attrs_dict.get("for", "")
            if label_for:
                self.labels_for.add(label_for)

        if tag == "button":
            index = len(self.controls) - 1
            self.button_text_stack.append(index)
            self.button_text[index] = ""

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag == "title":
            self.in_title = False

        if tag == "h1":
            self.current_heading = None

        if tag == "button" and self.button_text_stack:
            self.button_text_stack.pop()

    def handle_data(self, data: str) -> None:
        clean = data.strip()

        if self.in_title:
            self.title_text += data

        if self.current_heading == "h1" and clean:
            self.h1_texts.append(clean)

        if self.button_text_stack and clean:
            index = self.button_text_stack[-1]
            self.button_text[index] = (self.button_text.get(index, "") + " " + clean).strip()


def fetch_url(url: str) -> tuple[int, str]:
    """Fetch a URL using only the Python standard library.

    Why cache-bust:
    GitHub Pages/CDN can briefly serve stale HTML after a push.
    The monitor should check the current page, not a cached copy.
    """
    try:
        separator = "&" if "?" in url else "?"
        stamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        request_url = f"{url}{separator}v={stamp}"

        request = urllib.request.Request(
            request_url,
            headers={
                "User-Agent": "NothingButAQualityMonitor/1.0",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            status = int(response.status)
            content = response.read().decode("utf-8", errors="replace")
            return status, content

    except Exception as exc:
        logger.exception("Failed to fetch URL: %s", url)
        raise RuntimeError(f"Failed to fetch URL: {url}") from exc

def parse_html(html: str) -> PageParser:
    """Parse one HTML document into a lightweight state object."""
    try:
        parser = PageParser()
        parser.feed(html)
        return parser

    except Exception as exc:
        logger.exception("Failed to parse HTML")
        raise RuntimeError("Failed to parse HTML") from exc


def discover_tool_urls(home_html: str) -> list[str]:
    """Discover public tool pages from root-page links."""
    try:
        parser = parse_html(home_html)
        urls = []

        for href in parser.links:
            if href.endswith("/") and not href.startswith(("http:", "https:", "#")):
                urls.append(urljoin(BASE_URL, href))

        unique_urls = sorted(set(urls))

        if len(unique_urls) < 25:
            raise RuntimeError(f"Expected at least 25 tool URLs, found {len(unique_urls)}")

        return unique_urls

    except Exception as exc:
        logger.exception("Failed to discover tool URLs")
        raise RuntimeError("Failed to discover tool URLs") from exc


def control_has_accessible_name(control: dict, labels_for: set[str], button_text: str = "") -> bool:
    """Check whether a form control has an accessible name."""
    attrs = control["attrs"]
    tag = control["tag"]

    if tag == "input" and attrs.get("type", "").lower() in {"hidden", "submit"}:
        return True

    if attrs.get("aria-label") or attrs.get("aria-labelledby") or attrs.get("title"):
        return True

    control_id = attrs.get("id", "")
    if control_id and control_id in labels_for:
        return True

    if tag == "button" and button_text.strip():
        return True

    return False


def audit_page(url: str, html: str, is_tool: bool) -> dict:
    """Run deterministic checks against one page."""
    try:
        parser = parse_html(html)
        problems: list[str] = []

        title = parser.title_text.strip()
        description = parser.meta.get("description", "").strip()
        viewport = parser.meta.get("viewport", "").strip()

        if not parser.html_lang:
            problems.append("missing_html_lang")

        if not title:
            problems.append("missing_title")
        elif len(title) > 70:
            problems.append("title_too_long")

        if not description:
            problems.append("missing_meta_description")
        elif len(description) < 40:
            problems.append("meta_description_too_short")
        elif len(description) > 170:
            problems.append("meta_description_too_long")

        if not viewport:
            problems.append("missing_viewport")

        if len(parser.h1_texts) < 1:
            problems.append("missing_h1")

        for term in BAD_PUBLIC_TERMS:
            if re.search(re.escape(term), html, flags=re.IGNORECASE):
                problems.append(f"public_leak_term:{term}")

        if is_tool:
            if 'id="nothingbuta-tool-jump"' not in html:
                problems.append("missing_tool_dropdown")

            if ROOT_DROPDOWN_OPTION in html:
                problems.append("root_dropdown_option_present")

        for image in parser.images:
            if "alt" not in image:
                problems.append("image_missing_alt")

        for index, control in enumerate(parser.controls):
            text = parser.button_text.get(index, "")
            if not control_has_accessible_name(control, parser.labels_for, text):
                problems.append(f"control_missing_accessible_name:{control['tag']}")

        return {
            "url": url,
            "status": "PASS" if not problems else "FAIL",
            "title": title,
            "description_length": len(description),
            "h1_count": len(parser.h1_texts),
            "problems": problems,
        }

    except Exception as exc:
        logger.exception("Failed to audit page: %s", url)
        raise RuntimeError(f"Failed to audit page: {url}") from exc


def write_reports(proof: dict) -> None:
    """Write reports for Nova and Chris to review."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        JSON_OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Live Quality Monitor",
            "",
            f"Generated: {proof['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: {proof['status']}",
            f"- Pages checked: {proof['pages_checked']}",
            f"- Failed pages: {proof['failed_pages']}",
            "",
            "## Page Results",
            "",
        ]

        for result in proof["results"]:
            lines.append(f"### {result['url']}")
            lines.append("")
            lines.append(f"- Status: `{result['status']}`")
            lines.append(f"- Title: `{result['title']}`")
            lines.append(f"- Description length: `{result['description_length']}`")
            lines.append(f"- H1 count: `{result['h1_count']}`")

            if result["problems"]:
                lines.append("- Problems:")
                for problem in result["problems"]:
                    lines.append(f"  - `{problem}`")

            lines.append("")

        MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    except Exception as exc:
        logger.exception("Failed to write live quality reports")
        raise RuntimeError("Failed to write live quality reports") from exc


def main() -> int:
    """Run the live site quality monitor."""
    try:
        homepage_status, homepage_html = fetch_url(BASE_URL)

        if homepage_status != 200:
            raise RuntimeError(f"Homepage returned HTTP {homepage_status}")

        tool_urls = discover_tool_urls(homepage_html)
        results = [audit_page(BASE_URL, homepage_html, is_tool=False)]

        for url in tool_urls:
            status, html = fetch_url(url)

            if status != 200:
                results.append(
                    {
                        "url": url,
                        "status": "FAIL",
                        "title": "",
                        "description_length": 0,
                        "h1_count": 0,
                        "problems": [f"http_status:{status}"],
                    }
                )
                continue

            results.append(audit_page(url, html, is_tool=True))

        failed_pages = sum(1 for item in results if item["status"] != "PASS")

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "PASS" if failed_pages == 0 else "NEEDS_REVIEW",
            "pages_checked": len(results),
            "failed_pages": failed_pages,
            "results": results,
        }

        write_reports(proof)

        print("NOTHINGBUTA LIVE QUALITY MONITOR:", proof["status"])
        print("pages_checked:", proof["pages_checked"])
        print("failed_pages:", proof["failed_pages"])
        print("json:", JSON_OUT)
        print("markdown:", MD_OUT)

        return 0 if proof["status"] == "PASS" else 1

    except Exception as exc:
        logger.exception("Live quality monitor failed")
        print("NOTHINGBUTA LIVE QUALITY MONITOR: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())