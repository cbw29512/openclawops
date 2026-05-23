from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GrowthPaths:
    root: Path
    repo: Path
    monitor_script: Path
    seo_script: Path
    monitor_json: Path
    seo_json: Path
    proof_json: Path
    proof_md: Path
    task_log: Path


def build_paths(root: Path) -> GrowthPaths:
    repo = root / "nothingbuta" / "github" / "nothingbuta"

    return GrowthPaths(
        root=root,
        repo=repo,
        monitor_script=root / "scripts" / "nova_nothingbuta_live_quality_monitor.py",
        seo_script=root / "scripts" / "nova_nothingbuta_seo_growth_research_report.py",
        monitor_json=root / "data" / "nothingbuta_live_quality_monitor.json",
        seo_json=root / "data" / "nothingbuta_seo_growth_research_report.json",
        proof_json=root / "data" / "nothingbuta_growth_autopilot_v1.json",
        proof_md=root / "reports" / "nothingbuta-growth-autopilot-v1.md",
        task_log=root / "reports" / "nothingbuta-growth-autopilot-task.log",
    )
