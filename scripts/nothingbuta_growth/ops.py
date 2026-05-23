from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


def run_python_script(script_path: Path, cwd: Path) -> dict:
    try:
        if not script_path.exists():
            raise RuntimeError(f"Missing script: {script_path}")

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=180,
        )

        return {
            "script": str(script_path),
            "returncode": result.returncode,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
        }

    except Exception as exc:
        logger.exception("Failed to run script: %s", script_path)
        raise RuntimeError(f"Failed to run script: {script_path}") from exc


def load_json(path: Path) -> Any:
    try:
        if not path.exists():
            raise RuntimeError(f"Missing JSON file: {path}")

        return json.loads(path.read_text(encoding="utf-8"))

    except Exception as exc:
        logger.exception("Failed to load JSON: %s", path)
        raise RuntimeError(f"Failed to load JSON: {path}") from exc


def git_snapshot(repo: Path) -> dict:
    try:
        if not repo.exists():
            return {"status": "repo_missing", "repo": str(repo)}

        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(repo),
            text=True,
            capture_output=True,
            timeout=30,
        )

        log = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            cwd=str(repo),
            text=True,
            capture_output=True,
            timeout=30,
        )

        return {
            "repo": str(repo),
            "status_short": status.stdout.strip(),
            "status_returncode": status.returncode,
            "recent_commits": log.stdout.strip().splitlines(),
            "log_returncode": log.returncode,
        }

    except Exception as exc:
        logger.exception("Failed to create git snapshot")
        return {"status": "git_snapshot_failed", "error": str(exc)}
