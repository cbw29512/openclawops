from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path


# Objective:
# Add the NothingButA SEO Growth Research Report to the Safe Autopilot Check.
#
# This script DOES:
# - back up nova_nothingbuta_safe_autopilot_check.py
# - insert a report-only SEO growth research step after the live quality monitor
#
# This script DOES NOT:
# - edit public site files
# - commit
# - push
# - publish
# - change GitHub Pages settings
# - add analytics, ads, affiliate links, lead capture, or outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("install_seo_growth_research_into_autopilot")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPT_PATH = ROOT / "scripts" / "nova_nothingbuta_safe_autopilot_check.py"


LIVE_QUALITY_BLOCK = '''    {
        "label": "live quality monitor",
        "command": ["python", str(SCRIPTS / "nova_nothingbuta_live_quality_monitor.py")],
    },
'''


SEO_GROWTH_BLOCK = '''    {
        "label": "seo growth research report",
        "command": ["python", str(SCRIPTS / "nova_nothingbuta_seo_growth_research_report.py")],
    },
'''


def main() -> int:
    try:
        if not SCRIPT_PATH.exists():
            raise RuntimeError(f"Missing autopilot script: {SCRIPT_PATH}")

        text = SCRIPT_PATH.read_text(encoding="utf-8")

        if '"label": "seo growth research report"' in text:
            print("NOTHINGBUTA SEO GROWTH AUTOPILOT INSTALL: PASS")
            print("already_installed: True")
            print("script:", SCRIPT_PATH)
            return 0

        if LIVE_QUALITY_BLOCK not in text:
            raise RuntimeError(
                "Expected live quality monitor block not found. Refusing blind patch."
            )

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = SCRIPT_PATH.with_suffix(f".py.bak-seo-growth-autopilot-{stamp}")
        shutil.copy2(SCRIPT_PATH, backup_path)

        updated = text.replace(LIVE_QUALITY_BLOCK, LIVE_QUALITY_BLOCK + SEO_GROWTH_BLOCK, 1)
        SCRIPT_PATH.write_text(updated, encoding="utf-8")

        print("NOTHINGBUTA SEO GROWTH AUTOPILOT INSTALL: PASS")
        print("already_installed: False")
        print("backup:", backup_path)
        print("script:", SCRIPT_PATH)
        return 0

    except Exception as exc:
        logger.exception("SEO growth autopilot install failed")
        print("NOTHINGBUTA SEO GROWTH AUTOPILOT INSTALL: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
