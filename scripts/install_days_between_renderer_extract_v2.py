from __future__ import annotations

import ast
import html
import logging
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS_DIR = ROOT / "scripts"
MODULE_DIR = SCRIPTS_DIR / "nothingbuta_factory"

LEGACY_PATH = MODULE_DIR / "legacy_factory.py"
SPECIALS_PATH = MODULE_DIR / "renderer_specials_v2.py"
ENTRYPOINT_PATH = SCRIPTS_DIR / "nova_nothingbuta_local_factory_loop.py"
REPORTS_PATH = MODULE_DIR / "reports_v2.py"
AUDIT_PATH = MODULE_DIR / "audit_rules_v2.py"
CATALOG_PATH = MODULE_DIR / "renderer_catalog_v2.py"

TARGET_FUNCTION = "days_between_html"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def read_text(path: Path) -> str:
    try:
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        logging.exception("Read failed: %s", path)
        raise SystemExit(1) from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.write_text(text, encoding="utf-8")
    except Exception as exc:
        logging.exception("Write failed: %s", path)
        raise SystemExit(1) from exc


def backup_file(path: Path, label: str) -> Path:
    try:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = path.with_name(f"{path.name}.bak-{label}-{stamp}")
        shutil.copy2(path, backup_path)
        return backup_path
    except Exception as exc:
        logging.exception("Backup failed: %s", path)
        raise SystemExit(1) from exc


def find_function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node

    logging.error("Missing function: %s", name)
    raise SystemExit(1)


def build_specials_module(function_lines: list[str]) -> str:
    body_lines = function_lines[1:]

    converted_body = []
    for line in body_lines:
        converted_body.append("        " + line if line.strip() else "")

    module_lines = [
        "from __future__ import annotations",
        "",
        "import logging",
        "from typing import Any, Callable",
        "",
        "logger = logging.getLogger(__name__)",
        "",
        "",
        "def days_between_html_v2(",
        "    config: dict[str, Any],",
        "    safe_text: Callable[[Any], str],",
        ") -> str:",
        "    \"\"\"Render the strict Days Between Dates calculator HTML.\"\"\"",
        "    try:",
        *converted_body,
        "    except Exception:",
        "        logger.exception('Failed to render Days Between Dates HTML.')",
        "        raise",
        "",
    ]

    return "\n".join(module_lines)


def build_wrapper() -> list[str]:
    return [
        "def days_between_html(config: dict[str, Any]) -> str:",
        "    \"\"\"Delegate Days Between Dates rendering to renderer_specials_v2.\"\"\"",
        "    from nothingbuta_factory.renderer_specials_v2 import days_between_html_v2",
        "",
        "    return days_between_html_v2(config=config, safe_text=safe_text)",
    ]


def compile_file(path: Path) -> bool:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logging.error("Compile failed for %s\n%s\n%s", path, result.stdout, result.stderr)
            return False

        return True
    except Exception as exc:
        logging.exception("Compile crashed: %s", path)
        raise SystemExit(1) from exc


def temp_unit_test() -> bool:
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from nothingbuta_factory.renderer_specials_v2 import days_between_html_v2

        def fake_safe_text(value: Any) -> str:
            return html.escape(str(value), quote=True)

        output = days_between_html_v2(
            config={
                "name": "Days Between Dates Calculator",
                "description": "Compare two calendar dates safely.",
            },
            safe_text=fake_safe_text,
        )

        required = [
            "<!doctype html>",
            'type="date"',
            'aria-live="polite"',
            "Calculate days",
            "Inclusive day count",
            "document.querySelectorAll",
        ]

        return all(marker in output for marker in required)
    except Exception:
        logging.exception("Temp renderer unit test failed.")
        return False


def main() -> None:
    source = read_text(LEGACY_PATH)

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        logging.exception("Legacy factory does not parse before extraction.")
        raise SystemExit(1) from exc

    node = find_function(tree, TARGET_FUNCTION)

    if node.end_lineno is None:
        logging.error("AST did not provide end line for %s.", TARGET_FUNCTION)
        raise SystemExit(1)

    lines = source.splitlines()
    function_lines = lines[node.lineno - 1 : node.end_lineno]
    function_line_count = len(function_lines)

    if function_line_count != 115:
        logging.error("Expected 115-line function, found %s. Stop.", function_line_count)
        raise SystemExit(1)

    legacy_backup = backup_file(LEGACY_PATH, "days-between-renderer-extract-v2")
    specials_backup = backup_file(SPECIALS_PATH, "pre-days-between-renderer-extract-v2") if SPECIALS_PATH.exists() else None

    write_text(SPECIALS_PATH, build_specials_module(function_lines))

    patched_lines = (
        lines[: node.lineno - 1]
        + build_wrapper()
        + lines[node.end_lineno :]
    )

    write_text(LEGACY_PATH, "\n".join(patched_lines) + "\n")

    compile_ok = all(
        [
            compile_file(SPECIALS_PATH),
            compile_file(CATALOG_PATH),
            compile_file(AUDIT_PATH),
            compile_file(REPORTS_PATH),
            compile_file(LEGACY_PATH),
            compile_file(ENTRYPOINT_PATH),
        ]
    )

    unit_ok = temp_unit_test()

    print("")
    print("=== Days Between Renderer Extract V2 Result ===")
    print(f"legacy_backup: {legacy_backup}")
    print(f"specials_backup: {specials_backup}")
    print(f"specials_path: {SPECIALS_PATH}")
    print(f"renderer_lines_moved: {function_line_count}")
    print(f"compile_ok: {compile_ok}")
    print(f"temp_unit_test_ok: {unit_ok}")

    if not compile_ok or not unit_ok:
        logging.error("Validation failed. Roll back before continuing.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()