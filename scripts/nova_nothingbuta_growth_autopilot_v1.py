from __future__ import annotations

import logging
import sys
from pathlib import Path


# Objective:
# Run the NothingButA Growth Autopilot v1.
#
# State:
# - This is Little Brother's hourly watcher.
# - It checks live quality, SEO opportunities, repo cleanliness, and writes proof.
# - It does not commit, push, publish, monetize, spend, or contact anyone.
#
# Big picture:
# The site is already live and clean. This keeps it watched 24/7 locally while
# Big Brother/Chris reviews anything that needs action.


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from nothingbuta_growth import run_growth_autopilot


if __name__ == "__main__":
    raise SystemExit(run_growth_autopilot(ROOT))
