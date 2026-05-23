from __future__ import annotations

import ast
import logging
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS_DIR = ROOT / "scripts"
MODULE_DIR = SCRIPTS_DIR / "nothingbuta_factory"

LEGACY_PATH = MODULE_DIR / "legacy_factory.py"
AUDIT_PATH = MODULE_DIR / "audit_rules_v2.py"
ENTRYPOINT_PATH = SCRIPTS_DIR / "nova_nothingbuta_local_factory_loop.py"
REPORTS_PATH = MODULE_DIR / "reports_v2.py"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def backup_file(path: Path, label: str) -> Path:
    try:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = path.with_name(f"{path.name}.bak-{label}-{stamp}")
        shutil.copy2(path, backup_path)
        return backup_path
    except Exception as exc:
        logging.exception("Backup failed: %s", path)
        raise SystemExit(1) from exc


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


def build_audit_module() -> str:
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
    """Convert audit problem count into strict quality score."""
    try:
        if not problems:
            return 100
        return max(0, 100 - (len(problems) * 15))
    except Exception:
        logger.exception("NothingButA strict score calculation failed.")
        raise
'''


def build_wrappers() -> list[str]:
    return [
        "def audit_html(html_value: str, candidate: dict[str, Any], config: dict[str, Any] | None) -> list[str]:",
        "    \"\"\"Delegate strict HTML auditing to audit_rules_v2.\"\"\"",
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
        "    \"\"\"Delegate strict scoring to audit_rules_v2.\"\"\"",
        "    from nothingbuta_factory.audit_rules_v2 import strict_score_v2",
        "",
        "    return strict_score_v2(problems)",
    ]


def find_function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    logging.error("Missing function: %s", name)
    raise SystemExit(1)


def unit_test() -> bool:
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from nothingbuta_factory.audit_rules_v2 import audit_html_v2, strict_score_v2

        html = """
<!doctype html>
<html>
<head>
<title>Unit Test Calculator</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>@media (max-width:700px){body{margin:0}}</style>
</head>
<body>
<label>Amount <input inputmode="decimal"></label>
<label>Rate <input inputmode="decimal"></label>
<button>Calculate</button>
<section aria-live="polite">Result</section>
<section>FAQ</section>
<p>Estimate only. This is not financial advice.</p>
</body>
</html>
"""
        problems = audit_html_v2(
            html_value=html,
            candidate={"name": "Unit Test Calculator"},
            config={"name": "Unit Test Calculator", "category": "finance"},
            blocked_public_markers=["blocked-marker"],
            weak_template_markers=["weak-marker"],
        )

        return problems == [] and strict_score_v2(problems) == 100 and strict_score_v2(["x"]) == 85
    except Exception:
        logging.exception("Audit unit test failed.")
        return False


def main() -> None:
    try:
        source = LEGACY_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        lines = source.splitlines()

        audit_node = find_function(tree, "audit_html")
        score_node = find_function(tree, "strict_score")

        audit_count = audit_node.end_lineno - audit_node.lineno + 1
        score_count = score_node.end_lineno - score_node.lineno + 1

        if audit_count != 60 or score_count != 4:
            logging.error("Unexpected function sizes: audit=%s score=%s", audit_count, score_count)
            raise SystemExit(1)

        legacy_backup = backup_file(LEGACY_PATH, "audit-rules-extract-v2-fixed")
        audit_backup = backup_file(AUDIT_PATH, "pre-audit-rules-extract-v2-fixed") if AUDIT_PATH.exists() else None

        AUDIT_PATH.write_text(build_audit_module(), encoding="utf-8")

        patched_lines = (
            lines[: audit_node.lineno - 1]
            + build_wrappers()
            + lines[score_node.end_lineno :]
        )

        LEGACY_PATH.write_text("\n".join(patched_lines) + "\n", encoding="utf-8")

        compile_ok = all(
            [
                compile_file(AUDIT_PATH),
                compile_file(REPORTS_PATH),
                compile_file(LEGACY_PATH),
                compile_file(ENTRYPOINT_PATH),
            ]
        )
        unit_ok = unit_test()

        print("")
        print("=== Audit Rules Extract V2 Fixed Result ===")
        print(f"legacy_backup: {legacy_backup}")
        print(f"audit_backup: {audit_backup}")
        print(f"audit_path: {AUDIT_PATH}")
        print(f"compile_ok: {compile_ok}")
        print(f"temp_unit_test_ok: {unit_ok}")

        if not compile_ok or not unit_ok:
            logging.error("Validation failed. Roll back before continuing.")
            raise SystemExit(1)

    except Exception as exc:
        logging.exception("Installer crashed.")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()