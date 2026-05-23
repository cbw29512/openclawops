from __future__ import annotations

import sys
from pathlib import Path

# Keep the package import stable even when this script is launched from dashboard/.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from nothingbuta_factory.legacy_factory import main


if __name__ == "__main__":
    main()