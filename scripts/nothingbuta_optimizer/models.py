from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RelatedTool:
    slug: str
    name: str
    why: str


@dataclass(frozen=True)
class PageOptimizationConfig:
    batch_id: str
    batch_number: str
    target_slug: str
    target_path: Path
    backup_root: Path
    data_dir: Path
    reports_dir: Path
    json_out: Path
    md_out: Path
    content_marker: str
    schema_marker: str
    new_meta_description: str
    app_name: str
    app_url: str
    application_category: str
    section_label: str
    section_heading: str
    how_to_heading: str
    how_to_body: str
    result_heading: str
    result_body: str
    next_heading: str
    next_body: str
    related_tools: list[RelatedTool]


def config_summary(config: PageOptimizationConfig) -> dict:
    try:
        return {
            "batch_id": config.batch_id,
            "batch_number": config.batch_number,
            "target_slug": config.target_slug,
            "target_path": str(config.target_path),
            "related_tools": [tool.slug for tool in config.related_tools],
        }
    except Exception as exc:
        logger.exception("Failed to summarize config")
        raise RuntimeError("Failed to summarize config") from exc
