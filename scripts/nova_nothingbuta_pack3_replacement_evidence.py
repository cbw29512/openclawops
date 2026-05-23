from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


# State schema:
# ROOT: local OpenClawOps project root.
# JSON_OUT: machine-readable evidence packet for replacing two weak NothingButA slots.
# MD_OUT: human-readable report for review.
# No files are published, staged, committed, pushed, or externally changed.

ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

JSON_OUT = DATA / "nothingbuta_pack3_replacement_evidence.json"
MD_OUT = REPORTS / "nothingbuta-pack3-replacement-evidence.md"

now = datetime.now().astimezone().isoformat(timespec="seconds")

payload = {
    "generated_at": now,
    "purpose": "Replace weak NothingButA slots with evidence-backed single-purpose app/tool candidates.",
    "replaces": [
        {
            "old_name": "Calories Per Serving Calculator",
            "old_slug": "calories-per-serving-calculator",
            "reason": "Health/nutrition trust risk unless scoped very narrowly; weaker fit for immediate 24-site batch."
        },
        {
            "old_name": "Age Calculator",
            "old_slug": "age-calculator",
            "reason": "Likely broad search demand but weak monetization and low strategic value."
        }
    ],
    "new_candidates": [
        {
            "name": "Conversion Rate Calculator",
            "slug": "conversion-rate-calculator",
            "category": "business",
            "formula": "conversionrate",
            "decision": "build_candidate",
            "evidence_level": "high",
            "score": 88,
            "search_intent": [
                "conversion rate calculator",
                "website conversion rate calculator",
                "marketing conversion rate calculator",
                "sales conversion rate calculator"
            ],
            "inputs": [
                ["visitors", "Visitors", "Total visitors, clicks, leads, or opportunities", "1000"],
                ["conversions", "Conversions", "Number of purchases, signups, leads, or completed actions", "50"]
            ],
            "formula_description": "conversion rate = conversions / visitors * 100",
            "competitor_sources": [
                {
                    "name": "SE Ranking Conversion Rate Calculator",
                    "url": "https://seranking.com/free-tools/conversion-rate-calculator.html"
                },
                {
                    "name": "WebFX Conversion Rate Calculator",
                    "url": "https://www.webfx.com/tools/conversion-rate-calculator/"
                },
                {
                    "name": "Ignite Digital Conversion Rate Calculator",
                    "url": "https://ignitedigital.com/resources/tools/crf/"
                }
            ],
            "monetization_path": "Future B2B SEO/marketing affiliate, lead magnet, newsletter, or ads after traffic approval.",
            "trust_risk": "low_medium",
            "notes": "Keep advice generic. Do not promise revenue growth."
        },
        {
            "name": "Churn Rate Calculator",
            "slug": "churn-rate-calculator",
            "category": "business",
            "formula": "churnrate",
            "decision": "build_candidate",
            "evidence_level": "high",
            "score": 86,
            "search_intent": [
                "churn rate calculator",
                "customer churn calculator",
                "SaaS churn rate calculator",
                "retention rate calculator"
            ],
            "inputs": [
                ["starting", "Customers at start", "Customers at the beginning of the period", "1000"],
                ["lost", "Customers lost", "Customers who cancelled or were lost during the period", "40"]
            ],
            "formula_description": "churn rate = customers lost / customers at start * 100",
            "competitor_sources": [
                {
                    "name": "Yotpo Churn Rate Calculator",
                    "url": "https://www.yotpo.com/tools/churn-rate-calculator/"
                },
                {
                    "name": "Amplitude Churn Rate Calculator",
                    "url": "https://amplitude.com/calculate/churn-rate"
                },
                {
                    "name": "Affonso SaaS Churn Calculator",
                    "url": "https://affonso.io/resources/saas-churn-calculator"
                }
            ],
            "monetization_path": "Future SaaS/business affiliate, founder tools cluster, newsletter, or ads after traffic approval.",
            "trust_risk": "low_medium",
            "notes": "Keep benchmark claims out unless sourced. Tool should calculate only."
        }
    ],
    "safety": {
        "commit_allowed": False,
        "push_allowed": False,
        "publish_allowed": False,
        "github_pages_changes_allowed": False,
        "analytics_allowed": False,
        "ads_allowed": False,
        "affiliate_links_allowed": False,
        "lead_capture_allowed": False,
        "outreach_allowed": False,
        "requires_chris_approval_before_external_action": True
    }
}

DATA.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

lines = [
    "# NothingButA Pack 3 Replacement Evidence",
    "",
    f"Generated: {now}",
    "",
    "## Decision",
    "",
    "Replace the two weak/blocked slots with stronger B2B utility candidates.",
    "",
    "## Replaced Slots",
    "",
]

for item in payload["replaces"]:
    lines.extend([
        f"### {item['old_name']}",
        "",
        f"- Slug: `{item['old_slug']}`",
        f"- Reason: {item['reason']}",
        "",
    ])

lines.extend(["## New Candidates", ""])

for item in payload["new_candidates"]:
    lines.extend([
        f"### {item['name']}",
        "",
        f"- Slug: `{item['slug']}`",
        f"- Decision: `{item['decision']}`",
        f"- Evidence level: `{item['evidence_level']}`",
        f"- Score: `{item['score']}`",
        f"- Category: `{item['category']}`",
        f"- Formula: `{item['formula_description']}`",
        f"- Trust risk: `{item['trust_risk']}`",
        f"- Monetization path: {item['monetization_path']}",
        f"- Notes: {item['notes']}",
        "- Search intent:",
    ])

    for query in item["search_intent"]:
        lines.append(f"  - {query}")

    lines.append("- Competitor/evidence sources:")
    for source in item["competitor_sources"]:
        lines.append(f"  - {source['name']}: {source['url']}")

    lines.append("")

lines.extend([
    "## Safety",
    "",
    "- Commit allowed: false",
    "- Push allowed: false",
    "- Publish allowed: false",
    "- GitHub Pages changes allowed: false",
    "- Analytics allowed: false",
    "- Ads allowed: false",
    "- Affiliate links allowed: false",
    "- Lead capture allowed: false",
    "- Outreach allowed: false",
    "- External action requires Chris approval: true",
    "",
])

MD_OUT.write_text("\n".join(lines), encoding="utf-8")

print("NOTHINGBUTA PACK 3 REPLACEMENT EVIDENCE: PASS")
print(f"json: {JSON_OUT}")
print(f"markdown: {MD_OUT}")