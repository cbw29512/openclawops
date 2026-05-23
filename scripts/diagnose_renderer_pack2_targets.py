from __future__ import annotations

import json
import logging
import sys
from pathlib import Path


# State schema:
# REGISTRY_PATH: current candidate states.
# BACKLOG_PATH: source backlog with tool definitions.
# SCRIPTS_DIR: allows importing extracted renderer catalog.
ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA_DIR = ROOT / "data"
SCRIPTS_DIR = ROOT / "scripts"

REGISTRY_PATH = DATA_DIR / "nothingbuta_candidate_registry.json"
BACKLOG_PATH = DATA_DIR / "nothingbuta_tool_backlog.json"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def load_json(path: Path) -> dict:
    """Load a JSON object with clear failure logging."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logging.exception("Failed to load JSON: %s", path)
        raise SystemExit(1) from exc


def main() -> None:
    """Print read-only Renderer Pack 2 target details."""
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from nothingbuta_factory.renderer_catalog_v2 import TOOL_CONFIGS

        registry = load_json(REGISTRY_PATH)
        backlog = load_json(BACKLOG_PATH)

        candidates = registry.get("generated_candidates", [])
        blocked = [
            item for item in candidates
            if item.get("state") == "template_required"
        ]

        backlog_items = (
            backlog if isinstance(backlog, list)
            else backlog.get("tools", backlog.get("backlog", backlog.get("items", [])))
        )

        print("=== Renderer Expansion Pack 2 Targets ===")
        print(f"blocked_count: {len(blocked)}")
        print(f"catalog_count: {len(TOOL_CONFIGS)}")
        print("")

        for item in blocked:
            slug = item.get("slug")
            name = item.get("name")
            matching_backlog = [
                entry for entry in backlog_items
                if entry.get("slug") == slug or entry.get("name") == name
            ]

            print(f"## {name}")
            print(f"slug: {slug}")
            print(f"state: {item.get('state')}")
            print(f"audit_problems: {item.get('audit_problems')}")
            print(f"in_catalog: {slug in TOOL_CONFIGS}")
            print(f"backlog_matches: {len(matching_backlog)}")

            for entry in matching_backlog[:1]:
                print("backlog_entry:")
                print(json.dumps(entry, indent=2)[:1200])

            print("")

    except Exception as exc:
        logging.exception("Renderer Pack 2 diagnostic failed.")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()