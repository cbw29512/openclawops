from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .nothingbuta_state import (
        append_learning,
        load_candidates,
        project_root,
        run_local_review,
        save_candidates,
    )
except ImportError:
    from nothingbuta_state import (
        append_learning,
        load_candidates,
        project_root,
        run_local_review,
        save_candidates,
    )

logger = logging.getLogger("nova.nothingbuta_auto_loop")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_policy() -> dict[str, Any]:
    path = project_root() / "data" / "nothingbuta_quality_policy.json"
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        logger.exception("Failed to load quality policy.")
        return {
            "min_quality_score": 85,
            "min_seo_score": 80,
            "min_code_score": 80,
            "min_mobile_score": 90,
            "required_trust_score": 100,
            "html_required_markers": [],
        }


def get_candidate(candidate_id: str) -> dict[str, Any] | None:
    for candidate in load_candidates():
        if candidate.get("candidate_id") == candidate_id:
            return candidate
    return None


def mutate_candidate(candidate_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    candidates = load_candidates()
    for candidate in candidates:
        if candidate.get("candidate_id") == candidate_id:
            candidate.update(updates)
            candidate["updated_at"] = now_iso()
            save_candidates(candidates)
            return candidate
    raise ValueError(f"Candidate not found: {candidate_id}")


def gate_reasons(candidate: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    reasons: list[str] = []

    checks = [
        ("quality_score", policy.get("min_quality_score", 85), "quality score too low"),
        ("seo_score", policy.get("min_seo_score", 80), "SEO score too low"),
        ("code_score", policy.get("min_code_score", 80), "code score too low"),
        ("mobile_score", policy.get("min_mobile_score", 90), "mobile score too low"),
    ]

    for field, minimum, message in checks:
        if int(candidate.get(field) or 0) < int(minimum):
            reasons.append(message)

    if int(candidate.get("trust_score") or 0) < int(policy.get("required_trust_score", 100)):
        reasons.append("trust score below required gate")

    preview_path = project_root() / str(candidate.get("local_preview_path") or "")
    html = preview_path.read_text(encoding="utf-8-sig", errors="replace").lower() if preview_path.exists() else ""

    for marker in policy.get("html_required_markers", []):
        if marker.lower() not in html:
            reasons.append(f"missing mobile/UX marker: {marker}")

    public_policy_path = project_root() / "data" / "nothingbuta_public_page_policy.json"
    try:
        public_policy = json.loads(public_policy_path.read_text(encoding="utf-8-sig"))
    except Exception:
        public_policy = {"banned_public_terms": [], "required_public_markers": []}

    for term in public_policy.get("banned_public_terms", []):
        if term.lower() in html:
            reasons.append(f"visitor-facing page contains internal term: {term}")

    for marker in public_policy.get("required_public_markers", []):
        if marker.lower() not in html:
            reasons.append(f"missing public-page marker: {marker}")

    if "adsbygoogle" in html or "affiliate" in html:
        reasons.append("blocked monetization marker found in local draft")

    return sorted(set(reasons))


def regenerate_candidate(candidate: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    root = project_root()
    template_path = root / "nothingbuta" / "templates" / "debt_payoff_mobile_first.html"
    preview_path = root / str(candidate.get("local_preview_path") or "")

    if not template_path.exists():
        raise FileNotFoundError(f"Missing regeneration template: {template_path}")

    preview_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template_path, preview_path)

    updated = mutate_candidate(
        str(candidate["candidate_id"]),
        {
            "state": "little_brother_regenerated",
            "chris_decision": "internal_auto_regenerated",
            "auto_regeneration_count": int(candidate.get("auto_regeneration_count", 0)) + 1,
            "auto_regeneration_reasons": reasons,
            "publish_allowed": False,
            "external_action_allowed": False,
        },
    )
    append_learning("little_brother_regenerated", updated, "; ".join(reasons))
    return updated


def mark_ready(candidate_id: str) -> dict[str, Any]:
    updated = mutate_candidate(
        candidate_id,
        {
            "state": "chris_review_required",
            "chris_decision": "ready_after_internal_review",
            "publish_allowed": False,
            "external_action_allowed": False,
        },
    )
    append_learning("chris_review_required", updated, "Internal Big Brother review passed.")
    return updated


def mark_failed(candidate_id: str, reasons: list[str]) -> dict[str, Any]:
    updated = mutate_candidate(
        candidate_id,
        {
            "state": "auto_regeneration_required",
            "chris_decision": "internal_quality_gate_failed",
            "auto_regeneration_reasons": reasons,
            "publish_allowed": False,
            "external_action_allowed": False,
        },
    )
    append_learning("auto_regeneration_required", updated, "; ".join(reasons))
    return updated


def run_auto_quality_loop() -> dict[str, Any]:
    policy = load_policy()
    reviewable = {
        "local_preview_ready",
        "design_feedback_applied",
        "little_brother_regenerated",
        "regeneration_requested",
        "auto_regeneration_required",
    }

    results = []

    for candidate in load_candidates():
        candidate_id = str(candidate.get("candidate_id") or "")
        if not candidate_id or candidate.get("state") not in reviewable:
            continue

        reviewed = run_local_review(candidate_id)
        reasons = gate_reasons(reviewed, policy)

        if candidate.get("state") == "regeneration_requested" or reasons:
            regenerated = regenerate_candidate(reviewed, reasons or ["Chris requested regeneration."])
            reviewed_again = run_local_review(candidate_id)
            final_reasons = gate_reasons(reviewed_again, policy)

            final = mark_failed(candidate_id, final_reasons) if final_reasons else mark_ready(candidate_id)
            results.append({"candidate_id": candidate_id, "action": "regenerated", "final_state": final["state"]})
        else:
            final = mark_ready(candidate_id)
            results.append({"candidate_id": candidate_id, "action": "reviewed", "final_state": final["state"]})

    return {"status": "complete", "results": results}