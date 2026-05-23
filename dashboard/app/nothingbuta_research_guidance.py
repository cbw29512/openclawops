from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .nothingbuta_state import load_candidates, save_candidates
except ImportError:
    from nothingbuta_state import load_candidates, save_candidates

logger = logging.getLogger("nova.nothingbuta_research_guidance")


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


def build_builder_context() -> dict[str, Any]:
    """
    Build the machine-readable guidance packet Little Brother should use.

    This does not scrape or publish anything. It only combines local policy and
    research summaries already approved for safe pattern extraction.
    """
    root = project_root()
    data_dir = root / "data"

    findings = read_json(data_dir / "nothingbuta_inspiration_findings.json", {})
    research_policy = read_json(data_dir / "nothingbuta_research_policy.json", {})
    public_policy = read_json(data_dir / "nothingbuta_public_page_policy.json", {})
    quality_policy = read_json(data_dir / "nothingbuta_quality_policy.json", {})
    queue = load_candidates()

    active_candidate = queue[0] if queue else {}

    context = {
        "context_id": "nothingbuta-builder-context",
        "created_at": now_iso(),
        "status": "builder_context_ready",
        "candidate_id": active_candidate.get("candidate_id"),
        "candidate_name": active_candidate.get("site_name"),
        "research_status": findings.get("status"),
        "research_policy_id": research_policy.get("policy_id"),
        "quality_policy_id": quality_policy.get("policy_id"),
        "public_policy_id": public_policy.get("policy_id"),
        "mobile_first_required": True,
        "no_copy_required": True,
        "public_cleanliness_required": True,
        "publish_allowed": False,
        "external_action_allowed": False,
        "domain_purchase_allowed": False,
        "ads_allowed": False,
        "affiliate_links_allowed": False,
        "lead_capture_allowed": False,
        "design_consistency_rule": {
            "keep_consistent": [
                "tool near top",
                "large mobile inputs",
                "clear result card",
                "plain-English labels",
                "no forced signup",
                "visitor-facing disclaimer where needed",
                "input to result flow",
            ],
            "vary_by_site": [
                "colors",
                "hero layout",
                "examples",
                "supporting sections",
                "tone",
                "visual identity",
                "tool-specific result explanation",
            ],
        },
        "pain_points_to_address": findings.get("top_user_pain_points", []),
        "mobile_ux_patterns": findings.get("mobile_ux_patterns", []),
        "result_explanation_patterns": findings.get("result_explanation_patterns", []),
        "faq_candidates": findings.get("faq_candidates", []),
        "feature_gap_candidates": findings.get("feature_gap_candidates", []),
        "trust_and_disclaimer_patterns": findings.get("trust_and_disclaimer_patterns", []),
        "do_not_copy_notes": findings.get("do_not_copy_notes", []),
        "next_build_guidance": findings.get("next_build_guidance", []),
        "blocked_public_terms": public_policy.get("banned_public_terms", []),
        "required_public_markers": public_policy.get("required_public_markers", []),
    }

    write_json(data_dir / "nothingbuta_builder_context.json", context)
    return context


def apply_builder_context_to_queue() -> dict[str, Any]:
    """
    Attach the current builder context to the active candidate record.

    This makes the dashboard/queue prove that inspiration guidance was applied
    before Big Brother/Little Brother review.
    """
    context = build_builder_context()
    candidates = load_candidates()

    for candidate in candidates:
        if candidate.get("candidate_id") == context.get("candidate_id"):
            candidate["builder_context_status"] = context["status"]
            candidate["inspiration_guidance_applied"] = True
            candidate["research_status"] = context.get("research_status")
            candidate["applied_research_patterns"] = {
                "pain_points_to_address": context.get("pain_points_to_address", [])[:5],
                "mobile_ux_patterns": context.get("mobile_ux_patterns", [])[:5],
                "result_explanation_patterns": context.get("result_explanation_patterns", [])[:5],
                "faq_candidates": context.get("faq_candidates", [])[:5],
                "trust_and_disclaimer_patterns": context.get("trust_and_disclaimer_patterns", [])[:5],
            }
            candidate["no_copy_required"] = True
            candidate["public_cleanliness_required"] = True
            candidate["mobile_first_required"] = True
            candidate["updated_at"] = now_iso()

    save_candidates(candidates)

    return {
        "status": "complete",
        "builder_context": context,
        "candidate_count": len(candidates),
    }