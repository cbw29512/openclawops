from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS = ROOT / "scripts"

AUTOPILOT_PATH = SCRIPTS / "nova_nothingbuta_safe_autopilot_check.py"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


AUTOPILOT_SOURCE = r'''from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

REGISTRY = DATA / "nothingbuta_candidate_registry.json"
REPORT = REPORTS / "nothingbuta-safe-autopilot-check.md"

COMMANDS = [
    {
        "label": "direct render diagnostic",
        "command": ["python", str(SCRIPTS / "diagnose_pack2_direct_render.py")],
    },
    {
        "label": "Pack 2 registry refresh",
        "command": ["python", str(SCRIPTS / "refresh_pack2_registry_candidates.py")],
    },
    {
        "label": "factory loop",
        "command": ["python", str(SCRIPTS / "nova_nothingbuta_local_factory_loop.py")],
    },
    {
        "label": "release batch picker",
        "command": ["python", str(SCRIPTS / "nova_nothingbuta_release_batch_picker.py")],
    },
    {
        "label": "release freeze packet",
        "command": ["python", str(SCRIPTS / "nova_nothingbuta_release_freeze_packet.py")],
    },
    {
        "label": "local preview review page",
        "command": ["python", str(SCRIPTS / "nova_nothingbuta_local_preview_review_page.py")],
    },
    {
        "label": "staging copy proposal",
        "command": ["python", str(SCRIPTS / "nova_nothingbuta_staging_copy_proposal.py")],
    },
    {
        "label": "staging copy dry run",
        "command": ["python", str(SCRIPTS / "nova_nothingbuta_local_staging_copy.py")],
    },
]


def run_command(step: dict) -> dict:
    label = step["label"]
    command = step["command"]

    started_at = datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"[step:start] {label} at {started_at}")
    print(f"[step:command] {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

        finished_at = datetime.now().astimezone().isoformat(timespec="seconds")
        passed = result.returncode == 0

        print(f"[step:end] {label} passed={passed} exit_code={result.returncode} at {finished_at}")

        if result.stdout.strip():
            print(f"[step:stdout] {label}")
            print(result.stdout.strip())

        if result.stderr.strip():
            print(f"[step:stderr] {label}")
            print(result.stderr.strip())

        return {
            "label": label,
            "command": " ".join(command),
            "started_at": started_at,
            "finished_at": finished_at,
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "passed": passed,
        }
    except Exception as exc:
        finished_at = datetime.now().astimezone().isoformat(timespec="seconds")
        print(f"[step:error] {label} {exc}")

        return {
            "label": label,
            "command": " ".join(command),
            "started_at": started_at,
            "finished_at": finished_at,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(exc),
            "passed": False,
        }


def registry_summary() -> dict:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    items = data.get("generated_candidates", [])

    states = {}
    audits = {}
    blocked = []

    for item in items:
        state = str(item.get("state", "missing"))
        audit = str(item.get("audit_status", "missing"))

        states[state] = states.get(state, 0) + 1
        audits[audit] = audits.get(audit, 0) + 1

        if state != "local_preview_ready":
            blocked.append(
                {
                    "name": item.get("name"),
                    "slug": item.get("slug"),
                    "state": state,
                    "audit_status": audit,
                    "audit_problems": item.get("audit_problems", []),
                }
            )

    return {
        "items": len(items),
        "states": states,
        "audits": audits,
        "blocked": blocked,
    }


def write_report(results: list[dict], summary: dict) -> None:
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    lines = [
        "# NothingButA Safe Autopilot Check",
        "",
        f"Generated: {now}",
        "",
        "## Safety Gates",
        "",
        "- Commit allowed: false",
        "- Push allowed: false",
        "- Publish allowed: false",
        "- GitHub Pages changes: false",
        "- Analytics: false",
        "- Ads: false",
        "- Affiliate links: false",
        "- Lead capture: false",
        "- Outreach: false",
        "",
        "## Registry Summary",
        "",
        f"- Items: {summary['items']}",
        f"- States: `{summary['states']}`",
        f"- Audits: `{summary['audits']}`",
        "",
        "## Blocked Items",
        "",
    ]

    if not summary["blocked"]:
        lines.append("- None")
    else:
        for item in summary["blocked"]:
            lines.append(
                f"- {item['name']} / `{item['slug']}` / {item['state']} / {item['audit_status']} / {item['audit_problems']}"
            )

    lines.extend(["", "## Step Results", ""])

    for result in results:
        lines.extend(
            [
                f"### {result['label']}",
                "",
                f"- Passed: {result['passed']}",
                f"- Exit code: {result['exit_code']}",
                f"- Started: {result['started_at']}",
                f"- Finished: {result['finished_at']}",
                f"- Command: `{result['command']}`",
                "",
                "stdout:",
                "",
                "```text",
                result["stdout"] or "(empty)",
                "```",
                "",
                "stderr:",
                "",
                "```text",
                result["stderr"] or "(empty)",
                "```",
                "",
            ]
        )

    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    print("NOTHINGBUTA SAFE AUTOPILOT CHECK")
    print("[autopilot] starting labeled local-only chain")

    results = [run_command(step) for step in COMMANDS]
    summary = registry_summary()
    write_report(results, summary)

    all_passed = all(result["passed"] for result in results)

    print("[autopilot] finished")
    print(f"passed: {all_passed}")
    print(f"report: {REPORT}")
    print(f"items: {summary['items']}")
    print(f"states: {summary['states']}")
    print(f"audits: {summary['audits']}")
    print("blocked:")

    for item in summary["blocked"]:
        print(f"- {item['name']} | {item['slug']} | {item['audit_problems']}")

    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
'''


def backup_file(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak-verbose-step-logging-{stamp}")
    shutil.copy2(path, backup_path)
    return backup_path


def compile_file(path: Path) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )

    if result.stdout.strip():
        print(result.stdout)

    if result.stderr.strip():
        print(result.stderr)

    return result.returncode == 0


def run_autopilot_once() -> bool:
    result = subprocess.run(
        [sys.executable, str(AUTOPILOT_PATH)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )

    print(result.stdout)

    if result.stderr.strip():
        print(result.stderr)

    return result.returncode == 0


def main() -> None:
    if not AUTOPILOT_PATH.exists():
        logging.error("Missing autopilot file: %s", AUTOPILOT_PATH)
        raise SystemExit(1)

    backup_path = backup_file(AUTOPILOT_PATH)
    AUTOPILOT_PATH.write_text(AUTOPILOT_SOURCE, encoding="utf-8")

    compile_ok = compile_file(AUTOPILOT_PATH)
    run_ok = run_autopilot_once() if compile_ok else False

    print("NOTHINGBUTA VERBOSE AUTOPILOT LOGGING PATCH")
    print(f"backup: {backup_path}")
    print(f"compile_ok: {compile_ok}")
    print(f"run_ok: {run_ok}")

    if not compile_ok or not run_ok:
        logging.error("Patch failed. Restore backup before continuing.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()