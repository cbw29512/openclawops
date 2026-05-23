from __future__ import annotations

import logging
import sys
from pathlib import Path


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from nothingbuta_traffic import run_traffic_intelligence


if __name__ == "__main__":
    raise SystemExit(run_traffic_intelligence(ROOT))
