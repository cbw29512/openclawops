from __future__ import annotations

import logging
import re
from pathlib import Path
from urllib.parse import urlparse


logger = logging.getLogger(__name__)


def slug_from_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        path = parsed.path.strip("/")

        if not path:
            return "home"

        match = re.search(r"(?:^|/)nothingbuta(?:/([^/]+))?/?$", path)

        if match:
            return match.group(1) or "home"

        parts = path.split("/")
        return parts[-1] if parts[-1] else "home"

    except Exception as exc:
        logger.exception("Failed to parse slug from URL")
        raise RuntimeError("Failed to parse slug from URL") from exc


def known_slugs(repo_docs: Path) -> set[str]:
    try:
        slugs = {"home"}

        if not repo_docs.exists():
            return slugs

        for child in repo_docs.iterdir():
            if child.is_dir() and (child / "index.html").exists():
                slugs.add(child.name)

        return slugs

    except Exception as exc:
        logger.exception("Failed to load known slugs")
        raise RuntimeError("Failed to load known slugs") from exc
