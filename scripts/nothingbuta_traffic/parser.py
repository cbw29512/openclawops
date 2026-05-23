from __future__ import annotations

import csv
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


URL_HEADERS = ["page", "top pages", "url", "landing page", "pages"]
CLICK_HEADERS = ["clicks", "click"]
IMPRESSION_HEADERS = ["impressions", "impression"]
CTR_HEADERS = ["ctr", "click through rate", "click-through rate"]
POSITION_HEADERS = ["position", "avg position", "average position"]


def norm(value: str) -> str:
    return value.strip().lower().replace("\ufeff", "")


def find_value(row: dict, aliases: list[str]) -> str:
    lowered = {norm(str(key)): value for key, value in row.items()}

    for alias in aliases:
        if alias in lowered:
            return str(lowered[alias]).strip()

    return ""


def parse_int(value: str) -> int:
    try:
        cleaned = value.replace(",", "").strip()
        return int(float(cleaned)) if cleaned else 0
    except Exception:
        return 0


def parse_float(value: str) -> float:
    try:
        cleaned = value.replace(",", "").replace("%", "").strip()
        return float(cleaned) if cleaned else 0.0
    except Exception:
        return 0.0


def parse_ctr(value: str) -> float:
    number = parse_float(value)

    if "%" in value:
        return number / 100

    if number > 1:
        return number / 100

    return number


def read_csv_file(path: Path) -> list[dict]:
    try:
        rows: list[dict] = []

        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)

            for raw in reader:
                url = find_value(raw, URL_HEADERS)
                clicks = parse_int(find_value(raw, CLICK_HEADERS))
                impressions = parse_int(find_value(raw, IMPRESSION_HEADERS))
                ctr = parse_ctr(find_value(raw, CTR_HEADERS))
                position = parse_float(find_value(raw, POSITION_HEADERS))

                if not url:
                    continue

                rows.append(
                    {
                        "source_file": str(path),
                        "url": url,
                        "clicks": clicks,
                        "impressions": impressions,
                        "ctr": ctr,
                        "position": position,
                    }
                )

        return rows

    except Exception as exc:
        logger.exception("Failed to read CSV file: %s", path)
        raise RuntimeError(f"Failed to read CSV file: {path}") from exc


def load_inbox_csvs(inbox: Path) -> tuple[list[dict], list[str]]:
    try:
        inbox.mkdir(parents=True, exist_ok=True)

        records: list[dict] = []
        files = sorted(inbox.glob("*.csv"))

        for file_path in files:
            records.extend(read_csv_file(file_path))

        return records, [str(path) for path in files]

    except Exception as exc:
        logger.exception("Failed to load traffic inbox")
        raise RuntimeError("Failed to load traffic inbox") from exc
