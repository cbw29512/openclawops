from __future__ import annotations

import logging
from pathlib import Path

from .slugging import known_slugs, slug_from_url


logger = logging.getLogger(__name__)


def aggregate(records: list[dict], repo_docs: Path) -> list[dict]:
    try:
        known = known_slugs(repo_docs)
        by_slug: dict[str, dict] = {}

        for row in records:
            slug = slug_from_url(row["url"])

            if slug not in known:
                continue

            item = by_slug.setdefault(
                slug,
                {
                    "slug": slug,
                    "url": row["url"],
                    "clicks": 0,
                    "impressions": 0,
                    "ctr": 0.0,
                    "position": 0.0,
                    "position_weight": 0,
                },
            )

            clicks = int(row.get("clicks", 0))
            impressions = int(row.get("impressions", 0))
            position = float(row.get("position", 0.0))

            item["clicks"] += clicks
            item["impressions"] += impressions

            if impressions > 0 and position > 0:
                item["position"] += position * impressions
                item["position_weight"] += impressions

        results: list[dict] = []

        for item in by_slug.values():
            impressions = item["impressions"]

            item["ctr"] = item["clicks"] / impressions if impressions > 0 else 0.0
            item["position"] = (
                item["position"] / item["position_weight"]
                if item["position_weight"] > 0
                else 0.0
            )
            item.pop("position_weight", None)
            results.append(item)

        return sorted(results, key=lambda x: (x["impressions"], x["clicks"]), reverse=True)

    except Exception as exc:
        logger.exception("Failed to aggregate traffic records")
        raise RuntimeError("Failed to aggregate traffic records") from exc
