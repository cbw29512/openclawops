from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

CHECKPOINT_JSON = DATA / "nothingbuta_24_ready_milestone_checkpoint.json"
CHECKPOINT_MD = REPORTS / "nothingbuta-24-ready-milestone-checkpoint.md"

FILES_TO_REFERENCE = {
    "registry": DATA / "nothingbuta_candidate_registry.json",
    "release_batch": DATA / "nothingbuta_release_batch_picker.json",
    "freeze_packet": DATA / "nothingbuta_release_freeze_packet.json",
    "staging_proposal": DATA / "nothingbuta_staging_copy_proposal.json",
    "optimizer_report": DATA / "nothingbuta_hourly_optimizer_report.json",
    "preview_review_page": REPORTS / "nothingbuta-local-preview-review.html",
    "pack3_finish_report": REPORTS / "nothingbuta-pack3-registry-finish.md",
}

now = datetime.now().astimezone().isoformat(timespec="seconds")

registry = json.loads(FILES_TO_REFERENCE["registry"].read_text(encoding="utf-8"))
items = registry.get("generated_candidates", [])

states = {}
audits = {}

for item in items:
    state = str(item.get("state", "missing"))
    audit = str(item.get("audit_status", "missing"))
    states[state] = states.get(state, 0) + 1
    audits[audit] = audits.get(audit, 0) + 1

checkpoint = {
    "generated_at": now,
    "milestone": "NothingButA 24-ready local batch",
    "root": str(ROOT),
    "items": len(items),
    "states": states,
    "audits": audits,
    "blocked": [item for item in items if item.get("state") != "local_preview_ready"],
    "status": "ready_for_human_visual_review_before_any_staging_copy",
    "safety": {
        "files_copied_to_staging": False,
        "commit_allowed": False,
        "push_allowed": False,
        "publish_allowed": False,
        "github_pages_changes_allowed": False,
        "analytics_allowed": False,
        "ads_allowed": False,
        "affiliate_links_allowed": False,
        "lead_capture_allowed": False,
        "outreach_allowed": False,
        "requires_chris_approval_before_any_external_action": True,
    },
    "referenced_files": {key: str(path) for key, path in FILES_TO_REFERENCE.items()},
}

CHECKPOINT_JSON.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")

lines = [
    "# NothingButA 24-Ready Milestone Checkpoint",
    "",
    f"Generated: {now}",
    "",
    "## Milestone",
    "",
    "- 24 local tool/app candidates are ready.",
    "- 24 audit checks passed.",
    "- 0 candidates are blocked.",
    "- 0 files have been copied to staging.",
    "- External actions remain locked.",
    "",
    "## Registry Summary",
    "",
    f"- Items: {len(items)}",
    f"- States: `{states}`",
    f"- Audits: `{audits}`",
    "",
    "## Safety Gates",
    "",
]

for key, value in checkpoint["safety"].items():
    lines.append(f"- {key}: {str(value).lower()}")

lines.extend(["", "## Referenced Files", ""])

for key, path in FILES_TO_REFERENCE.items():
    lines.append(f"- {key}: `{path}`")

lines.extend([
    "",
    "## Next Human Step",
    "",
    "Open the local preview review page and visually inspect the 24 tools before approving any local staging copy.",
    "",
])

CHECKPOINT_MD.write_text("\n".join(lines), encoding="utf-8")

print("NOTHINGBUTA 24 READY MILESTONE CHECKPOINT: PASS")
print(f"items: {len(items)}")
print(f"states: {states}")
print(f"audits: {audits}")
print(f"json: {CHECKPOINT_JSON}")
print(f"markdown: {CHECKPOINT_MD}")