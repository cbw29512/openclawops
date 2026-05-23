from __future__ import annotations

import html
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("nova.nothingbuta_factory_review")


def project_root() -> Path:
    """Resolve the OpenClawOps project root from dashboard/app."""
    return Path(__file__).resolve().parents[2]


def now_iso() -> str:
    """Return an audit-friendly timestamp."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path, fallback: Any) -> Any:
    """Read JSON safely with UTF-8 BOM tolerance."""
    try:
        if not path.exists():
            return fallback
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        logger.exception("Failed to read JSON: %s", path)
        return fallback


def write_json(path: Path, value: Any) -> None:
    """Write clean UTF-8 JSON."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")
    except Exception:
        logger.exception("Failed to write JSON: %s", path)
        raise


def write_text(path: Path, value: str) -> None:
    """Write clean UTF-8 text."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
    except Exception:
        logger.exception("Failed to write text: %s", path)
        raise


def safe(value: Any) -> str:
    """Escape text before rendering HTML."""
    return html.escape(str(value or ""), quote=True)


def clean_slug(value: str) -> str:
    """Allow only safe local preview slugs."""
    return re.sub(r"[^a-z0-9-]", "", str(value).lower())


def paths() -> dict[str, Path]:
    """Centralized file paths for the review layer."""
    root = project_root()

    return {
        "root": root,
        "backlog": root / "data" / "nothingbuta_tool_backlog.json",
        "registry": root / "data" / "nothingbuta_candidate_registry.json",
        "latest_factory": root / "reports" / "nothingbuta-latest-factory-loop.json",
        "pipeline": root / "data" / "nothingbuta_review_pipeline.json",
        "report": root / "reports" / "nothingbuta-review-queue.md",
        "candidates": root / "nothingbuta" / "factory" / "candidates",
    }


def load_backlog() -> dict[str, Any]:
    """Load the local tool backlog."""
    p = paths()["backlog"]
    data = read_json(p, {"candidate_tools": [], "live_tools": []})
    if not isinstance(data, dict):
        return {"candidate_tools": [], "live_tools": []}
    data.setdefault("candidate_tools", [])
    data.setdefault("live_tools", [])
    return data


def save_backlog(backlog: dict[str, Any]) -> None:
    """Save the local tool backlog."""
    backlog["updated_at"] = now_iso()
    write_json(paths()["backlog"], backlog)


def load_registry() -> dict[str, Any]:
    """Load generated candidate registry."""
    data = read_json(paths()["registry"], {"generated_candidates": []})
    if not isinstance(data, dict):
        return {"generated_candidates": []}
    data.setdefault("generated_candidates", [])
    return data


def candidate_preview_url(slug: str) -> str:
    """Return local dashboard preview route for a candidate."""
    return f"/nothingbuta/factory-preview/{clean_slug(slug)}/"


def has_preview(slug: str) -> bool:
    """Check whether local preview HTML exists."""
    preview_path = paths()["candidates"] / clean_slug(slug) / "index.html"
    return preview_path.exists()


def normalize_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Return normalized candidate fields for queue rendering."""
    slug = clean_slug(str(candidate.get("slug", "")))
    score = int(candidate.get("strict_quality_score") or 0)
    state = str(candidate.get("state") or "")
    audit_status = str(candidate.get("quality_status") or candidate.get("audit_status") or "")

    return {
        "tool_id": str(candidate.get("tool_id") or ""),
        "name": str(candidate.get("name") or "Unnamed Tool"),
        "slug": slug,
        "state": state,
        "priority": int(candidate.get("priority") or 0),
        "strict_quality_score": score,
        "audit_status": audit_status,
        "audit_problems": candidate.get("audit_problems") or [],
        "local_preview_path": str(candidate.get("local_preview_path") or ""),
        "preview_exists": has_preview(slug),
        "preview_url": candidate_preview_url(slug) if slug else "",
        "publish_allowed": False,
        "push_allowed": False,
        "commit_allowed": False,
    }


def build_review_pipeline() -> dict[str, Any]:
    """
    Build the factory review queues.

    This reads local factory output and creates:
    - ready_for_chris_review
    - renderer_needed
    - repair_queue
    - archived
    """
    backlog = load_backlog()
    latest = read_json(paths()["latest_factory"], {})
    candidates = [normalize_candidate(item) for item in backlog.get("candidate_tools", [])]

    ready = []
    renderer_needed = []
    repair = []
    archived = []
    selected = []

    for item in candidates:
        state = item["state"]
        score = item["strict_quality_score"]

        if state == "archived_by_chris":
            archived.append(item)
        elif state == "approved_for_staging_candidate":
            selected.append(item)
        elif state == "local_preview_ready" and score == 100 and item["preview_exists"]:
            ready.append(item)
        elif state == "template_required":
            renderer_needed.append(item)
        elif state in {"quality_failed", "regeneration_required"} or score < 100:
            repair.append(item)

    ready.sort(key=lambda item: item["priority"], reverse=True)
    renderer_needed.sort(key=lambda item: item["priority"], reverse=True)
    repair.sort(key=lambda item: item["priority"], reverse=True)
    selected.sort(key=lambda item: item["priority"], reverse=True)

    pipeline = {
        "pipeline_id": "nothingbuta-review-pipeline",
        "created_at": now_iso(),
        "state": "review_pipeline_ready",
        "latest_factory_status": latest.get("status"),
        "latest_factory_run_id": latest.get("run_id"),
        "counts": {
            "ready_for_chris_review": len(ready),
            "renderer_needed": len(renderer_needed),
            "repair_queue": len(repair),
            "approved_for_staging_candidate": len(selected),
            "archived": len(archived),
            "total_candidates": len(candidates),
        },
        "ready_for_chris_review": ready,
        "renderer_needed": renderer_needed,
        "repair_queue": repair,
        "approved_for_staging_candidate": selected,
        "archived": archived,
        "safety": {
            "commit_allowed": False,
            "push_allowed": False,
            "publish_allowed": False,
            "github_pages_settings_change_allowed": False,
            "analytics_allowed": False,
            "ads_allowed": False,
            "affiliate_links_allowed": False,
            "lead_capture_allowed": False,
        },
    }

    write_json(paths()["pipeline"], pipeline)
    write_review_markdown(pipeline)

    return pipeline


def write_review_markdown(pipeline: dict[str, Any]) -> None:
    """Write the human-readable review queue."""
    def lines(items: list[dict[str, Any]]) -> str:
        if not items:
            return "- None"
        return "\n".join(
            f"- {item['name']} | {item['slug']} | score {item['strict_quality_score']} | state {item['state']}"
            for item in items
        )

    report = f"""# NothingButA Review Queue

Generated: {pipeline['created_at']}

## Status

{pipeline['state'].upper()}

## Counts

- Ready for Chris review: {pipeline['counts']['ready_for_chris_review']}
- Renderer needed: {pipeline['counts']['renderer_needed']}
- Repair queue: {pipeline['counts']['repair_queue']}
- Approved for staging candidate: {pipeline['counts']['approved_for_staging_candidate']}
- Archived: {pipeline['counts']['archived']}
- Total candidates: {pipeline['counts']['total_candidates']}

## Ready For Chris Review

{lines(pipeline['ready_for_chris_review'])}

## Needs Strict Renderer

{lines(pipeline['renderer_needed'])}

## Needs Repair

{lines(pipeline['repair_queue'])}

## Selected For Staging Prep

{lines(pipeline['approved_for_staging_candidate'])}

## Safety

- Commit allowed: false
- Push allowed: false
- Publish allowed: false
- GitHub Pages settings changes: false
- Analytics: false
- Ads: false
- Affiliate links: false
- Lead capture: false
"""
    write_text(paths()["report"], report)


def mutate_candidate(tool_id: str, action: str) -> dict[str, Any]:
    """
    Mutate local candidate state from dashboard buttons.

    Allowed local-only actions:
    - approve: approved_for_staging_candidate
    - regenerate: regeneration_required
    - archive: archived_by_chris
    """
    valid_actions = {
        "approve": "approved_for_staging_candidate",
        "regenerate": "regeneration_required",
        "archive": "archived_by_chris",
    }

    if action not in valid_actions:
        raise ValueError(f"Unsupported action: {action}")

    backlog = load_backlog()
    changed = False

    for candidate in backlog.get("candidate_tools", []):
        if str(candidate.get("tool_id")) == str(tool_id):
            candidate["state"] = valid_actions[action]
            candidate["chris_action"] = action
            candidate["chris_action_at"] = now_iso()
            candidate["publish_allowed"] = False
            candidate["push_allowed"] = False
            candidate["commit_allowed"] = False
            candidate["external_action_allowed"] = False
            changed = True
            break

    if not changed:
        raise KeyError(f"Candidate not found: {tool_id}")

    save_backlog(backlog)
    return build_review_pipeline()


def read_candidate_preview(slug: str) -> str:
    """Read a local candidate preview file for dashboard display."""
    clean = clean_slug(slug)
    preview_path = paths()["candidates"] / clean / "index.html"

    if not preview_path.exists():
        return "<!doctype html><html><body><h1>Preview not found</h1></body></html>"

    return preview_path.read_text(encoding="utf-8-sig", errors="replace")


def render_card(item: dict[str, Any], show_actions: bool = True) -> str:
    """Render one dashboard candidate card."""
    problems = item.get("audit_problems") or []
    problem_text = "".join(f"<li>{safe(problem)}</li>" for problem in problems) or "<li>None</li>"

    preview_link = ""
    if item.get("preview_exists"):
        preview_link = f'<a class="btn" href="{safe(item["preview_url"])}" target="_blank">Preview</a>'

    actions = ""
    if show_actions:
        actions = f"""
        <form method="post" action="/nothingbuta/factory-review/{safe(item['tool_id'])}/approve">
          <button type="submit">Approve for staging prep</button>
        </form>
        <form method="post" action="/nothingbuta/factory-review/{safe(item['tool_id'])}/regenerate">
          <button class="secondary" type="submit">Regenerate</button>
        </form>
        <form method="post" action="/nothingbuta/factory-review/{safe(item['tool_id'])}/archive">
          <button class="danger" type="submit">Archive</button>
        </form>
        """

    return f"""
    <article class="card">
      <div class="topline">
        <span class="tag">{safe(item.get('state'))}</span>
        <span class="score">Score {safe(item.get('strict_quality_score'))}</span>
      </div>
      <h3>{safe(item.get('name'))}</h3>
      <p><strong>Slug:</strong> {safe(item.get('slug'))}</p>
      <p><strong>Priority:</strong> {safe(item.get('priority'))}</p>
      <div class="actions">{preview_link}{actions}</div>
      <details>
        <summary>Audit problems</summary>
        <ul>{problem_text}</ul>
      </details>
    </article>
    """


def render_section(title: str, items: list[dict[str, Any]], empty: str) -> str:
    """Render a candidate queue section."""
    cards = "\n".join(render_card(item) for item in items) if items else f'<div class="empty">{safe(empty)}</div>'
    return f"""
    <section class="section">
      <h2>{safe(title)}</h2>
      <div class="grid">{cards}</div>
    </section>
    """


def render_review_page() -> str:
    """Render dashboard page for NothingButA factory review."""
    pipeline = build_review_pipeline()
    counts = pipeline["counts"]

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>NothingButA Factory Review</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    *{{box-sizing:border-box}}
    body{{margin:0;font-family:Arial,sans-serif;background:#f8fafc;color:#0f172a}}
    .wrap{{width:min(100% - 24px,1200px);margin:auto;padding:24px 0 60px}}
    .hero{{background:linear-gradient(135deg,#0f172a,#2563eb);color:white;border-radius:28px;padding:28px;box-shadow:0 18px 55px rgba(15,23,42,.18)}}
    h1{{font-size:clamp(36px,7vw,70px);line-height:.95;margin:0 0 12px;letter-spacing:-.06em}}
    .hero p{{color:#dbeafe;font-size:18px;line-height:1.5;margin:0}}
    .stats{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:16px}}
    .stat{{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);border-radius:18px;padding:14px}}
    .stat strong{{display:block;font-size:26px}}
    .section{{margin-top:22px}}
    .section h2{{font-size:28px;letter-spacing:-.04em}}
    .grid{{display:grid;grid-template-columns:1fr;gap:14px}}
    .card{{background:white;border:1px solid #dbe3ef;border-radius:24px;padding:18px;box-shadow:0 14px 35px rgba(15,23,42,.08)}}
    .card h3{{font-size:23px;margin:10px 0;letter-spacing:-.03em}}
    .topline{{display:flex;justify-content:space-between;gap:10px;align-items:center}}
    .tag,.score{{display:inline-flex;border-radius:999px;padding:7px 10px;font-size:12px;font-weight:900}}
    .tag{{background:#e0e7ff;color:#3730a3}}
    .score{{background:#dcfce7;color:#14532d}}
    .actions{{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}}
    .btn,button{{border:0;border-radius:14px;background:#2563eb;color:white;padding:11px 13px;font-weight:900;text-decoration:none;cursor:pointer}}
    button.secondary{{background:#475569}}
    button.danger{{background:#991b1b}}
    details{{margin-top:12px;color:#475569}}
    .empty{{background:white;border:1px dashed #cbd5e1;border-radius:22px;padding:18px;color:#64748b}}
    .nav{{margin-top:16px}}
    .nav a{{color:white;font-weight:900}}
    @media (min-width:900px){{.stats{{grid-template-columns:repeat(5,1fr)}}.grid{{grid-template-columns:repeat(2,1fr)}}}}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <h1>NothingButA Factory Review</h1>
      <p>Local-only review queue for factory-built tool candidates. Public release is still approval-gated.</p>
      <div class="stats">
        <div class="stat"><strong>{counts['ready_for_chris_review']}</strong>Ready</div>
        <div class="stat"><strong>{counts['renderer_needed']}</strong>Needs renderer</div>
        <div class="stat"><strong>{counts['repair_queue']}</strong>Needs repair</div>
        <div class="stat"><strong>{counts['approved_for_staging_candidate']}</strong>Selected</div>
        <div class="stat"><strong>{counts['total_candidates']}</strong>Total</div>
      </div>
      <div class="nav"><a href="/nothingbuta">Back to NothingButA dashboard</a></div>
    </section>

    {render_section("Ready For Chris Review", pipeline["ready_for_chris_review"], "No 100-score candidates ready right now.")}
    {render_section("Needs Strict Renderer", pipeline["renderer_needed"], "No renderer blockers right now.")}
    {render_section("Needs Repair", pipeline["repair_queue"], "No repair queue right now.")}
    {render_section("Selected For Staging Prep", pipeline["approved_for_staging_candidate"], "Nothing selected yet.")}
  </main>
</body>
</html>"""