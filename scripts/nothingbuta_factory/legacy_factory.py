from __future__ import annotations

import hashlib
import html
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = REPORTS_DIR / "nothingbuta-factory-runs"
FACTORY_DIR = ROOT / "nothingbuta" / "factory"
CANDIDATES_DIR = FACTORY_DIR / "candidates"

BACKLOG_PATH = DATA_DIR / "nothingbuta_tool_backlog.json"
REGISTRY_PATH = DATA_DIR / "nothingbuta_candidate_registry.json"
POLICY_PATH = DATA_DIR / "nothingbuta_local_factory_loop_policy.json"
LATEST_REPORT_PATH = REPORTS_DIR / "nothingbuta-latest-factory-loop.md"
LATEST_JSON_PATH = REPORTS_DIR / "nothingbuta-latest-factory-loop.json"
LOCK_PATH = DATA_DIR / "nothingbuta_factory_loop.lock"
LOG_PATH = REPORTS_DIR / "nothingbuta-local-factory-loop.log"

logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

SEED_IDEAS: list[dict[str, Any]] = [
    {"tool_id": "nba-util-0002", "name": "Mortgage Payment Calculator", "slug": "mortgage-payment-calculator", "priority": 95, "category": "finance"},
    {"tool_id": "nba-util-0003", "name": "Tip Calculator", "slug": "tip-calculator", "priority": 88, "category": "everyday"},
    {"tool_id": "nba-util-0004", "name": "Paycheck Take-Home Estimator", "slug": "paycheck-estimator", "priority": 92, "category": "work"},
    {"tool_id": "nba-util-0005", "name": "Car Payment Calculator", "slug": "car-payment-calculator", "priority": 90, "category": "finance"},
    {"tool_id": "nba-util-0006", "name": "Rent Affordability Calculator", "slug": "rent-affordability-calculator", "priority": 87, "category": "finance"},
    {"tool_id": "nba-util-0007", "name": "Savings Goal Calculator", "slug": "savings-goal-calculator", "priority": 84, "category": "finance"},
    {"tool_id": "nba-util-0008", "name": "Unit Price Calculator", "slug": "unit-price-calculator", "priority": 83, "category": "shopping"},
    {"tool_id": "nba-util-0009", "name": "Hourly To Salary Calculator", "slug": "hourly-to-salary-calculator", "priority": 86, "category": "work"},
    {"tool_id": "nba-util-0010", "name": "Loan Early Payoff Calculator", "slug": "loan-early-payoff-calculator", "priority": 89, "category": "finance"},
    {"tool_id": "nba-util-0011", "name": "Simple ROI Calculator", "slug": "roi-calculator", "priority": 80, "category": "business"},
    {"tool_id": "nba-util-0012", "name": "Break-Even Calculator", "slug": "break-even-calculator", "priority": 82, "category": "business"},
    {"tool_id": "nba-util-0013", "name": "Discount Calculator", "slug": "discount-calculator", "priority": 81, "category": "shopping"},
    {"tool_id": "nba-util-0014", "name": "Sales Tax Calculator", "slug": "sales-tax-calculator", "priority": 79, "category": "shopping"},
    {"tool_id": "nba-util-0015", "name": "Percentage Change Calculator", "slug": "percentage-change-calculator", "priority": 78, "category": "math"},
    {"tool_id": "nba-util-0016", "name": "Calories Per Serving Calculator", "slug": "calories-per-serving-calculator", "priority": 76, "category": "food"},
    {"tool_id": "nba-util-0017", "name": "Recipe Scale Calculator", "slug": "recipe-scale-calculator", "priority": 77, "category": "food"},
    {"tool_id": "nba-util-0018", "name": "Paint Coverage Calculator", "slug": "paint-coverage-calculator", "priority": 75, "category": "home"},
    {"tool_id": "nba-util-0019", "name": "Flooring Calculator", "slug": "flooring-calculator", "priority": 74, "category": "home"},
    {"tool_id": "nba-util-0020", "name": "Concrete Calculator", "slug": "concrete-calculator", "priority": 73, "category": "home"},
    {"tool_id": "nba-util-0021", "name": "Days Between Dates Calculator", "slug": "days-between-dates-calculator", "priority": 85, "category": "date"},
    {"tool_id": "nba-util-0022", "name": "Age Calculator", "slug": "age-calculator", "priority": 72, "category": "date"},
    {"tool_id": "nba-util-0023", "name": "Time Card Calculator", "slug": "time-card-calculator", "priority": 91, "category": "work"},
    {"tool_id": "nba-util-0024", "name": "Freelance Rate Calculator", "slug": "freelance-rate-calculator", "priority": 82, "category": "work"},
    {"tool_id": "nba-util-0025", "name": "Emergency Fund Calculator", "slug": "emergency-fund-calculator", "priority": 88, "category": "finance"},
]

from nothingbuta_factory.renderer_catalog_v2 import TOOL_CONFIGS

SUPPORTED_SLUGS = set(TOOL_CONFIGS.keys())


# === RENDERER_EXPANSION_PACK_1 START ===
TOOL_CONFIGS.update(
    {
        "emergency-fund-calculator": {
            "name": "Emergency Fund Calculator",
            "description": "Estimate how much emergency savings you may want based on monthly expenses and target months.",
            "category": "finance",
            "formula": "emergencyfund",
            "inputs": [
                ["expenses", "Monthly essential expenses", "Rent, food, utilities, insurance, and other must-pay costs", "3200"],
                ["months", "Target months covered", "Common targets are 3, 6, or 12 months", "6"],
                ["current", "Current emergency savings", "Amount already saved", "750"],
                ["monthly", "Monthly contribution", "Amount you can add each month", "250"],
            ],
            "faq": [
                ["What does emergency fund target mean?", "It multiplies essential monthly expenses by the number of months you want covered."],
                ["Is this financial advice?", "No. It is an educational estimate only and does not replace professional advice."],
            ],
        },
        "rent-affordability-calculator": {
            "name": "Rent Affordability Calculator",
            "description": "Estimate a rent range from monthly income, target rent percentage, debts, and utilities.",
            "category": "finance",
            "formula": "rent",
            "inputs": [
                ["income", "Monthly take-home income", "Income available after taxes", "4200"],
                ["percent", "Target rent percent", "Common affordability target is around 30 percent", "30"],
                ["debts", "Monthly debt payments", "Car payment, loans, cards, or other required payments", "350"],
                ["utilities", "Estimated utilities", "Power, water, internet, and similar bills", "250"],
            ],
            "faq": [
                ["Does this include utilities?", "Yes, utilities are subtracted so the result is closer to a practical rent estimate."],
                ["Is 30 percent always right?", "No. It is a common starting point, but real affordability depends on your full budget."],
            ],
        },
        "days-between-dates-calculator": {
            "name": "Days Between Dates Calculator",
            "description": "Calculate the number of days between two dates, with an inclusive count option shown.",
            "category": "date",
            "formula": "daysbetween",
            "inputs": [
                ["start", "Start date", "First date", "2026-01-01"],
                ["end", "End date", "Second date", "2026-12-31"],
            ],
            "faq": [
                ["What is inclusive count?", "Inclusive count includes both the start date and the end date."],
                ["Does time of day matter?", "No. This simple tool compares calendar dates only."],
            ],
        },
        "break-even-calculator": {
            "name": "Break-Even Calculator",
            "description": "Estimate how many units you need to sell to cover fixed and variable costs.",
            "category": "business",
            "formula": "breakeven",
            "inputs": [
                ["fixed", "Fixed costs", "Costs that do not change with each sale", "2000"],
                ["price", "Selling price per unit", "Revenue from one unit sold", "50"],
                ["variable", "Variable cost per unit", "Cost to produce or deliver one unit", "20"],
            ],
            "faq": [
                ["What does break-even mean?", "It is the point where estimated revenue covers estimated costs."],
                ["What if variable cost is higher than price?", "The calculator will warn you because each sale loses money before fixed costs are covered."],
            ],
        },
        "freelance-rate-calculator": {
            "name": "Freelance Rate Calculator",
            "description": "Estimate an hourly freelance rate from income goals, billable hours, expenses, and tax buffer.",
            "category": "work",
            "formula": "freelancerate",
            "inputs": [
                ["income", "Desired annual income", "Amount you want to keep before business expenses and tax buffer", "75000"],
                ["expenses", "Annual business expenses", "Software, equipment, insurance, marketing, and similar costs", "8000"],
                ["tax", "Tax buffer %", "Extra percentage to reserve for taxes and overhead uncertainty", "25"],
                ["hours", "Billable hours per week", "Hours you can realistically bill clients", "25"],
                ["weeks", "Working weeks per year", "Use fewer than 52 if you want vacation or unpaid time", "46"],
            ],
            "faq": [
                ["Why use billable hours instead of total hours?", "Freelancers spend time on admin, sales, and unpaid work, so billable hours are the hours that generate revenue."],
                ["Is this tax advice?", "No. It is an educational estimate and does not replace tax or business advice."],
            ],
        },
    }
)

SUPPORTED_SLUGS = set(TOOL_CONFIGS.keys())
# === RENDERER_EXPANSION_PACK_1 END ===


WEAK_TEMPLATE_MARKERS = [
    "quick estimate",
    "starting number",
    "second number",
    "combined value",
    "local preview only",
    "local candidate",
    "needs deeper review",
    "explore a simple local preview",
]

BLOCKED_PUBLIC_MARKERS = [
    "openclawops",
    "big brother",
    "little brother",
    "adsbygoogle",
    "affiliate",
    "document.cookie",
    "localstorage",
    "sessionstorage",
    "mailto:",
    "local preview only",
    "local candidate",
    "quick estimate",
    "combined value",
    "needs deeper review",
]


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path, fallback: Any) -> Any:
    try:
        if not path.exists():
            return fallback
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        logging.exception("Failed to read JSON: %s", path)
        return fallback


def write_json(path: Path, value: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")
    except Exception:
        logging.exception("Failed to write JSON: %s", path)
        raise


def write_text(path: Path, value: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
    except Exception:
        logging.exception("Failed to write text: %s", path)
        raise


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def safe_text(value: Any) -> str:
    return html.escape(str(value), quote=True)


def normalize_input_rows(config: dict[str, Any]) -> list[tuple[str, str, str, str]]:
    """
    Normalize tool input rows so one malformed candidate cannot crash the loop.

    Expected row:
    [field_id, label, help_text, default_value]

    Accepted recovery rows:
    [field_id, label, default_value]
    [field_id, label]
    """
    rows: list[tuple[str, str, str, str]] = []

    for raw_row in config.get("inputs", []):
        try:
            row = list(raw_row)

            if len(row) >= 4:
                field_id, label, help_text, default_value = row[:4]
            elif len(row) == 3:
                field_id, label, default_value = row
                help_text = "Enter a value"
            elif len(row) == 2:
                field_id, label = row
                help_text = "Enter a value"
                default_value = "0"
            else:
                continue

            rows.append((str(field_id), str(label), str(help_text), str(default_value)))
        except Exception:
            logging.exception("Failed to normalize input row for config: %s", config.get("name"))

    if not rows:
        rows.append(("value", "Value", "Enter a value", "0"))

    return rows


def save_policy() -> None:
    policy = {
        "policy_id": "nothingbuta-local-factory-loop-policy",
        "created_or_updated_at": now_iso(),
        "state": "active_strict_quality",
        "purpose": "Continuously build local-only single-purpose utility candidates with strict quality gates.",
        "loop_interval_minutes": 10,
        "batch_size_default": 5,
        "local_candidate_limit": "none",
        "pass_requires": [
            "tool-specific renderer exists",
            "no generic placeholder calculator",
            "mobile-first layout",
            "large touch-friendly inputs",
            "clear result area",
            "labels for every input",
            "FAQ section",
            "no internal workflow language",
            "no external scripts or tracking",
            "no ads, affiliate links, lead capture, cookies, or storage",
            "finance/work tools include estimate disclaimer",
        ],
        "blocked": [
            "git commit",
            "git push",
            "publishing",
            "GitHub Pages settings changes",
            "analytics installation",
            "ads",
            "affiliate links",
            "lead capture",
            "contact forms",
            "unknown-bot scraping",
            "copying Reddit/forum/competitor content",
            "generic placeholder previews marked as passing",
        ],
    }
    write_json(POLICY_PATH, policy)


def default_backlog() -> dict[str, Any]:
    return {
        "backlog_id": "nothingbuta-tool-backlog",
        "created_at": now_iso(),
        "state": "local_factory_backlog_ready",
        "live_tools": [
            {
                "tool_id": "nba-util-0001",
                "name": "Debt Payoff Calculator",
                "slug": "debt-payoff-calculator",
                "state": "live_verified",
                "public_path": "docs/debt-payoff-calculator/index.html",
            }
        ],
        "candidate_tools": [],
        "rules": {
            "local_candidate_generation_limit": "none",
            "live_publication_limit": "approval_gated",
        },
    }


def load_backlog() -> dict[str, Any]:
    backlog = read_json(BACKLOG_PATH, default_backlog())

    if not isinstance(backlog, dict):
        backlog = default_backlog()

    backlog.setdefault("candidate_tools", [])
    backlog.setdefault("live_tools", default_backlog()["live_tools"])
    backlog["state"] = "local_factory_backlog_ready"

    return backlog


def expand_backlog(backlog: dict[str, Any]) -> dict[str, Any]:
    existing_ids = {str(item.get("tool_id")) for item in backlog.get("candidate_tools", [])}
    existing_slugs = {str(item.get("slug")) for item in backlog.get("candidate_tools", [])}
    added = 0

    for seed in SEED_IDEAS:
        if seed["tool_id"] in existing_ids or seed["slug"] in existing_slugs:
            continue

        backlog["candidate_tools"].append(
            {
                **seed,
                "state": "idea",
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "source": "local_seed_backlog",
                "research_status": "research_queue_ready",
                "build_status": "not_started",
                "quality_status": "not_reviewed",
                "publish_allowed": False,
                "push_allowed": False,
                "commit_allowed": False,
                "external_action_allowed": False,
            }
        )
        added += 1

    backlog["updated_at"] = now_iso()
    backlog["seed_ideas_added_last_run"] = added
    return backlog


def html_shell(config: dict[str, Any]) -> str:
    name = safe_text(config["name"])
    description = safe_text(config["description"])
    formula = safe_text(config["formula"])

    input_html = "\n".join(
        f"""
        <label for="{safe_text(field_id)}">{safe_text(label)} <small>{safe_text(help_text)}</small></label>
        <input id="{safe_text(field_id)}" type="number" inputmode="decimal" value="{safe_text(default_value)}" step="0.01">
        """
        for field_id, label, help_text, default_value in normalize_input_rows(config)
    )

    faq_html = "\n".join(
        f"""
        <details>
          <summary>{safe_text(question)}</summary>
          <p>{safe_text(answer)}</p>
        </details>
        """
        for question, answer in config["faq"]
    )

    disclaimer = ""
    if config["category"] in {"finance", "work", "business"}:
        disclaimer = '<p class="fine">Estimate only. This is not financial, tax, payroll, lending, or professional advice.</p>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>NothingButA {name}</title>
  <meta name="description" content="{description}">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    *{{box-sizing:border-box}}
    body{{margin:0;font-family:Arial,sans-serif;background:#f8fafc;color:#0f172a}}
    .wrap{{width:min(100% - 24px,980px);margin:auto;padding:22px 0 52px}}
    .hero{{padding:24px;border-radius:28px;background:linear-gradient(135deg,#111827,#2563eb);color:white;box-shadow:0 18px 55px rgba(15,23,42,.18)}}
    .eyebrow{{display:inline-block;padding:7px 11px;border-radius:999px;background:rgba(255,255,255,.14);font-size:13px;font-weight:900}}
    h1{{font-size:clamp(38px,9vw,64px);line-height:.95;margin:14px 0 10px;letter-spacing:-.06em}}
    .hero p{{color:#dbeafe;font-size:18px;line-height:1.5;margin:0}}
    .grid{{display:grid;grid-template-columns:1fr;gap:14px;margin-top:14px}}
    .card,.result,.note,.faq{{background:white;border:1px solid #dbe3ef;border-radius:24px;padding:18px;box-shadow:0 14px 40px rgba(15,23,42,.08)}}
    label{{display:block;font-weight:900;margin:14px 0 7px}}
    small{{display:block;color:#64748b;font-weight:500;margin-top:3px}}
    input{{width:100%;min-height:54px;border:1px solid #cbd5e1;border-radius:17px;padding:14px 15px;font-size:18px;background:#f8fafc}}
    input:focus{{outline:4px solid rgba(37,99,235,.16);border-color:#2563eb;background:white}}
    button{{width:100%;min-height:54px;border:0;border-radius:17px;background:#2563eb;color:white;font-size:17px;font-weight:900;margin-top:16px}}
    .metric{{padding:14px;border-radius:17px;background:#f1f5f9;margin-top:10px}}
    .metric strong{{display:block;font-size:25px;letter-spacing:-.03em}}
    .metric span{{color:#64748b;font-size:13px}}
    .warn{{background:#fef3c7;color:#78350f;padding:14px;border-radius:17px;margin-top:12px;font-weight:800}}
    .fine{{color:#64748b;font-size:14px;line-height:1.5;margin-top:14px}}
    .faq{{margin-top:14px}}
    details{{border-top:1px solid #e2e8f0;padding:12px 0}}
    details:first-of-type{{border-top:0}}
    summary{{font-weight:900;cursor:pointer}}
    details p{{color:#475569;line-height:1.5}}
    @media (min-width:800px){{.wrap{{padding-top:32px}}.grid{{grid-template-columns:.9fr 1.1fr}}.card,.result,.note,.faq{{padding:22px}}}}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <span class="eyebrow">NothingButA tool candidate</span>
      <h1>{name}</h1>
      <p>{description}</p>
    </section>

    <section class="grid">
      <form class="card" onsubmit="event.preventDefault();calc();">
        <h2>Your numbers</h2>
        {input_html}
        <button type="submit">Calculate result</button>
        {disclaimer}
      </form>

      <section class="result" aria-live="polite">
        <h2>Result</h2>
        <div id="out"></div>
      </section>
    </section>

    <section class="faq">
      <h2>FAQ</h2>
      {faq_html}
    </section>
  </main>

  <script>
    const FORMULA = "{formula}";
    const usd = new Intl.NumberFormat("en-US", {{ style: "currency", currency: "USD" }});
    const num = (id) => Number(document.getElementById(id)?.value) || 0;
    const money = (value) => usd.format(Number.isFinite(value) ? value : 0);
    const block = (value, label) => `<div class="metric"><strong>${{value}}</strong><span>${{label}}</span></div>`;

    function payment(principal, apr, months) {{
      const rate = apr / 100 / 12;
      if (principal <= 0 || months <= 0) return 0;
      if (rate <= 0) return principal / months;
      return principal * (rate * Math.pow(1 + rate, months)) / (Math.pow(1 + rate, months) - 1);
    }}

    function payoff(balance, apr, monthly) {{
      const rate = apr / 100 / 12;
      if (balance <= 0 || monthly <= 0) return {{ ok: false, msg: "Enter a balance and payment above zero." }};
      if (rate > 0 && monthly <= balance * rate) return {{ ok: false, msg: "Payment is too low to reduce the balance." }};
      let months = 0;
      let interest = 0;
      while (balance > 0 && months < 1200) {{
        const charge = balance * rate;
        interest += charge;
        balance = balance + charge - monthly;
        months += 1;
      }}
      return months >= 1200 ? {{ ok: false, msg: "Try a higher payment." }} : {{ ok: true, months, interest }};
    }}

    function monthsText(months) {{
      const years = Math.floor(months / 12);
      const rem = months % 12;
      return years ? `${{years}} yr ${{rem}} mo` : `${{rem}} mo`;
    }}

    function calc() {{
      try {{
        let html = "";

        if (FORMULA === "mortgage") {{
          const principal = Math.max(num("price") - num("down"), 0);
          const pi = payment(principal, num("rate"), num("years") * 12);
          const total = pi + num("escrow");
          html = block(money(total), "Estimated monthly payment") + block(money(pi), "Principal and interest") + block(money(num("escrow")), "Taxes and insurance estimate") + block(money(principal), "Estimated loan amount");
        }}

        if (FORMULA === "paycheck") {{
          const gross = num("gross");
          const federal = gross * num("federal") / 100;
          const state = gross * num("state") / 100;
          const deductions = num("deduct");
          const takehome = Math.max(gross - federal - state - deductions, 0);
          html = block(money(takehome), "Estimated take-home pay") + block(money(federal + state + deductions), "Estimated deductions") + block(money(federal), "Federal estimate") + block(money(state), "State/local estimate");
        }}

        if (FORMULA === "timecard") {{
          const regularPay = num("rate") * num("regular");
          const overtimePay = num("rate") * num("multiplier") * num("overtime");
          const gross = regularPay + overtimePay;
          html = block(money(gross), "Estimated gross pay") + block(money(regularPay), "Regular pay") + block(money(overtimePay), "Overtime pay") + block(money(gross * 52), "Estimated annual gross pay");
        }}

        if (FORMULA === "car") {{
          const principal = Math.max(num("price") - num("down"), 0);
          const monthly = payment(principal, num("rate"), num("months"));
          html = block(money(monthly), "Estimated monthly payment") + block(money(monthly * num("months")), "Estimated total paid") + block(money(Math.max(monthly * num("months") - principal, 0)), "Estimated interest") + block(money(principal), "Estimated loan amount");
        }}

        if (FORMULA === "earlyloan") {{
          const base = payoff(num("balance"), num("rate"), num("payment"));
          const extra = payoff(num("balance"), num("rate"), num("payment") + num("extra"));
          if (!base.ok || !extra.ok) {{
            html = `<div class="warn">${{base.msg || extra.msg}}</div>`;
          }} else {{
            html = block(monthsText(extra.months), "Payoff time with extra payment") + block(money(extra.interest), "Interest paid") + block(money(Math.max(base.interest - extra.interest, 0)), "Interest saved") + block(String(Math.max(base.months - extra.months, 0)), "Months saved");
          }}
        }}

        if (FORMULA === "tip") {{
          const bill = num("bill");
          const tip = bill * num("tip") / 100;
          const total = bill + tip;
          const each = total / Math.max(num("people"), 1);
          html = block(money(tip), "Tip amount") + block(money(total), "Total bill") + block(money(each), "Each person pays");
        }}

        if (FORMULA === "hourlysalary") {{
          const weekly = num("rate") * num("hours");
          const yearly = weekly * num("weeks");
          html = block(money(weekly), "Estimated weekly gross pay") + block(money(yearly / 12), "Estimated monthly gross pay") + block(money(yearly), "Estimated yearly gross pay");
        }}

        if (FORMULA === "savingsgoal") {{
          const remaining = Math.max(num("goal") - num("current"), 0);
          const months = num("monthly") > 0 ? Math.ceil(remaining / num("monthly")) : 0;
          html = block(money(remaining), "Amount left to save") + block(String(months), "Months to goal") + block(money(num("monthly") * months), "Planned future savings");
        }}

        if (FORMULA === "unitprice") {{
          const first = num("units") > 0 ? num("price") / num("units") : 0;
          const second = num("compareunits") > 0 ? num("compare") / num("compareunits") : 0;
          const winner = first && second ? (first < second ? "First package is cheaper per unit" : "Second package is cheaper per unit") : "Enter both packages to compare";
          html = block(money(first), "First unit price") + block(money(second), "Second unit price") + block(winner, "Best value");
        }}

        if (FORMULA === "discount") {{
          const savings = num("price") * num("discount") / 100;
          html = block(money(Math.max(num("price") - savings, 0)), "Sale price") + block(money(savings), "Amount saved");
        }}

        if (FORMULA === "salestax") {{
          const tax = num("price") * num("tax") / 100;
          html = block(money(tax), "Estimated sales tax") + block(money(num("price") + tax), "Estimated total");
        }}

        if (FORMULA === "percentchange") {{
          const oldValue = num("old");
          const newValue = num("new");
          const change = newValue - oldValue;
          const percent = oldValue !== 0 ? (change / oldValue) * 100 : 0;
          html = block(change.toLocaleString(), "Numeric change") + block(`${{percent.toFixed(2)}}%`, "Percentage change");
        }}


        // === RENDERER_EXPANSION_PACK_1_FORMULAS START ===
        if (FORMULA === "emergencyfund") {{
          const target = num("expenses") * num("months");
          const remaining = Math.max(target - num("current"), 0);
          const monthsNeeded = num("monthly") > 0 ? Math.ceil(remaining / num("monthly")) : 0;
          html = block(money(target), "Emergency fund target") + block(money(remaining), "Amount left to save") + block(String(monthsNeeded), "Months to target") + block(money(num("current")), "Current savings");
        }}

        if (FORMULA === "rent") {{
          const targetRent = num("income") * num("percent") / 100;
          const practicalRent = Math.max(targetRent - num("debts") - num("utilities"), 0);
          html = block(money(practicalRent), "Estimated practical rent ceiling") + block(money(targetRent), "Income-based rent target") + block(money(num("debts") + num("utilities")), "Debts and utilities considered") + block(`${{num("percent").toFixed(1)}}%`, "Target rent percentage");
        }}

        if (FORMULA === "breakeven") {{
          const contribution = num("price") - num("variable");
          if (contribution <= 0) {{
            html = '<div class="warn">Selling price must be higher than variable cost per unit.</div>';
          }} else {{
            const units = Math.ceil(num("fixed") / contribution);
            const revenue = units * num("price");
            html = block(units.toLocaleString(), "Units to break even") + block(money(revenue), "Revenue at break-even") + block(money(contribution), "Contribution per unit") + block(money(num("fixed")), "Fixed costs");
          }}
        }}

        if (FORMULA === "freelancerate") {{
          const billableHours = Math.max(num("hours") * num("weeks"), 1);
          const subtotal = num("income") + num("expenses");
          const taxBuffer = subtotal * num("tax") / 100;
          const neededRevenue = subtotal + taxBuffer;
          const rate = neededRevenue / billableHours;
          html = block(money(rate), "Estimated hourly rate") + block(money(neededRevenue), "Revenue target") + block(billableHours.toLocaleString(), "Annual billable hours") + block(money(taxBuffer), "Tax and buffer amount");
        }}
        // === RENDERER_EXPANSION_PACK_1_FORMULAS END ===


        // === RENDERER_EXPANSION_PACK_2_FORMULAS START ===
        if (FORMULA === "roi") {{
          const cost = num("cost");
          const returned = num("return");
          if (cost <= 0) {{
            html = '<div class="warn">Enter a cost above zero.</div>';
          }} else {{
            const net = returned - cost;
            const roi = (net / cost) * 100;
            html = block(money(net), "Estimated net return") + block(`${{roi.toFixed(2)}}%`, "Estimated ROI") + block(money(returned), "Return value") + block(money(cost), "Initial cost");
          }}
        }}

        if (FORMULA === "recipescale") {{
          const original = num("original");
          const desired = num("desired");
          const quantity = num("quantity");
          if (original <= 0 || desired <= 0) {{
            html = '<div class="warn">Enter original and desired servings above zero.</div>';
          }} else {{
            const factor = desired / original;
            const scaled = quantity * factor;
            html = block(scaled.toLocaleString(undefined, {{ maximumFractionDigits: 3 }}), "Scaled ingredient quantity") + block(`${{factor.toFixed(2)}}x`, "Scale factor") + block(original.toLocaleString(), "Original servings") + block(desired.toLocaleString(), "Desired servings");
          }}
        }}

        if (FORMULA === "paintcoverage") {{
          const wallArea = Math.max(num("width") * num("height"), 0);
          const subtractArea = (num("doors") * 21) + (num("windows") * 15);
          const paintableArea = Math.max(wallArea - subtractArea, 0);
          const totalCoverage = paintableArea * Math.max(num("coats"), 1);
          const gallons = num("coverage") > 0 ? totalCoverage / num("coverage") : 0;
          html = block(`${{paintableArea.toLocaleString()}} sq ft`, "Estimated paintable area") + block(`${{totalCoverage.toLocaleString()}} sq ft`, "Area after coats") + block(gallons.toFixed(2), "Estimated gallons") + block(Math.ceil(gallons).toLocaleString(), "Whole gallons to consider");
        }}

        if (FORMULA === "flooring") {{
          const area = Math.max(num("length") * num("width"), 0);
          const withWaste = area * (1 + Math.max(num("waste"), 0) / 100);
          const boxes = num("box") > 0 ? Math.ceil(withWaste / num("box")) : 0;
          html = block(`${{area.toLocaleString()}} sq ft`, "Room area") + block(`${{withWaste.toFixed(2)}} sq ft`, "Area with waste allowance") + block(boxes.toLocaleString(), "Estimated boxes") + block(`${{num("waste").toFixed(1)}}%`, "Waste allowance");
        }}

        if (FORMULA === "concrete") {{
          const cubicFeet = Math.max(num("length") * num("width") * (num("depth") / 12), 0);
          const withWaste = cubicFeet * (1 + Math.max(num("waste"), 0) / 100);
          const cubicYards = withWaste / 27;
          const bags = num("yield") > 0 ? Math.ceil(withWaste / num("yield")) : 0;
          html = block(`${{withWaste.toFixed(2)}} cu ft`, "Estimated concrete volume") + block(`${{cubicYards.toFixed(3)}} cu yd`, "Estimated cubic yards") + block(bags.toLocaleString(), "Estimated bags") + block(`${{num("depth").toFixed(1)}} in`, "Slab depth");
        }}
        // === RENDERER_EXPANSION_PACK_2_FORMULAS END ===


        // === RENDERER_EXPANSION_PACK_3_FORMULAS START ===
        if (FORMULA === "conversionrate") {{
          const visitors = num("visitors");
          const conversions = num("conversions");
          if (visitors <= 0) {{
            html = '<div class="warn">Enter visitors above zero.</div>';
          }} else {{
            const rate = (conversions / visitors) * 100;
            html = block(`${{rate.toFixed(2)}}%`, "Conversion rate") + block(conversions.toLocaleString(), "Conversions") + block(visitors.toLocaleString(), "Visitors") + block((visitors - conversions).toLocaleString(), "Non-converting visitors");
          }}
        }}

        if (FORMULA === "churnrate") {{
          const starting = num("starting");
          const lost = num("lost");
          if (starting <= 0) {{
            html = '<div class="warn">Enter starting customers above zero.</div>';
          }} else {{
            const churn = (lost / starting) * 100;
            const retained = Math.max(starting - lost, 0);
            const retention = (retained / starting) * 100;
            html = block(`${{churn.toFixed(2)}}%`, "Churn rate") + block(`${{retention.toFixed(2)}}%`, "Retention rate") + block(lost.toLocaleString(), "Customers lost") + block(retained.toLocaleString(), "Customers retained");
          }}
        }}
        // === RENDERER_EXPANSION_PACK_3_FORMULAS END ===

        document.getElementById("out").innerHTML = html || '<div class="warn">This tool needs a stricter formula before it can pass.</div>';
      }} catch (err) {{
        console.error(err);
        document.getElementById("out").innerHTML = '<div class="warn">Check the numbers and try again.</div>';
      }}
    }}

    document.querySelectorAll("input").forEach((input) => input.addEventListener("input", calc));
    calc();
  </script>
</body>
</html>
"""



def days_between_html(config: dict[str, Any]) -> str:
    """Delegate Days Between Dates rendering to renderer_specials_v2."""
    from nothingbuta_factory.renderer_specials_v2 import days_between_html_v2

    return days_between_html_v2(config=config, safe_text=safe_text)


def audit_html(html_value: str, candidate: dict[str, Any], config: dict[str, Any] | None) -> list[str]:
    """Delegate strict HTML auditing to audit_rules_v2."""
    from nothingbuta_factory.audit_rules_v2 import audit_html_v2

    return audit_html_v2(
        html_value=html_value,
        candidate=candidate,
        config=config,
        blocked_public_markers=BLOCKED_PUBLIC_MARKERS,
        weak_template_markers=WEAK_TEMPLATE_MARKERS,
    )


def strict_score(problems: list[str]) -> int:
    """Delegate strict scoring to audit_rules_v2."""
    from nothingbuta_factory.audit_rules_v2 import strict_score_v2

    return strict_score_v2(problems)


def load_registry() -> dict[str, Any]:
    registry = read_json(
        REGISTRY_PATH,
        {
            "registry_id": "nothingbuta-candidate-registry",
            "created_at": now_iso(),
            "generated_candidates": [],
        },
    )

    if not isinstance(registry, dict):
        registry = {
            "registry_id": "nothingbuta-candidate-registry",
            "created_at": now_iso(),
            "generated_candidates": [],
        }

    registry.setdefault("generated_candidates", [])
    return registry


def save_registry(registry: dict[str, Any]) -> None:
    registry["updated_at"] = now_iso()
    write_json(REGISTRY_PATH, registry)


def regrade_existing_candidates(backlog: dict[str, Any]) -> int:
    marked = 0

    for candidate in backlog.get("candidate_tools", []):
        preview_path = candidate.get("local_preview_path")
        slug = str(candidate.get("slug", ""))

        if not preview_path:
            continue

        path = Path(str(preview_path))

        if not path.exists():
            continue

        content = path.read_text(encoding="utf-8-sig", errors="replace").lower()
        has_weak_marker = any(marker in content for marker in WEAK_TEMPLATE_MARKERS)
        unsupported = slug not in SUPPORTED_SLUGS

        if has_weak_marker:
            candidate["state"] = "regeneration_required"
            candidate["quality_status"] = "weak_generic_preview_rejected"
            candidate["strict_quality_reason"] = "Existing preview used a generic placeholder template."
            candidate["updated_at"] = now_iso()
            marked += 1
        elif unsupported:
            candidate["state"] = "template_required"
            candidate["quality_status"] = "strict_template_required"
            candidate["strict_quality_reason"] = "No strict renderer exists yet for this slug."
            candidate["updated_at"] = now_iso()
            marked += 1

    return marked


def select_candidates(backlog: dict[str, Any], batch_size: int) -> list[dict[str, Any]]:
    candidates = [
        item for item in backlog.get("candidate_tools", [])
        if item.get("state") in {"idea", "research_ready", "local_build_ready", "regeneration_required"}
    ]

    candidates.sort(key=lambda item: int(item.get("priority", 0)), reverse=True)
    return candidates[:batch_size]


def update_candidate(backlog: dict[str, Any], tool_id: str, updates: dict[str, Any]) -> None:
    for item in backlog.get("candidate_tools", []):
        if item.get("tool_id") == tool_id:
            item.update(updates)
            item["updated_at"] = now_iso()
            return


def build_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    slug = str(candidate["slug"])
    config = TOOL_CONFIGS.get(slug)

    if config is None:
        return {
            "tool_id": candidate["tool_id"],
            "name": candidate["name"],
            "slug": slug,
            "state": "template_required",
            "local_preview_path": None,
            "audit_status": "BLOCKED",
            "strict_quality_score": 0,
            "audit_problems": ["no strict renderer exists for this slug"],
            "publish_allowed": False,
            "push_allowed": False,
            "commit_allowed": False,
            "external_action_allowed": False,
        }

    html_value = days_between_html(config) if slug == "days-between-dates-calculator" else html_shell(config)
    problems = audit_html(html_value, candidate, config)
    score = strict_score(problems)
    passed = not problems and score == 100

    output_dir = CANDIDATES_DIR / slug
    output_path = output_dir / "index.html"
    output_dir.mkdir(parents=True, exist_ok=True)

    write_text(output_path, html_value)

    return {
        "tool_id": candidate["tool_id"],
        "name": config["name"],
        "slug": slug,
        "state": "local_preview_ready" if passed else "quality_failed",
        "local_preview_path": str(output_path),
        "audit_status": "PASS" if passed else "FAIL",
        "strict_quality_score": score,
        "html_sha256": sha256_text(html_value),
        "audit_problems": problems,
        "publish_allowed": False,
        "push_allowed": False,
        "commit_allowed": False,
        "external_action_allowed": False,
    }


def write_run_reports(run: dict[str, Any]) -> None:
    """Delegate report writing to the extracted reports_v2 module."""
    from nothingbuta_factory.reports_v2 import write_run_reports_v2

    return write_run_reports_v2(
        run=run,
        runs_dir=RUNS_DIR,
        latest_json_path=LATEST_JSON_PATH,
        latest_report_path=LATEST_REPORT_PATH,
        write_json=write_json,
        write_text=write_text,
    )


def run_factory_loop() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)

    if LOCK_PATH.exists():
        lock_age_seconds = max(0, datetime.now().timestamp() - LOCK_PATH.stat().st_mtime)
        if lock_age_seconds < 600:
            return {
                "run_id": f"factory-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "created_at": now_iso(),
                "status": "skipped_locked",
                "reason": "Another factory loop appears to be running.",
            }

    LOCK_PATH.write_text(now_iso(), encoding="utf-8")

    try:
        save_policy()

        batch_size = int(os.environ.get("NOTHINGBUTA_FACTORY_BATCH", "5"))

        backlog = load_backlog()
        backlog = expand_backlog(backlog)
        weak_marked = regrade_existing_candidates(backlog)

        selected = select_candidates(backlog, batch_size)
        registry = load_registry()

        built: list[dict[str, Any]] = []

        for candidate in selected:
            try:
                result = build_candidate(candidate)
            except Exception as candidate_exc:
                logging.exception("Candidate build failed: %s", candidate.get("slug"))
                result = {
                    "tool_id": candidate.get("tool_id", "unknown"),
                    "name": candidate.get("name", "Unknown Candidate"),
                    "slug": candidate.get("slug", "unknown"),
                    "state": "quality_failed",
                    "local_preview_path": candidate.get("local_preview_path"),
                    "audit_status": "FAIL",
                    "strict_quality_score": 0,
                    "audit_problems": [f"candidate build exception: {candidate_exc}"],
                    "publish_allowed": False,
                    "push_allowed": False,
                    "commit_allowed": False,
                    "external_action_allowed": False,
                }

            built.append(result)

            update_candidate(
                backlog,
                str(candidate["tool_id"]),
                {
                    "state": result["state"],
                    "build_status": "strict_local_preview_created" if result.get("local_preview_path") else "strict_template_required",
                    "quality_status": result["audit_status"],
                    "strict_quality_score": result.get("strict_quality_score", 0),
                    "local_preview_path": result.get("local_preview_path"),
                    "html_sha256": result.get("html_sha256"),
                    "audit_problems": result["audit_problems"],
                    "publish_allowed": False,
                    "push_allowed": False,
                    "commit_allowed": False,
                    "external_action_allowed": False,
                },
            )

        existing_registry_ids = {str(item.get("tool_id")) for item in registry.get("generated_candidates", [])}

        for result in built:
            payload = {**result, "updated_at": now_iso()}

            if result["tool_id"] not in existing_registry_ids:
                payload["created_at"] = now_iso()
                registry["generated_candidates"].append(payload)
            else:
                for item in registry["generated_candidates"]:
                    if item.get("tool_id") == result["tool_id"]:
                        item.update(payload)

        backlog["updated_at"] = now_iso()
        write_json(BACKLOG_PATH, backlog)
        save_registry(registry)

        run = {
            "run_id": f"factory-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "created_at": now_iso(),
            "status": "pass",
            "batch_size": batch_size,
            "backlog_candidate_count": len(backlog.get("candidate_tools", [])),
            "weak_existing_marked": weak_marked,
            "built_candidates": built,
            "commit_allowed": False,
            "push_allowed": False,
            "publish_allowed": False,
            "external_action_allowed": False,
            "github_pages_settings_change_allowed": False,
        }

        write_run_reports(run)
        logging.info("Strict factory loop pass: built=%s backlog=%s weak_marked=%s", len(built), len(backlog.get("candidate_tools", [])), weak_marked)
        return run

    except Exception as exc:
        logging.exception("Strict factory loop failed.")

        run = {
            "run_id": f"factory-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "created_at": now_iso(),
            "status": "fail",
            "batch_size": locals().get("batch_size", 0),
            "backlog_candidate_count": len(backlog.get("candidate_tools", [])) if isinstance(locals().get("backlog"), dict) else 0,
            "weak_existing_marked": locals().get("weak_marked", 0),
            "built_candidates": locals().get("built", []),
            "error": str(exc),
            "commit_allowed": False,
            "push_allowed": False,
            "publish_allowed": False,
            "external_action_allowed": False,
        }

        write_run_reports(run)
        raise

    finally:
        try:
            if LOCK_PATH.exists():
                LOCK_PATH.unlink()
        except Exception:
            logging.exception("Failed to remove lock file.")


def main() -> None:
    run = run_factory_loop()

    print("NOTHINGBUTA STRICT LOCAL FACTORY LOOP:", str(run.get("status", "")).upper())
    print("Run:", run.get("run_id"))
    print("Built:", len(run.get("built_candidates", [])))
    print("Weak existing marked:", run.get("weak_existing_marked", 0))
    print("Backlog:", run.get("backlog_candidate_count", "n/a"))
    print("Latest report:", LATEST_REPORT_PATH)


if __name__ == "__main__":
    main()
