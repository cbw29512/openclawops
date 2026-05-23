from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

POLICY_JSON = DATA / "nothingbuta_hourly_optimization_policy.json"
POLICY_MD = REPORTS / "nothingbuta-hourly-optimization-policy.md"

now = datetime.now().astimezone().isoformat(timespec="seconds")

policy = {
    "created_at": now,
    "policy_id": "nothingbuta-hourly-optimization-policy",
    "mission": "Continuously improve 24 high-performing SEO-optimized single-purpose app/tool sites.",
    "core_goal": "Each site should do one specific thing easily and well, be useful to real searchers, and grow durable organic traffic over time.",
    "cadence": {
        "minimum_check_frequency": "hourly",
        "applies_to": [
            "local previews",
            "staging candidates",
            "published sites after approval"
        ]
    },
    "hourly_ai_responsibilities": [
        "check each site/page for broken output, missing preview, or checksum drift",
        "review SEO title, meta description, H1, FAQ, internal-link opportunities, and search intent fit",
        "look for UX improvements that make the app easier to use",
        "identify trust issues, weak wording, missing disclaimers, or thin-content risk",
        "research better competitor examples and searcher intent patterns",
        "recommend page improvements as local-only packets",
        "flag weak/stale sites for replacement research instead of forcing low-quality slots",
        "preserve winners and improve borderline pages before replacing them"
    ],
    "traffic_growth_loop": [
        "prepare indexing and sitemap recommendations after publish approval",
        "suggest internal link clusters by topic",
        "suggest long-tail utility examples only when useful, not spam",
        "use future Search Console/performance evidence after approval",
        "feed results back into improvement and replacement decisions"
    ],
    "locked_safety_gates": {
        "commit_allowed": False,
        "push_allowed": False,
        "publish_allowed": False,
        "github_pages_changes_allowed": False,
        "analytics_allowed": False,
        "ads_allowed": False,
        "affiliate_links_allowed": False,
        "lead_capture_allowed": False,
        "outreach_allowed": False,
        "spending_allowed": False,
        "requires_chris_approval_before_external_action": True
    }
}

DATA.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

POLICY_JSON.write_text(json.dumps(policy, indent=2), encoding="utf-8")

lines = [
    "# NothingButA Hourly Optimization Policy",
    "",
    f"Generated: {now}",
    "",
    "## Mission",
    "",
    policy["mission"],
    "",
    "## Core Goal",
    "",
    policy["core_goal"],
    "",
    "## Hourly AI Responsibilities",
    "",
]

for item in policy["hourly_ai_responsibilities"]:
    lines.append(f"- {item}")

lines.extend([
    "",
    "## Traffic Growth Loop",
    "",
])

for item in policy["traffic_growth_loop"]:
    lines.append(f"- {item}")

lines.extend([
    "",
    "## Locked Safety Gates",
    "",
])

for key, value in policy["locked_safety_gates"].items():
    lines.append(f"- {key}: {str(value).lower()}")

POLICY_MD.write_text("\n".join(lines), encoding="utf-8")

print("NOTHINGBUTA HOURLY OPTIMIZATION POLICY: PASS")
print(f"json: {POLICY_JSON}")
print(f"markdown: {POLICY_MD}")