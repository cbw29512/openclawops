from __future__ import annotations

import logging
from pathlib import Path

from .aggregate import aggregate
from .classify import classify


logger = logging.getLogger(__name__)


def build_analysis(records: list[dict], repo_docs: Path) -> dict:
    try:
        aggregated = aggregate(records, repo_docs)
        opportunities = [classify(item) for item in aggregated]
        opportunities = sorted(opportunities, key=lambda x: x["traffic_score"], reverse=True)

        return {
            "pages_analyzed": len(aggregated),
            "opportunities": opportunities,
        }

    except Exception as exc:
        logger.exception("Failed to build traffic analysis")
        raise RuntimeError("Failed to build traffic analysis") from exc
