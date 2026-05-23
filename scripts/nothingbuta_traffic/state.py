from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrafficPaths:
    root: Path
    inbox: Path
    processed: Path
    repo_docs: Path
    proof_json: Path
    proof_md: Path


def build_paths(root: Path) -> TrafficPaths:
    return TrafficPaths(
        root=root,
        inbox=root / "data" / "nothingbuta_traffic_inbox",
        processed=root / "data" / "nothingbuta_traffic_processed",
        repo_docs=root / "nothingbuta" / "github" / "nothingbuta" / "docs",
        proof_json=root / "data" / "nothingbuta_traffic_intelligence_v2.json",
        proof_md=root / "reports" / "nothingbuta-traffic-intelligence-v2.md",
    )
