from __future__ import annotations

import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path


# Objective:
# Self-test NothingButA Traffic Intelligence v2 with local fake traffic rows.
#
# This script DOES:
# - create a temporary fake Search Console-style CSV
# - parse it
# - analyze it
# - write proof
#
# This script DOES NOT:
# - put fake data in the real traffic inbox
# - edit live pages
# - commit
# - push
# - publish
# - monetize


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_traffic_v2_selftest")

ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS_DIR = ROOT / "scripts"
TEST_DIR = ROOT / "data" / "nothingbuta_traffic_selftest"
TEST_CSV = TEST_DIR / "fake_search_console_pages.csv"
PROOF_JSON = ROOT / "data" / "nothingbuta_traffic_v2_selftest.json"
PROOF_MD = ROOT / "reports" / "nothingbuta-traffic-v2-selftest.md"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from nothingbuta_traffic.analyzer import build_analysis
from nothingbuta_traffic.parser import read_csv_file
from nothingbuta_traffic.state import build_paths


def write_fake_csv() -> None:
    try:
        TEST_DIR.mkdir(parents=True, exist_ok=True)

        rows = [
            {
                "Page": "https://cbw29512.github.io/nothingbuta/car-payment-calculator/",
                "Clicks": "4",
                "Impressions": "600",
                "CTR": "0.67%",
                "Position": "11.2",
            },
            {
                "Page": "https://cbw29512.github.io/nothingbuta/discount-calculator/",
                "Clicks": "0",
                "Impressions": "82",
                "CTR": "0%",
                "Position": "18.5",
            },
            {
                "Page": "https://cbw29512.github.io/nothingbuta/roi-calculator/",
                "Clicks": "62",
                "Impressions": "900",
                "CTR": "6.88%",
                "Position": "4.1",
            },
        ]

        with TEST_CSV.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["Page", "Clicks", "Impressions", "CTR", "Position"])
            writer.writeheader()
            writer.writerows(rows)

    except Exception as exc:
        logger.exception("Failed to write fake CSV")
        raise RuntimeError("Failed to write fake CSV") from exc


def write_proof(proof: dict) -> None:
    try:
        PROOF_JSON.parent.mkdir(parents=True, exist_ok=True)
        PROOF_MD.parent.mkdir(parents=True, exist_ok=True)

        PROOF_JSON.write_text(json.dumps(proof, indent=2), encoding="utf-8")

        lines = [
            "# NothingButA Traffic Intelligence v2 Self-Test",
            "",
            f"Generated: {proof['generated_at']}",
            "",
            f"- Status: `{proof['status']}`",
            f"- Fake records loaded: `{proof['fake_records_loaded']}`",
            f"- Pages analyzed: `{proof['pages_analyzed']}`",
            f"- Opportunities detected: `{proof['opportunities_detected']}`",
            "",
            "## Top Opportunities",
            "",
        ]

        for item in proof["top_opportunities"]:
            lines.append(
                f"- `{item['slug']}` score `{item['traffic_score']}` "
                f"clicks `{item['clicks']}` impressions `{item['impressions']}` "
                f"type `{item['opportunity_type']}`"
            )

        PROOF_MD.write_text("\n".join(lines), encoding="utf-8")

    except Exception as exc:
        logger.exception("Failed to write proof")
        raise RuntimeError("Failed to write proof") from exc


def main() -> int:
    try:
        paths = build_paths(ROOT)

        write_fake_csv()
        records = read_csv_file(TEST_CSV)
        analysis = build_analysis(records, paths.repo_docs)

        opportunities = analysis["opportunities"]
        detected = [item for item in opportunities if item["traffic_score"] > 0]

        proof = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "status": "PASS" if len(detected) >= 2 else "NEEDS_REVIEW",
            "fake_csv": str(TEST_CSV),
            "fake_records_loaded": len(records),
            "pages_analyzed": analysis["pages_analyzed"],
            "opportunities_detected": len(detected),
            "top_opportunities": opportunities[:5],
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

        write_proof(proof)

        print("NOTHINGBUTA TRAFFIC V2 SELFTEST:", proof["status"])
        print("fake_records_loaded:", proof["fake_records_loaded"])
        print("pages_analyzed:", proof["pages_analyzed"])
        print("opportunities_detected:", proof["opportunities_detected"])
        print("json:", PROOF_JSON)
        print("markdown:", PROOF_MD)

        return 0 if proof["status"] == "PASS" else 1

    except Exception as exc:
        logger.exception("Self-test failed")
        print("NOTHINGBUTA TRAFFIC V2 SELFTEST: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
