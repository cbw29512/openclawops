from __future__ import annotations

import logging
from datetime import datetime

from .html_injection import inject_content_section, inject_structured_data, replace_meta_description
from .io_ops import backup_target, read_text, write_text
from .models import PageOptimizationConfig
from .reporting import write_reports
from .validation import self_check


logger = logging.getLogger(__name__)


def run_optimization(config: PageOptimizationConfig) -> int:
    try:
        backup_path = backup_target(config.target_path, config.backup_root, config.target_slug, config.batch_number)
        original = read_text(config.target_path)

        updated = original
        changes: list[str] = []

        updated, meta_changed = replace_meta_description(updated, config.new_meta_description)
        if meta_changed:
            changes.append("expanded_meta_description")

        updated, schema_changed = inject_structured_data(updated, config)
        if schema_changed:
            changes.append("added_webapplication_json_ld")

        updated, content_changed = inject_content_section(updated, config)
        if content_changed:
            changes.append("added_helpful_copy_and_related_links")

        problems = self_check(updated, config)

        if not problems and updated != original:
            write_text(config.target_path, updated)

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "batch_id": config.batch_id,
            "target_slug": config.target_slug,
            "target_path": str(config.target_path),
            "backup_path": str(backup_path),
            "status": "PASS" if not problems else "FAILED",
            "changed": updated != original and not problems,
            "changes": changes,
            "problems": problems,
        }

        write_reports(proof, config)

        print(f"NOTHINGBUTA OPTIMIZATION BATCH {config.batch_number}: {proof['status']}")
        print("target:", config.target_slug)
        print("changed:", proof["changed"])
        print("backup:", backup_path)
        print("json:", config.json_out)
        print("markdown:", config.md_out)

        if problems:
            print("problems:", problems)

        return 0 if proof["status"] == "PASS" else 1
    except Exception as exc:
        logger.exception("Optimization batch failed")
        print(f"NOTHINGBUTA OPTIMIZATION BATCH {config.batch_number}: FAILED")
        print(str(exc))
        return 1
