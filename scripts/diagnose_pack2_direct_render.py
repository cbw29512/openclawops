from __future__ import annotations

import logging
import sys
from pathlib import Path


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS_DIR = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


PACK2_SLUGS = [
    "roi-calculator",
    "recipe-scale-calculator",
    "paint-coverage-calculator",
    "flooring-calculator",
    "concrete-calculator",
]


def main() -> None:
    try:
        from nothingbuta_factory.renderer_catalog_v2 import TOOL_CONFIGS
        from nothingbuta_factory.legacy_factory import html_shell, audit_html, strict_score

        print("=== Pack 2 Direct Render Diagnostic ===")
        print(f"catalog_count: {len(TOOL_CONFIGS)}")
        print("")

        for slug in PACK2_SLUGS:
            config = TOOL_CONFIGS.get(slug)

            print(f"## {slug}")

            if config is None:
                print("in_catalog: False")
                print("")
                continue

            html_value = html_shell(config)
            problems = audit_html(html_value, {"slug": slug, "name": config.get("name")}, config)
            score = strict_score(problems)

            print("in_catalog: True")
            print(f"name: {config.get('name')}")
            print(f"formula: {config.get('formula')}")
            print(f"html_length: {len(html_value)}")
            print(f"score: {score}")
            print(f"problem_count: {len(problems)}")

            if problems:
                print("problems:")
                for problem in problems:
                    print(f"- {problem}")
            else:
                print("problems: []")

            print("")

    except Exception as exc:
        logging.exception("Pack 2 direct render diagnostic failed.")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()