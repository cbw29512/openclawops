from __future__ import annotations

import logging
import shutil
from pathlib import Path


# Objective:
# Add the NothingButA live quality monitor to the existing safe autopilot check.
#
# This script DOES:
# - back up nova_nothingbuta_safe_autopilot_check.py
# - insert a live quality monitor command into the autopilot check list
# - fail closed if the expected insertion point is not found
#
# This script DOES NOT:
# - commit
# - push
# - publish
# - change GitHub Pages settings
# - add analytics, ads, affiliate links, lead capture, or outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("install_live_quality_monitor_into_autopilot")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPT_PATH = ROOT / "scripts" / "nova_nothingbuta_safe_autopilot_check.py"

INSERT_BLOCK = '''    {
        "label": "live quality monitor",
        "command": ["python", str(SCRIPTS / "nova_nothingbuta_live_quality_monitor.py")],
    },
'''


def main() -> int:
    try:
        if not SCRIPT_PATH.exists():
            raise RuntimeError(f"Missing autopilot script: {SCRIPT_PATH}")

        text = SCRIPT_PATH.read_text(encoding="utf-8")

        if '"label": "live quality monitor"' in text:
            print("NOTHINGBUTA LIVE QUALITY AUTOPILOT INSTALL: PASS")
            print("already_installed: True")
            print("script:", SCRIPT_PATH)
            return 0

        marker = '''    {
        "label": "hourly optimizer report",
        "command": ["python", str(SCRIPTS / "nova_nothingbuta_hourly_optimizer_report.py")],
    },
'''

        if marker not in text:
            raise RuntimeError(
                "Expected hourly optimizer report block not found. "
                "Refusing blind patch."
            )

        backup_path = SCRIPT_PATH.with_suffix(".py.bak-live-quality-monitor")
        shutil.copy2(SCRIPT_PATH, backup_path)

        updated = text.replace(marker, marker + INSERT_BLOCK, 1)
        SCRIPT_PATH.write_text(updated, encoding="utf-8")

        print("NOTHINGBUTA LIVE QUALITY AUTOPILOT INSTALL: PASS")
        print("already_installed: False")
        print("backup:", backup_path)
        print("script:", SCRIPT_PATH)
        return 0

    except Exception as exc:
        logger.exception("Install failed")
        print("NOTHINGBUTA LIVE QUALITY AUTOPILOT INSTALL: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
