from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from .decision import build_growth_decision
from .ops import git_snapshot, load_json, run_python_script
from .reporting import write_reports
from .state import build_paths


logger = logging.getLogger(__name__)


def run_growth_autopilot(root: Path) -> int:
    try:
        paths = build_paths(root)

        monitor_run = run_python_script(paths.monitor_script, paths.root)
        seo_run = run_python_script(paths.seo_script, paths.root)

        monitor = load_json(paths.monitor_json)
        seo = load_json(paths.seo_json)
        git_state = git_snapshot(paths.repo)

        decision = build_growth_decision(monitor, seo, git_state)

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": decision["status"],
            "monitor_run": monitor_run,
            "seo_run": seo_run,
            "decision": decision,
            "git": git_state,
            "safety_gates": {
                "commit": False,
                "push": False,
                "publish": False,
                "github_pages_changes": False,
                "analytics_change": False,
                "ads": False,
                "affiliate_links": False,
                "lead_capture": False,
                "outreach": False,
                "spending": False,
            },
        }

        write_reports(proof, paths.proof_json, paths.proof_md)

        print("NOTHINGBUTA GROWTH AUTOPILOT V1:", proof["status"])
        print("live_quality:", decision["little_brother"]["live_quality_status"])
        print("failed_pages:", decision["little_brother"]["live_quality_failed_pages"])
        print("seo_opportunities:", decision["little_brother"]["seo_total_opportunities"])
        print("high_priority:", decision["little_brother"]["seo_high_priority_opportunities"])
        print("repo_dirty:", decision["little_brother"]["repo_working_tree_dirty"])
        print("json:", paths.proof_json)
        print("markdown:", paths.proof_md)

        return 0 if proof["status"] == "PASS" else 1

    except Exception as exc:
        logger.exception("Growth autopilot failed")
        print("NOTHINGBUTA GROWTH AUTOPILOT V1: FAILED")
        print(str(exc))
        return 1
