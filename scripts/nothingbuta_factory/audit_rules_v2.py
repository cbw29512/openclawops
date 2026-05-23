from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)


def audit_html_v2(
    html_value: str,
    candidate: dict[str, Any],
    config: dict[str, Any] | None,
    blocked_public_markers: Sequence[str],
    weak_template_markers: Sequence[str],
) -> list[str]:
    """Audit generated public HTML for strict NothingButA quality and safety rules."""
    try:
        problems: list[str] = []
        lower = html_value.lower()

        if config is None:
            problems.append("no strict tool-specific renderer exists for this slug")
            return problems

        required_markers = [
            "<!doctype html>",
            "name=\"viewport\"",
            "<title>",
            "<input",
            "<button",
            "aria-live",
            "@media",
            "inputmode",
            "<label",
            "faq",
            "result",
            str(config["name"]).lower(),
        ]

        for marker in required_markers:
            if marker.lower() not in lower:
                problems.append(f"missing required marker: {marker}")

        for marker in blocked_public_markers:
            if marker.lower() in lower:
                problems.append(f"blocked public marker found: {marker}")

        for marker in weak_template_markers:
            if marker.lower() in lower:
                problems.append(f"weak generic template marker found: {marker}")

        input_count = lower.count("<input")
        label_count = lower.count("<label")

        if input_count < 2:
            problems.append("too few inputs for a useful single-purpose tool")

        if label_count < input_count:
            problems.append("every input must have a visible label")

        if "<script src=" in lower:
            problems.append("external scripts are blocked")

        if "fetch(" in lower or "xmlhttprequest" in lower:
            problems.append("network calls are blocked")

        if "document.cookie" in lower or "localstorage" in lower or "sessionstorage" in lower:
            problems.append("visitor storage is blocked")

        if config.get("category") in {"finance", "work", "business"}:
            if "estimate only" not in lower:
                problems.append("finance/work/business tools require estimate-only disclaimer")
            if "not financial" not in lower and "not tax" not in lower and "not payroll" not in lower:
                problems.append("finance/work/business tools require professional-advice disclaimer")

        return problems
    except Exception:
        logger.exception("NothingButA HTML audit failed.")
        raise


def strict_score_v2(problems: list[str]) -> int:
    """Convert audit problem count into strict quality score."""
    try:
        if not problems:
            return 100
        return max(0, 100 - (len(problems) * 15))
    except Exception:
        logger.exception("NothingButA strict score calculation failed.")
        raise
