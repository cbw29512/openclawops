from __future__ import annotations

import ast
import logging
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# -----------------------------
# State schema:
# ROOT: local OpenClawOps project root.
# LEGACY_PATH: current working monolithic factory after report writer extraction.
# AUDIT_PATH: new extracted audit rules module.
# ENTRYPOINT_PATH: tiny factory entrypoint.
# REPORTS_PATH: previously extracted report writer module.
# -----------------------------
ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS_DIR = ROOT / "scripts"
MODULE_DIR = SCRIPTS_DIR / "nothingbuta_factory"

LEGACY_PATH = MODULE_DIR / "legacy_factory.py"
AUDIT_PATH = MODULE_DIR / "audit_rules_v2.py"
ENTRYPOINT_PATH = SCRIPTS_DIR / "nova_nothingbuta_local_factory_loop.py"
REPORTS_PATH = MODULE_DIR / "reports_v2.py"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def read_text(path: Path) -> str:
    """Read UTF-8 source text with clear error reporting."""
    try:
        if not path.exists():
            raise FileNotFoundError(f"Missing required file: {path}")
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        logging.exception("Read failed: %s", path)
        raise SystemExit(1) from exc


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 source text with clear error reporting."""
    try:
        path.write_text(text, encoding="utf-8")
    except Exception as exc:
        logging.exception("Write failed: %s", path)
        raise SystemExit(1) from exc


def backup_file(path: Path, label: str) -> Path:
    """Create timestamped backup before mutation."""
    try:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = path.with_name(f"{path.name}.bak-{label}-{stamp}")
        shutil.copy2(path, backup_path)
        return backup_path
    except Exception as exc:
        logging.exception("Backup failed: %s", path)
        raise SystemExit(1) from exc


def parse_tree(source: str) -> ast.Module:
    """Parse source once so function boundaries are AST-derived."""
    try:
        return ast.parse(source)
    except SyntaxError as exc:
        logging.exception("Cannot parse legacy factory before extraction.")
        raise SystemExit(1) from exc


def find_top_level_function(tree: ast.Module, function_name: str) -> ast.FunctionDef:
    """Find a top-level function by exact name."""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return node

    logging.error("Could not find function: %s", function_name)
    raise SystemExit(1)


def build_audit_module() -> str:
    """Build extracted audit module with injected marker lists."""
    return '''from __future__ import annotations

import logging
from typing import Any, Sequence

logger = logging.getLogger(__name__)


def audit_html_v2(
    html_value: str,
    candidate: dict[str, Any],
    config: dict[str, Any] | None,
    blocked_public_markers: Sequence[str],
    weak_template_markers: Sequence[str],
) -> list[str]:
    """Audit generated public HTML for strict NothingButA quality and safety rules."""
    try:
        problems: list[str] = []
        lower = html_value.lower()

        if config is None:
            problems.append("no strict tool-specific renderer exists for this slug")
            return problems

        required_markers = [
            "<!doctype html>",
            "name=\\"viewport\\"",
            "<title>",
            "<input",
            "<button",
            "aria-live",
            "@media",
            "inputmode",
            "<label",
            "faq",
            "result",
            str(config["name"]).lower(),
        ]

        for marker in required_markers:
            if marker.lower() not in lower:
                problems.append(f"missing required marker: {marker}")

        for marker in blocked_public_markers:
            if marker.lower() in lower:
                problems.append(f"blocked public marker found: {marker}")

        for marker in weak_template_markers:
            if marker.lower() in lower:
                problems.append(f"weak generic template marker found: {marker}")

        input_count = lower.count("<input")
        label_count = lower.count("<label")

        if input_count < 2:
            problems.append("too few inputs for a useful single-purpose tool")

        if label_count < input_count:
            problems.append("every input must have a visible label")

        if "<script src=" in lower:
            problems.append("external scripts are blocked")

        if "fetch(" in lower or "xmlhttprequest" in lower:
            problems.append("network calls are blocked")

        if "document.cookie" in lower or "localstorage" in lower or "sessionstorage" in lower:
            problems.append("visitor storage is blocked")

        if config.get("category") in {"finance", "work", "business"}:
            if "estimate only" not in lower:
                problems.append("finance/work/business tools require estimate-only disclaimer")
            if "not financial" not in lower and "not tax" not in lower and "not payroll" not in lower:
                problems.append("finance/work/business tools require professional-advice disclaimer")

        return problems
    except Exception:
        logger.exception("NothingButA HTML audit failed.")
        raise


def strict_score_v2(problems: list[str]) -> int:
    """Convert audit problem count into the strict quality score."""
    try:
        if not problems:
            return 100

        return max(0, 100 - (len(problems) * 15))
    except Exception:
        logger.exception("NothingButA strict score calculation failed.")
        raise
'''


def build_legacy_wrappers() -> list[str]:
    """Keep old function names stable while delegating to extracted audit module."""
    return [
        "def audit_html(html_value: str, candidate: dict[str, Any], config: dict[str, Any] | None) -> list[str]:",
        "    \"\"\"Delegate strict HTML auditing to the extracted audit_rules_v2 module.\"\"\"",
        "    from nothingbuta_factory.audit_rules_v2 import audit_html_v2",
        "",
        "    return audit_html_v2(",
        "        html_value=html_value,",
        "        candidate=candidate,",
        "        config=config,",
        "        blocked_public_markers=BLOCKED_PUBLIC_MARKERS,",
        "        weak_template_markers=WEAK_TEMPLATE_MARKERS,",
        "    )",
        "",
        "",
        "def strict_score(problems: list[str]) -> int:",
        "    \"\"\"Delegate strict scoring to the extracted audit_rules_v2 module.\"\"\"",
        "    from nothingbuta_factory.audit_rules_v2 import strict_score_v2",
        "",
        "    return strict_score_v2(problems)",
    ]


def compile_file(path: Path) -> bool:
    """Compile-check a Python file."""
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
        logging.exception("Compile check crashed for %s", path)
        raise SystemExit(1) from exc


def temp_unit_test_audit_module() -> bool:
    """Test extracted audit behavior without touching real factory outputs."""
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from nothingbuta_factory.audit_rules_v2 import audit_html_v2, strict_score_v2

        good_html = """
<!doctype html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Unit Test Calculator</title>
  <style>
    @media (max-width: 700px) { body { margin: 0; } }
  </style>
</head>
<body>
  <main>
    <h1>Unit Test Calculator</h1>
    <label>Amount <input inputmode="decimal" value="100"></label>
    <label>Rate <input inputmode="decimal" value="5"></label>
    <button>Calculate</button>
    <section aria-live="polite">Result</section>
    <section>FAQ</section>
    <p>Estimate only. This is not financial advice.</p>
  </main>
</body>
</html>
"""

        problems = audit_html_v2(
            html_value=good_html,
            candidate={"name": "Unit Test Calculator"},
            config={"name": "Unit Test Calculator", "category": "finance"},
            blocked_public_markers=["internal-only-marker"],
            weak_template_markers=["weak-template-marker"],
        )

        return problems == [] and strict_score_v2(problems) == 100 and strict_score_v2(["x"]) == 85
    except Exception:
        logging.exception("Temp audit unit test failed.")
        return False


def main() -> None:
    """Install audit rules extraction as one reversible patch."""
    source = read_text(LEGACY_PATH)
    tree = parse_tree(source)
    lines = source.splitlines()

    audit_node = find_top_level_function(tree, "audit_html")
    score_node = find_top_level_function(tree, "strict_score")

    if audit_node.end_lineno is None or score_node.end_lineno is None:
        logging.error("Python AST did not provide end line numbers.")
        raise SystemExit(1)

    if audit_node.lineno >= score_node.lineno:
        logging.error("Unexpected function order. Stop before patching.")
        raise SystemExit(1)

    audit_line_count = audit_node.end_lineno - audit_node.lineno + 1
    score_line_count = score_node.end_lineno - score_node.lineno + 1

    if audit_line_count != 60 or score_line_count != 4:
        logging.error(
            "Unexpected function sizes. audit_html=%s, strict_score=%s. Stop.",
            audit_line_count,
            score_line_count,
        )
        raise SystemExit(1)

    legacy_backup = backup_file(LEGACY_PATH, "audit-rules-extract-v2")
    audit_backup = backup_file(AUDIT_PATH, "pre-audit-rules-extract-v2") if AUDIT_PATH.exists() else None

    write_text(AUDIT_PATH, build_audit_module())

    wrapper_lines = build_legacy_wrappers()
    patched_lines = (
        lines[: audit_node.lineno - 1]
        + wrapper_lines
        + lines[score_node.end_lineno :]
    )

    write_text(LEGACY_PATH, "\\n".join(patched_lines) + "\\n")

    compile_ok = all(
        [
            compile_file(AUDIT_PATH),
            compile_file(REPORTS_PATH),
            compile_file(LEGACY_PATH),
            compile_file(ENTRYPOINT_PATH),
        ]
    )

    unit_ok = temp_unit_test_audit_module()

    print("")
    print("=== Audit Rules Extract V2 Result ===")
    print(f"legacy_backup: {legacy_backup}")
    print(f"audit_backup: {audit_backup}")
    print(f"audit_path: {AUDIT_PATH}")
    print(f"compile_ok: {compile_ok}")
    print(f"temp_unit_test_ok: {unit_ok}")

    if not compile_ok or not unit_ok:
        logging.error("Patch installed but validation failed. Roll back before continuing.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()