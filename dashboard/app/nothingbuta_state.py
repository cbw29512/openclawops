from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("nova.nothingbuta_state")


def project_root() -> Path:
    """Resolve the OpenClawOps project root from dashboard/app."""
    return Path(__file__).resolve().parents[2]


def now_iso() -> str:
    """Return an audit-friendly timestamp."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def queue_path() -> Path:
    """Return the local review queue path."""
    return project_root() / "data" / "nothingbuta_review_queue.json"


def ledger_path() -> Path:
    """Return the local learning ledger path."""
    return project_root() / "data" / "nothingbuta_learning_ledger.jsonl"


def load_candidates() -> list[dict[str, Any]]:
    """Load queue candidates safely."""
    try:
        path = queue_path()
        if not path.exists():
            return []

        data = json.loads(path.read_text(encoding="utf-8-sig"))

        if isinstance(data, dict):
            return [data]

        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]

        return []
    except Exception:
        logger.exception("Failed to load NothingButA candidates.")
        return []


def save_candidates(candidates: list[dict[str, Any]]) -> None:
    """Persist queue candidates."""
    try:
        path = queue_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(candidates, indent=2), encoding="utf-8")
    except Exception:
        logger.exception("Failed to save NothingButA candidates.")
        raise


def append_learning(event_type: str, candidate: dict[str, Any], notes: str | None = None) -> None:
    """Append Chris/Nova feedback as JSONL."""
    try:
        path = ledger_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        event = {
            "event_type": event_type,
            "candidate_id": candidate.get("candidate_id"),
            "site_name": candidate.get("site_name"),
            "state": candidate.get("state"),
            "chris_decision": candidate.get("chris_decision"),
            "notes": notes,
            "created_at": now_iso(),
        }

        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")
    except Exception:
        logger.exception("Failed to append NothingButA learning event.")
        raise


def update_candidate(candidate_id: str, action: str, notes: str | None = None) -> dict[str, Any]:
    """Apply Chris decision or local review update."""
    candidates = load_candidates()

    for candidate in candidates:
        if candidate.get("candidate_id") != candidate_id:
            continue

        if action == "approve":
            candidate["state"] = "approved_for_staging"
            candidate["chris_decision"] = "approved_for_staging"

        elif action == "regenerate":
            clean_notes = (notes or "").strip()
            if not clean_notes:
                raise ValueError("Regeneration notes are required.")

            candidate["state"] = "regeneration_requested"
            candidate["chris_decision"] = "regenerate"
            candidate["regeneration_notes"] = clean_notes
            candidate["revision_requested_count"] = int(candidate.get("revision_requested_count", 0)) + 1

        elif action == "delete":
            candidate["state"] = "deleted_archived"
            candidate["chris_decision"] = "delete"
            candidate["delete_notes"] = (notes or "").strip() or None

        else:
            raise ValueError(f"Unsupported action: {action}")

        candidate["publish_allowed"] = False
        candidate["external_action_allowed"] = False
        candidate["updated_at"] = now_iso()

        save_candidates(candidates)
        append_learning(action, candidate, notes)
        return candidate

    raise ValueError(f"Candidate not found: {candidate_id}")


def run_local_review(candidate_id: str) -> dict[str, Any]:
    """Run deterministic local Big Brother review."""
    candidates = load_candidates()

    for candidate in candidates:
        if candidate.get("candidate_id") != candidate_id:
            continue

        preview_rel = candidate.get("local_preview_path") or ""
        preview_path = project_root() / preview_rel

        if not preview_path.exists():
            review = {
                "status": "failed",
                "overall_score": 0,
                "recommendations": [f"Missing preview file: {preview_path}"],
                "reviewed_at": now_iso(),
            }
        else:
            html = preview_path.read_text(encoding="utf-8", errors="replace").lower()

            checks = [
                ("title", "<title>" in html, "Add a clear HTML title."),
                ("description", 'name="description"' in html, "Add a meta description."),
                ("viewport", 'name="viewport"' in html, "Add mobile viewport metadata."),
                ("inputs", html.count("<input") >= 3, "Tool needs enough inputs to be useful."),
                ("result", "result" in html, "Add a visible result/output area."),
                ("no_ads", "adsbygoogle" not in html, "Do not add ads during local review."),
                ("no_affiliate", "affiliate" not in html, "Do not add affiliate links during local review."),
                ("disclaimer", "not financial advice" in html, "Finance tools need a clear disclaimer."),
                ("public_clean", not any(term in html for term in ["local-only", "draft", "nova", "big brother", "little brother", "internal", "regenerate", "future version", "next upgrade", "chris"]), "Remove internal workflow or draft language from the visitor-facing page."),
            ]

            passed = sum(1 for _, ok, _ in checks if ok)
            total = len(checks)
            score = round((passed / total) * 100)

            review = {
                "status": "complete",
                "overall_score": score,
                "quality_score": score,
                "seo_score": round((sum(1 for name, ok, _ in checks if name in ["title", "description"] and ok) / 2) * 100),
                "code_score": round((sum(1 for name, ok, _ in checks if name in ["inputs", "result"] and ok) / 2) * 100),
                "mobile_score": 100 if any(name == "viewport" and ok for name, ok, _ in checks) else 0,
                "trust_score": round((sum(1 for name, ok, _ in checks if name in ["no_ads", "no_affiliate", "disclaimer"] and ok) / 3) * 100),
                "checks": [{"name": name, "passed": ok, "fix": fix} for name, ok, fix in checks],
                "recommendations": [fix for _, ok, fix in checks if not ok],
                "reviewed_at": now_iso(),
            }

        candidate["big_brother_review_status"] = review["status"]
        candidate["big_brother_review"] = review
        candidate["quality_score"] = review.get("quality_score", 0)
        candidate["seo_score"] = review.get("seo_score", 0)
        candidate["code_score"] = review.get("code_score", 0)
        candidate["mobile_score"] = review.get("mobile_score", 0)
        candidate["trust_score"] = review.get("trust_score", 0)

        if candidate.get("state") == "local_preview_ready":
            candidate["state"] = "chris_review_required"

        candidate["updated_at"] = now_iso()
        save_candidates(candidates)
        append_learning("big_brother_review", candidate)
        return candidate

    raise ValueError(f"Candidate not found: {candidate_id}")


