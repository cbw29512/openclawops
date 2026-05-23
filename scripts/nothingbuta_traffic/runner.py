from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from .analyzer import build_analysis
from .parser import load_inbox_csvs
from .reporting import write_reports
from .state import build_paths


logger = logging.getLogger(__name__)


def run_traffic_intelligence(root: Path) -> int:
    try:
        paths = build_paths(root)
        records, files = load_inbox_csvs(paths.inbox)

        if not files:
            proof = {
                "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "status": "PASS",
                "traffic_source_status": "waiting_for_csv",
                "csv_files_found": 0,
                "csv_files": [],
                "rows_read": 0,
                "pages_analyzed": 0,
                "opportunities": [],
                "safety_gates": {
                    "commit": False,
                    "push": False,
                    "publish": False,
                    "ads": False,
                    "affiliate_links": False,
                    "lead_capture": False,
                    "outreach": False,
                    "spending": False,
                },
            }
            write_reports(proof, paths.proof_json, paths.proof_md)
            print("NOTHINGBUTA TRAFFIC INTELLIGENCE V2: PASS")
            print("traffic_source_status: waiting_for_csv")
            print("csv_files_found: 0")
            print("json:", paths.proof_json)
            print("markdown:", paths.proof_md)
            return 0

        analysis = build_analysis(records, paths.repo_docs)

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "PASS",
            "traffic_source_status": "csv_loaded",
            "csv_files_found": len(files),
            "csv_files": files,
            "rows_read": len(records),
            "pages_analyzed": analysis["pages_analyzed"],
            "opportunities": analysis["opportunities"],
            "safety_gates": {
                "commit": False,
                "push": False,
                "publish": False,
                "ads": False,
                "affiliate_links": False,
                "lead_capture": False,
                "outreach": False,
                "spending": False,
            },
        }

        write_reports(proof, paths.proof_json, paths.proof_md)

        print("NOTHINGBUTA TRAFFIC INTELLIGENCE V2: PASS")
        print("traffic_source_status:", proof["traffic_source_status"])
        print("csv_files_found:", proof["csv_files_found"])
        print("rows_read:", proof["rows_read"])
        print("pages_analyzed:", proof["pages_analyzed"])
        print("json:", paths.proof_json)
        print("markdown:", paths.proof_md)

        return 0

    except Exception as exc:
        logger.exception("Traffic intelligence failed")
        print("NOTHINGBUTA TRAFFIC INTELLIGENCE V2: FAILED")
        print(str(exc))
        return 1
