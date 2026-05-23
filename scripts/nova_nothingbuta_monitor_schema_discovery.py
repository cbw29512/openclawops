from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any


# Objective:
# Discover the real JSON schema of nothingbuta_live_quality_monitor.json.
#
# Why:
# The previous PowerShell inspection assumed fields like page_results.url,
# but the monitor file appears to use a different shape.
#
# This script DOES:
# - read the monitor JSON
# - print top-level keys
# - find list fields
# - print non-PASS records if found
#
# This script DOES NOT:
# - edit files
# - commit
# - push
# - publish
# - change GitHub Pages


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_monitor_schema_discovery")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
MONITOR_PATH = ROOT / "data" / "nothingbuta_live_quality_monitor.json"


def load_json(path: Path) -> Any:
    try:
        if not path.exists():
            raise RuntimeError(f"Missing monitor JSON: {path}")

        return json.loads(path.read_text(encoding="utf-8"))

    except Exception as exc:
        logger.exception("Failed to load monitor JSON")
        raise RuntimeError("Failed to load monitor JSON") from exc


def is_non_pass_record(item: Any) -> bool:
    try:
        if not isinstance(item, dict):
            return False

        status = str(item.get("status", "")).upper()
        problems = item.get("problems") or item.get("issues") or item.get("failures") or []

        return status not in {"", "PASS"} or bool(problems)

    except Exception as exc:
        logger.exception("Failed to inspect record")
        raise RuntimeError("Failed to inspect record") from exc


def walk_lists(value: Any, path: str = "$") -> list[tuple[str, list[Any]]]:
    try:
        found: list[tuple[str, list[Any]]] = []

        if isinstance(value, list):
            found.append((path, value))

            for index, item in enumerate(value[:3]):
                found.extend(walk_lists(item, f"{path}[{index}]"))

        elif isinstance(value, dict):
            for key, child in value.items():
                found.extend(walk_lists(child, f"{path}.{key}"))

        return found

    except Exception as exc:
        logger.exception("Failed while walking JSON lists")
        raise RuntimeError("Failed while walking JSON lists") from exc


def summarize_record(item: dict) -> dict:
    try:
        return {
            "keys": sorted(item.keys()),
            "url": item.get("url") or item.get("page") or item.get("page_url") or item.get("path"),
            "slug": item.get("slug"),
            "status": item.get("status"),
            "title": item.get("title"),
            "description_length": item.get("description_length") or item.get("meta_description_length"),
            "h1_count": item.get("h1_count"),
            "problems": item.get("problems") or item.get("issues") or item.get("failures"),
        }

    except Exception as exc:
        logger.exception("Failed to summarize record")
        raise RuntimeError("Failed to summarize record") from exc


def main() -> int:
    try:
        data = load_json(MONITOR_PATH)

        print("NOTHINGBUTA LIVE QUALITY MONITOR SCHEMA DISCOVERY")
        print("monitor:", MONITOR_PATH)
        print("root_type:", type(data).__name__)

        if isinstance(data, dict):
            print("top_level_keys:", sorted(data.keys()))
            print("status:", data.get("status"))
            print("pages_checked:", data.get("pages_checked"))
            print("failed_pages:", data.get("failed_pages"))

        print("")
        print("LIST FIELDS FOUND")

        list_fields = walk_lists(data)

        for path, items in list_fields:
            print(f"{path} | count={len(items)}")

        print("")
        print("NON-PASS RECORDS FOUND")

        found_count = 0

        for path, items in list_fields:
            for item in items:
                if is_non_pass_record(item):
                    found_count += 1
                    print("")
                    print("source_list:", path)
                    print(json.dumps(summarize_record(item), indent=2))

        print("")
        print("non_pass_records:", found_count)
        print("SCHEMA DISCOVERY COMPLETE: no files changed.")

        return 0

    except Exception as exc:
        logger.exception("Schema discovery failed")
        print("NOTHINGBUTA LIVE QUALITY MONITOR SCHEMA DISCOVERY: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
