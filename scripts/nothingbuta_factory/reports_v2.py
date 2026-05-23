from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


def write_run_reports_v2(
    run: dict[str, Any],
    runs_dir: Path,
    latest_json_path: Path,
    latest_report_path: Path,
    write_json: Callable[[Path, Any], None],
    write_text: Callable[[Path, str], None],
) -> None:
    """Write per-run and latest factory reports using injected dependencies."""
    try:
            run_id = run["run_id"]
            run_json_path = runs_dir / f"{run_id}.json"
            run_md_path = runs_dir / f"{run_id}.md"

            write_json(run_json_path, run)
            write_json(latest_json_path, run)

            built_lines = "\n".join(
                f"- {item['name']} - {item['state']} - score {item.get('strict_quality_score', 0)} - {item.get('local_preview_path') or 'no preview written'}"
                for item in run.get("built_candidates", [])
            ) or "- None"

            blocked_lines = "\n".join(
                f"- {item['name']} - {problem}"
                for item in run.get("built_candidates", [])
                for problem in item.get("audit_problems", [])
            ) or "- None"

            report = f"""# NothingButA Local Factory Loop

        Generated: {run['created_at']}

        ## Status

        {run['status'].upper()}

        ## Strict Quality Patch

        ACTIVE

        ## Batch

        - Batch size: {run.get('batch_size', 'n/a')}
        - Backlog candidates: {run.get('backlog_candidate_count', 'n/a')}
        - Existing weak previews marked: {run.get('weak_existing_marked', 0)}
        - Built this run: {len(run.get('built_candidates', []))}

        ## Built Candidates

        {built_lines}

        ## Audit Problems / Blocks

        {blocked_lines}

        ## Safety

        - Commit allowed: false
        - Push allowed: false
        - Publish allowed: false
        - GitHub Pages settings changes: false
        - Analytics: false
        - Ads: false
        - Affiliate links: false
        - Lead capture: false

        ## Next Human Action

        Review only candidates with state local_preview_ready and strict_quality_score 100.
        """

            write_text(run_md_path, report)
            write_text(latest_report_path, report)
    except Exception:
        logger.exception('Failed to write NothingButA factory reports.')
        raise
