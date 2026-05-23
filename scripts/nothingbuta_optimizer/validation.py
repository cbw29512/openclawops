from __future__ import annotations

import logging
import re

from .models import PageOptimizationConfig


logger = logging.getLogger(__name__)

ROOT_DROPDOWN_OPTION = '<option value="../">All tools home</option>'


def self_check(html: str, config: PageOptimizationConfig) -> list[str]:
    try:
        problems: list[str] = []

        if ROOT_DROPDOWN_OPTION in html:
            problems.append("root_dropdown_option_present")

        description_match = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
            html,
            flags=re.IGNORECASE,
        )

        if not description_match:
            problems.append("missing_meta_description")
        elif len(description_match.group(1)) < 90:
            problems.append("meta_description_still_too_short")

        if config.schema_marker not in html:
            problems.append("missing_structured_data")

        if config.content_marker not in html:
            problems.append("missing_growth_content_section")

        for tool in config.related_tools:
            expected = f'../{tool.slug}/'
            if expected not in html:
                problems.append(f"missing_related_link:{tool.slug}")

        return problems
    except Exception as exc:
        logger.exception("Self-check failed")
        raise RuntimeError("Self-check failed") from exc
