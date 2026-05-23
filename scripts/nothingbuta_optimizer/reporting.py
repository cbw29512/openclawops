from __future__ import annotations

import json
import logging

from .models import PageOptimizationConfig


logger = logging.getLogger(__name__)


def write_reports(proof: dict, config: PageOptimizationConfig) -> None:
    try:
        config.data_dir.mkdir(parents=True, exist_ok=True)
        config.reports_dir.mkdir(parents=True, exist_ok=True)

        config.json_out.write_text(json.dumps(proof, indent=2), encoding="utf-8")

        lines = [
            f"# NothingButA Optimization Batch {config.batch_number}",
            "",
            f"Generated: {proof['generated_at']}",
            "",
            "## Summary",
            "",
            f"- Status: {proof['status']}",
            f"- Target slug: `{proof['target_slug']}`",
            f"- Changed: `{proof['changed']}`",
            f"- Backup: `{proof['backup_path']}`",
            "",
            "## Changes",
            "",
        ]

        for change in proof["changes"]:
            lines.append(f"- {change}")

        if proof["problems"]:
            lines.extend(["", "## Problems", ""])
            for problem in proof["problems"]:
                lines.append(f"- `{problem}`")

        config.md_out.write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        logger.exception("Failed to write reports")
        raise RuntimeError("Failed to write reports") from exc
