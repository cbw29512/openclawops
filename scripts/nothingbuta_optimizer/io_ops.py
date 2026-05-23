from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path


logger = logging.getLogger(__name__)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.exception("Failed to read file: %s", path)
        raise RuntimeError(f"Failed to read file: {path}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.write_text(text, encoding="utf-8")
    except Exception as exc:
        logger.exception("Failed to write file: %s", path)
        raise RuntimeError(f"Failed to write file: {path}") from exc


def backup_target(target_path: Path, backup_root: Path, target_slug: str, batch_number: str) -> Path:
    try:
        if not target_path.exists():
            raise RuntimeError(f"Missing target page: {target_path}")

        backup_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = backup_root / f"{target_slug}-before-optimization-{batch_number}-{stamp}.html"
        shutil.copy2(target_path, backup_path)
        return backup_path
    except Exception as exc:
        logger.exception("Failed to back up target page")
        raise RuntimeError("Failed to back up target page") from exc
