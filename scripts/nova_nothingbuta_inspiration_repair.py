from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

POLICY_PATH = DATA_DIR / "nothingbuta_research_policy.json"
SOURCES_PATH = DATA_DIR / "nothingbuta_inspiration_sources.json"
FINDINGS_PATH = DATA_DIR / "nothingbuta_inspiration_findings.json"
RUN_REPORT_PATH = REPORTS_DIR / "nothingbuta-inspiration-research-run.md"


def now_iso() -> str:
    """Return an audit-friendly timestamp."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_json(path: Path, value: dict) -> None:
    """Write clean UTF-8 JSON without depending on PowerShell object behavior."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"Failed writing JSON file {path}: {exc}") from exc


def write_text(path: Path, value: str) -> None:
    """Write clean UTF-8 text."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"Failed writing text file {path}: {exc}") from exc


def build_policy(timestamp: str) -> dict:
    """Define what research may and may not do."""
    return {
        "policy_id": "nothingbuta-inspiration-research-policy",
        "created_at": timestamp,
        "updated_at": timestamp,
        "status": "active",
        "purpose": "Extract inspiration patterns for better utility websites without copying content, code, layout, branding, or user posts.",
        "allowed_research_outputs": [
            "pain_point_summary",
            "user_language_patterns",
            "ux_pattern_summary",
            "seo_structure_pattern",
            "mobile_usability_pattern",
            "trust_signal_pattern",
            "feature_gap",
            "build_guidance",
        ],
        "blocked_outputs": [
            "copied_reddit_comments",
            "copied_forum_posts",
            "copied_competitor_copy",
            "copied_layout",
            "copied_code",
            "copied_branding",
            "stored_personal_user_data",
            "mass_scraped_content",
            "published_research_quotes_without_review",
        ],
        "reddit_rule": {
            "allowed": "Use official/approved API access, compliant search-result observation, or manual review. Store only summarized non-identifying observations.",
            "blocked": "Do not bypass Reddit access controls, scrape as an unknown bot, copy comments into products, or use Reddit data for model training.",
        },
        "forum_rule": {
            "allowed": "Use forums for repeated pain points and common questions.",
            "blocked": "Do not copy posts, usernames, private details, or forum wording into public pages.",
        },
        "competitor_rule": {
            "allowed": "Study UX, information architecture, feature coverage, mobile behavior, trust/disclaimer placement, and SEO structure.",
            "blocked": "Do not copy visual design, code, calculators, proprietary logic, headings, or article text.",
        },
        "publish_allowed": False,
        "external_action_allowed": False,
        "domain_purchase_allowed": False,
        "ads_allowed": False,
        "affiliate_links_allowed": False,
        "lead_capture_allowed": False,
    }


def build_sources(timestamp: str) -> dict:
    """Define safe source groups and research queries."""
    return {
        "source_registry_id": "nothingbuta-inspiration-sources",
        "created_at": timestamp,
        "updated_at": timestamp,
        "active_candidate_id": "nba-util-0001",
        "candidate_name": "Nothing But A Debt Payoff Calculator",
        "research_mode": "pattern_extraction_without_copying",
        "source_groups": [
            {
                "group": "reddit_and_forums",
                "purpose": "Find repeated user pain points, confusing terms, real-world debt payoff questions, and language normal people use.",
                "access_rule": "Use compliant/approved access or manual/search observation only. Store summaries, not copied posts.",
                "queries": [
                    "site:reddit.com debt payoff calculator extra payment confusion",
                    "site:reddit.com personalfinance debt payoff extra payment interest saved",
                    "site:reddit.com debtfree payoff calculator snowball avalanche",
                    "site:reddit.com povertyfinance pay off credit card extra payment",
                    "site:reddit.com creditcards payoff calculator APR monthly payment",
                    "forum debt payoff calculator extra payment interest saved",
                    "forum credit card payoff calculator confusing APR",
                ],
            },
            {
                "group": "competitor_tools",
                "purpose": "Study UX patterns, mobile calculator behavior, result-card design, FAQ placement, examples, and trust/disclaimer language.",
                "access_rule": "Observe patterns only. Do not copy text, layout, code, branding, or proprietary features.",
                "source_examples": [
                    {
                        "name": "Bankrate credit card payoff calculator",
                        "pattern_to_study": [
                            "calculator input sequence",
                            "financial disclaimer style",
                            "result explanation",
                        ],
                    },
                    {
                        "name": "NerdWallet financial calculators",
                        "pattern_to_study": [
                            "calculator hub structure",
                            "supporting educational copy",
                            "trust positioning",
                        ],
                    },
                    {
                        "name": "Calculator.net debt payoff calculator",
                        "pattern_to_study": [
                            "input coverage",
                            "result table possibilities",
                            "simple utility layout",
                        ],
                    },
                    {
                        "name": "Undebt.it payoff tools",
                        "pattern_to_study": [
                            "snowball vs avalanche concepts",
                            "multiple debt workflow",
                            "payoff plan framing",
                        ],
                    },
                ],
            },
            {
                "group": "seo_and_search_intent",
                "purpose": "Find what users expect from this query and what supporting content helps them use the tool.",
                "access_rule": "Use intent summaries and pattern notes only.",
                "queries": [
                    "debt payoff calculator extra payment",
                    "credit card payoff calculator",
                    "debt snowball calculator",
                    "debt avalanche calculator",
                    "how much interest can I save with extra payments",
                    "pay off credit card faster calculator",
                ],
            },
        ],
        "required_pattern_outputs": [
            "top_user_pain_points",
            "mobile_ux_patterns",
            "result_explanation_patterns",
            "faq_candidates",
            "feature_gap_candidates",
            "trust_and_disclaimer_patterns",
            "do_not_copy_notes",
            "next_build_guidance",
        ],
    }


def build_findings(timestamp: str) -> dict:
    """Create safe initial pattern findings without scraping or copying."""
    return {
        "findings_id": "nothingbuta-inspiration-findings-nba-util-0001",
        "created_at": timestamp,
        "updated_at": timestamp,
        "candidate_id": "nba-util-0001",
        "candidate_name": "Nothing But A Debt Payoff Calculator",
        "status": "research_packet_ready",
        "source_review_required": True,
        "top_user_pain_points": [
            "Users may not understand how APR turns into monthly interest.",
            "Users want to know whether extra payments are worth it.",
            "Users want a plain answer, not a spreadsheet.",
            "Users may compare snowball versus avalanche payoff approaches.",
            "Mobile users need the result immediately after changing numbers.",
        ],
        "mobile_ux_patterns": [
            "Use one-column input flow on phones.",
            "Keep input fields thumb-friendly.",
            "Show the result directly below inputs on mobile.",
            "Avoid long educational copy before the calculator.",
            "Use default example values so the tool is useful immediately.",
        ],
        "result_explanation_patterns": [
            "Show payoff time first.",
            "Show interest paid and interest saved separately.",
            "Show months saved as a simple number.",
            "Explain what changes when the extra payment changes.",
            "Use plain-English warnings when payment is too low.",
        ],
        "faq_candidates": [
            "What does interest saved mean?",
            "Does this replace my lender payoff quote?",
            "Should I use debt snowball or debt avalanche?",
            "Why does a small extra payment change the payoff date?",
            "What if my payment is too low?",
        ],
        "feature_gap_candidates": [
            "Add debt snowball versus avalanche comparison.",
            "Add multiple-debt payoff planner.",
            "Add printable payoff summary later.",
            "Add month-by-month payoff table later.",
            "Add extra-payment scenario comparison.",
        ],
        "trust_and_disclaimer_patterns": [
            "Use a short financial estimate disclaimer near the tool.",
            "Avoid promising exact payoff dates.",
            "Explain that lender terms, fees, payment timing, and compounding can change results.",
            "Do not collect sensitive financial details in the first public version.",
        ],
        "do_not_copy_notes": [
            "Do not copy Reddit comments or forum posts.",
            "Do not copy competitor page text.",
            "Do not copy competitor layout or branding.",
            "Do not copy proprietary calculator code.",
            "Use research only to extract general patterns and user needs.",
        ],
        "next_build_guidance": [
            "Keep the calculator as the first interactive element.",
            "Add simple scenario comparison without overwhelming mobile users.",
            "Use FAQ to answer the top confusion points.",
            "Avoid internal workflow language on the public page.",
            "Keep the page visually distinct from future NothingButA tools while preserving the same easy input-result flow.",
        ],
        "publish_allowed": False,
        "external_action_allowed": False,
    }


def write_run_report(timestamp: str, sources: dict, findings: dict) -> None:
    """Write a human-readable report for review."""
    source_groups = "\n".join(f"- {group['group']}" for group in sources["source_groups"])
    pain_points = "\n".join(f"- {item}" for item in findings["top_user_pain_points"])
    mobile_patterns = "\n".join(f"- {item}" for item in findings["mobile_ux_patterns"])

    report = f"""# NothingButA Inspiration Research Run

Generated: {timestamp}

## Status

PASS

## Mode

Safe local research packet.

This run did not scrape Reddit, forums, or competitor sites. It created a structured research queue and initial pattern guidance for Nova/OpenClaw.

## Candidate

{sources["candidate_name"]}

## Research Groups

{source_groups}

## Initial Pain Point Patterns

{pain_points}

## Initial Mobile UX Patterns

{mobile_patterns}

## Safety

- No copied Reddit comments
- No copied forum posts
- No copied competitor text
- No copied layouts
- No copied code
- No publishing
- No external actions
"""
    write_text(RUN_REPORT_PATH, report)


def main() -> None:
    """Run the repair and safe local research packet generation."""
    try:
        timestamp = now_iso()

        policy = build_policy(timestamp)
        sources = build_sources(timestamp)
        findings = build_findings(timestamp)

        write_json(POLICY_PATH, policy)
        write_json(SOURCES_PATH, sources)
        write_json(FINDINGS_PATH, findings)
        write_run_report(timestamp, sources, findings)

        print("NOTHINGBUTA INSPIRATION RESEARCH RUN: PASS")
        print(f"Policy:   {POLICY_PATH}")
        print(f"Sources:  {SOURCES_PATH}")
        print(f"Findings: {FINDINGS_PATH}")
        print(f"Report:   {RUN_REPORT_PATH}")
    except Exception as exc:
        print("NOTHINGBUTA INSPIRATION RESEARCH RUN: FAIL")
        print(str(exc))
        raise


if __name__ == "__main__":
    main()