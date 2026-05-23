from __future__ import annotations

import ast
import logging
from pathlib import Path


# State schema:
# ROOT = local project root
# LEGACY_PATH = current preserved factory module after report-writer extraction
# KEYWORDS = function-name filters for possible audit extraction targets
ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
LEGACY_PATH = ROOT / "scripts" / "nothingbuta_factory" / "legacy_factory.py"
REPORTS_PATH = ROOT / "scripts" / "nothingbuta_factory" / "reports_v2.py"
ENTRYPOINT_PATH = ROOT / "scripts" / "nova_nothingbuta_local_factory_loop.py"
KEYWORDS = ("audit", "quality", "strict")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def count_lines(path: Path) -> int:
    """Return line count for one file, failing clearly if missing."""
    try:
        if not path.exists():
            raise FileNotFoundError(path)
        return len(path.read_text(encoding="utf-8").splitlines())
    except Exception as exc:
        logging.exception("Could not count lines for %s", path)
        raise SystemExit(1) from exc


def find_matching_functions(path: Path) -> list[tuple[str, int, int, int]]:
    """Find top-level functions whose names look audit/quality related."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as exc:
        logging.exception("Could not parse %s", path)
        raise SystemExit(1) from exc

    matches: list[tuple[str, int, int, int]] = []

    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue

        lowered_name = node.name.lower()
        if any(keyword in lowered_name for keyword in KEYWORDS):
            matches.append(
                (
                    node.name,
                    node.lineno,
                    node.end_lineno,
                    node.end_lineno - node.lineno + 1,
                )
            )

    return matches


def main() -> None:
    """Print read-only audit-boundary diagnostics."""
    print("=== NothingButA Module Size Check ===")
    for path in (ENTRYPOINT_PATH, LEGACY_PATH, REPORTS_PATH):
        print(f"{path.name}: {count_lines(path)} lines")

    print("")
    print("=== Audit-like functions in legacy_factory.py ===")
    matches = find_matching_functions(LEGACY_PATH)

    if not matches:
        print("No audit-like functions found.")
        return

    for name, start_line, end_line, line_count in matches:
        print(f"{name}: lines {start_line}-{end_line} ({line_count} lines)")


if __name__ == "__main__":
    main()