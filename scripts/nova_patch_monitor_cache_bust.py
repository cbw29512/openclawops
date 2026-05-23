from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path


# Objective:
# Patch nova_nothingbuta_live_quality_monitor.py so every fetched URL is cache-busted.
#
# Why:
# GitHub Pages/CDN can briefly serve stale HTML after a push.
# The monitor should verify current live pages, not cached responses.
#
# This script DOES:
# - back up the monitor script
# - replace fetch_url with a cache-busting version
#
# This script DOES NOT:
# - change site files
# - commit
# - push
# - publish


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_monitor_cache_bust_patch")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
MONITOR_PATH = ROOT / "scripts" / "nova_nothingbuta_live_quality_monitor.py"


NEW_FETCH_URL = '''def fetch_url(url: str) -> tuple[int, str]:
    """Fetch a URL using only the Python standard library.

    Why cache-bust:
    GitHub Pages/CDN can briefly serve stale HTML after a push.
    The monitor should check the current page, not a cached copy.
    """
    try:
        separator = "&" if "?" in url else "?"
        stamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        request_url = f"{url}{separator}v={stamp}"

        request = urllib.request.Request(
            request_url,
            headers={
                "User-Agent": "NothingButAQualityMonitor/1.0",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            status = int(response.status)
            content = response.read().decode("utf-8", errors="replace")
            return status, content

    except Exception as exc:
        logger.exception("Failed to fetch URL: %s", url)
        raise RuntimeError(f"Failed to fetch URL: {url}") from exc
'''


def main() -> int:
    try:
        if not MONITOR_PATH.exists():
            raise RuntimeError(f"Monitor script missing: {MONITOR_PATH}")

        backup_path = MONITOR_PATH.with_suffix(".py.bak_cache_bust")
        shutil.copy2(MONITOR_PATH, backup_path)

        text = MONITOR_PATH.read_text(encoding="utf-8")

        pattern = re.compile(
            r"def fetch_url\(url: str\) -> tuple\[int, str\]:.*?(?=\n\ndef parse_html)",
            flags=re.DOTALL,
        )

        updated, replacements = pattern.subn(NEW_FETCH_URL.rstrip(), text, count=1)

        if replacements != 1:
            raise RuntimeError(f"Expected to replace exactly 1 fetch_url block, replaced {replacements}")

        MONITOR_PATH.write_text(updated, encoding="utf-8")

        print("NOTHINGBUTA MONITOR CACHE-BUST PATCH: PASS")
        print("backup:", backup_path)
        print("patched:", MONITOR_PATH)

        return 0

    except Exception as exc:
        logger.exception("Cache-bust patch failed")
        print("NOTHINGBUTA MONITOR CACHE-BUST PATCH: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
