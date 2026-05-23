from __future__ import annotations

import ast
import json
import logging
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPTS_DIR = ROOT / "scripts"
MODULE_DIR = SCRIPTS_DIR / "nothingbuta_factory"
DATA_DIR = ROOT / "data"

LEGACY_PATH = MODULE_DIR / "legacy_factory.py"
CATALOG_PATH = MODULE_DIR / "renderer_catalog_v2.py"
ENTRYPOINT_PATH = SCRIPTS_DIR / "nova_nothingbuta_local_factory_loop.py"
REGISTRY_PATH = DATA_DIR / "nothingbuta_candidate_registry.json"

REPORTS_PATH = MODULE_DIR / "reports_v2.py"
AUDIT_PATH = MODULE_DIR / "audit_rules_v2.py"
SPECIALS_PATH = MODULE_DIR / "renderer_specials_v2.py"

PACK_FORMULA_MARKER = "RENDERER_EXPANSION_PACK_2_FORMULAS"
PACK_CONFIG_MARKER = "RENDERER_EXPANSION_PACK_2_CONFIGS"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


PACK2_CONFIGS: dict[str, dict[str, Any]] = {
    "roi-calculator": {
        "name": "Simple ROI Calculator",
        "description": "Estimate return on investment from cost and return values.",
        "category": "business",
        "formula": "roi",
        "inputs": [
            ["cost", "Initial cost", "What you spent or invested", "1000"],
            ["return", "Return value", "What came back from the investment", "1250"],
        ],
        "faq": [
            ["What does ROI mean?", "ROI estimates return on investment by comparing gain against cost."],
            ["Is this financial advice?", "No. This is an estimate-only planning tool, not financial advice."],
        ],
    },
    "recipe-scale-calculator": {
        "name": "Recipe Scale Calculator",
        "description": "Scale an ingredient amount when changing recipe servings.",
        "category": "food",
        "formula": "recipescale",
        "inputs": [
            ["original", "Original servings", "Servings the recipe currently makes", "4"],
            ["desired", "Desired servings", "Servings you want to make", "6"],
            ["quantity", "Original ingredient quantity", "Amount listed in the original recipe", "2"],
        ],
        "faq": [
            ["How does recipe scaling work?", "The calculator multiplies the original quantity by desired servings divided by original servings."],
            ["Can I use any unit?", "Yes. Keep the same unit before and after scaling, such as cups, grams, or tablespoons."],
        ],
    },
    "paint-coverage-calculator": {
        "name": "Paint Coverage Calculator",
        "description": "Estimate paintable wall area and gallons needed for a simple room project.",
        "category": "home",
        "formula": "paintcoverage",
        "inputs": [
            ["width", "Total wall width", "Combined wall width in feet", "40"],
            ["height", "Wall height", "Wall height in feet", "8"],
            ["doors", "Doors", "Number of standard doors to subtract", "2"],
            ["windows", "Windows", "Number of standard windows to subtract", "4"],
            ["coats", "Coats", "Number of paint coats", "2"],
            ["coverage", "Coverage per gallon", "Square feet covered by one gallon", "350"],
        ],
        "faq": [
            ["How much area does this subtract for doors and windows?", "It estimates 21 square feet per door and 15 square feet per window."],
            ["Is this exact?", "No. Paint coverage varies by surface, product, color change, and application method."],
        ],
    },
    "flooring-calculator": {
        "name": "Flooring Calculator",
        "description": "Estimate flooring square footage, waste allowance, and box count.",
        "category": "home",
        "formula": "flooring",
        "inputs": [
            ["length", "Room length", "Length in feet", "12"],
            ["width", "Room width", "Width in feet", "10"],
            ["waste", "Waste allowance", "Extra percentage for cuts and mistakes", "10"],
            ["box", "Coverage per box", "Square feet covered by one box", "20"],
        ],
        "faq": [
            ["Why include waste?", "Most flooring projects need extra material for cuts, layout, and mistakes."],
            ["Is this exact?", "No. Confirm measurements and product coverage before buying materials."],
        ],
    },
    "concrete-calculator": {
        "name": "Concrete Calculator",
        "description": "Estimate concrete volume and bag count for a simple slab.",
        "category": "home",
        "formula": "concrete",
        "inputs": [
            ["length", "Slab length", "Length in feet", "10"],
            ["width", "Slab width", "Width in feet", "8"],
            ["depth", "Slab depth", "Depth in inches", "4"],
            ["waste", "Waste allowance", "Extra percentage for spill, uneven ground, and margin", "10"],
            ["yield", "Bag yield", "Cubic feet per bag", "0.6"],
        ],
        "faq": [
            ["Why is depth in inches?", "Concrete slab depth is often planned in inches while length and width are measured in feet."],
            ["Is this structural advice?", "No. This is an estimate-only material calculator, not engineering or construction advice."],
        ],
    },
}


PACK2_JS_ESCAPED = '''
        // === RENDERER_EXPANSION_PACK_2_FORMULAS START ===
        if (FORMULA === "roi") {{
          const cost = num("cost");
          const returned = num("return");
          if (cost <= 0) {{
            html = '<div class="warn">Enter a cost above zero.</div>';
          }} else {{
            const net = returned - cost;
            const roi = (net / cost) * 100;
            html = block(money(net), "Estimated net return") + block(`${{roi.toFixed(2)}}%`, "Estimated ROI") + block(money(returned), "Return value") + block(money(cost), "Initial cost");
          }}
        }}

        if (FORMULA === "recipescale") {{
          const original = num("original");
          const desired = num("desired");
          const quantity = num("quantity");
          if (original <= 0 || desired <= 0) {{
            html = '<div class="warn">Enter original and desired servings above zero.</div>';
          }} else {{
            const factor = desired / original;
            const scaled = quantity * factor;
            html = block(scaled.toLocaleString(undefined, {{ maximumFractionDigits: 3 }}), "Scaled ingredient quantity") + block(`${{factor.toFixed(2)}}x`, "Scale factor") + block(original.toLocaleString(), "Original servings") + block(desired.toLocaleString(), "Desired servings");
          }}
        }}

        if (FORMULA === "paintcoverage") {{
          const wallArea = Math.max(num("width") * num("height"), 0);
          const subtractArea = (num("doors") * 21) + (num("windows") * 15);
          const paintableArea = Math.max(wallArea - subtractArea, 0);
          const totalCoverage = paintableArea * Math.max(num("coats"), 1);
          const gallons = num("coverage") > 0 ? totalCoverage / num("coverage") : 0;
          html = block(`${{paintableArea.toLocaleString()}} sq ft`, "Estimated paintable area") + block(`${{totalCoverage.toLocaleString()}} sq ft`, "Area after coats") + block(gallons.toFixed(2), "Estimated gallons") + block(Math.ceil(gallons).toLocaleString(), "Whole gallons to consider");
        }}

        if (FORMULA === "flooring") {{
          const area = Math.max(num("length") * num("width"), 0);
          const withWaste = area * (1 + Math.max(num("waste"), 0) / 100);
          const boxes = num("box") > 0 ? Math.ceil(withWaste / num("box")) : 0;
          html = block(`${{area.toLocaleString()}} sq ft`, "Room area") + block(`${{withWaste.toFixed(2)}} sq ft`, "Area with waste allowance") + block(boxes.toLocaleString(), "Estimated boxes") + block(`${{num("waste").toFixed(1)}}%`, "Waste allowance");
        }}

        if (FORMULA === "concrete") {{
          const cubicFeet = Math.max(num("length") * num("width") * (num("depth") / 12), 0);
          const withWaste = cubicFeet * (1 + Math.max(num("waste"), 0) / 100);
          const cubicYards = withWaste / 27;
          const bags = num("yield") > 0 ? Math.ceil(withWaste / num("yield")) : 0;
          html = block(`${{withWaste.toFixed(2)}} cu ft`, "Estimated concrete volume") + block(`${{cubicYards.toFixed(3)}} cu yd`, "Estimated cubic yards") + block(bags.toLocaleString(), "Estimated bags") + block(`${{num("depth").toFixed(1)}} in`, "Slab depth");
        }}
        // === RENDERER_EXPANSION_PACK_2_FORMULAS END ===
'''


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


def validate_existing_state() -> None:
    sys.path.insert(0, str(SCRIPTS_DIR))
    from nothingbuta_factory.renderer_catalog_v2 import TOOL_CONFIGS

    legacy_source = LEGACY_PATH.read_text(encoding="utf-8")
    catalog_source = CATALOG_PATH.read_text(encoding="utf-8")

    if PACK_FORMULA_MARKER in legacy_source:
        logging.error("Pack 2 formula marker already exists. Stop.")
        raise SystemExit(1)

    if PACK_CONFIG_MARKER in catalog_source:
        logging.error("Pack 2 config marker already exists. Stop.")
        raise SystemExit(1)

    if not isinstance(TOOL_CONFIGS, dict) or not TOOL_CONFIGS:
        logging.error("TOOL_CONFIGS is missing or empty. Stop.")
        raise SystemExit(1)

    sample = next(iter(TOOL_CONFIGS.values()))
    required_keys = {"name", "description", "category", "formula", "inputs", "faq"}
    missing = sorted(required_keys - set(sample.keys()))
    if missing:
        logging.error("Catalog sample missing keys: %s", missing)
        raise SystemExit(1)

    duplicates = sorted(slug for slug in PACK2_CONFIGS if slug in TOOL_CONFIGS)
    if duplicates:
        logging.error("Pack 2 slug(s) already in catalog: %s", duplicates)
        raise SystemExit(1)


def build_catalog_source(source: str) -> str:
    append_block = [
        "",
        "",
        "# === RENDERER_EXPANSION_PACK_2_CONFIGS START ===",
        "TOOL_CONFIGS.update(",
        json.dumps(PACK2_CONFIGS, indent=4),
        ")",
        "# === RENDERER_EXPANSION_PACK_2_CONFIGS END ===",
        "",
    ]
    return source.rstrip() + "\n" + "\n".join(append_block)


def build_legacy_source(source: str) -> str:
    anchor = '        document.getElementById("out").innerHTML = html || \'<div class="warn">This tool needs a stricter formula before it can pass.</div>\';'

    if anchor not in source:
        logging.error("Formula insertion anchor not found. Stop.")
        raise SystemExit(1)

    return source.replace(anchor, PACK2_JS_ESCAPED.rstrip() + "\n\n" + anchor, 1)


def preflight_parse(path_label: str, source: str) -> None:
    try:
        ast.parse(source)
    except SyntaxError as exc:
        logging.error("Preflight parse failed for %s: %s", path_label, exc)
        raise SystemExit(1) from exc


def run_factory() -> bool:
    result = subprocess.run(
        [sys.executable, str(ENTRYPOINT_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )

    print(result.stdout)
    if result.stderr.strip():
        print(result.stderr)

    return result.returncode == 0 and "PASS" in result.stdout


def registry_summary() -> dict[str, Any]:
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    items = data.get("generated_candidates", [])

    states: dict[str, int] = {}
    audits: dict[str, int] = {}

    for item in items:
        state = str(item.get("state", "missing"))
        audit = str(item.get("audit_status", "missing"))
        states[state] = states.get(state, 0) + 1
        audits[audit] = audits.get(audit, 0) + 1

    blocked = [
        {
            "name": item.get("name"),
            "slug": item.get("slug"),
            "state": item.get("state"),
            "audit_status": item.get("audit_status"),
            "audit_problems": item.get("audit_problems"),
        }
        for item in items
        if item.get("state") != "local_preview_ready"
    ]

    return {
        "items": len(items),
        "states": states,
        "audits": audits,
        "blocked": blocked,
    }


def main() -> None:
    validate_existing_state()

    legacy_source = LEGACY_PATH.read_text(encoding="utf-8")
    catalog_source = CATALOG_PATH.read_text(encoding="utf-8")

    patched_legacy = build_legacy_source(legacy_source)
    patched_catalog = build_catalog_source(catalog_source)

    preflight_parse("legacy_factory.py patched source", patched_legacy)
    preflight_parse("renderer_catalog_v2.py patched source", patched_catalog)

    legacy_backup = backup_file(LEGACY_PATH, "renderer-pack2-fixed-formulas")
    catalog_backup = backup_file(CATALOG_PATH, "renderer-pack2-fixed-configs")

    LEGACY_PATH.write_text(patched_legacy, encoding="utf-8")
    CATALOG_PATH.write_text(patched_catalog, encoding="utf-8")

    compile_ok = all(
        [
            compile_file(CATALOG_PATH),
            compile_file(LEGACY_PATH),
            compile_file(REPORTS_PATH),
            compile_file(AUDIT_PATH),
            compile_file(SPECIALS_PATH),
            compile_file(ENTRYPOINT_PATH),
        ]
    )

    factory_ok = False
    if compile_ok:
        factory_ok = run_factory()

    summary = registry_summary()

    print("=== Renderer Pack 2 Validated Set Fixed Result ===")
    print(f"legacy_backup: {legacy_backup}")
    print(f"catalog_backup: {catalog_backup}")
    print(f"compile_ok: {compile_ok}")
    print(f"factory_ok: {factory_ok}")
    print(json.dumps(summary, indent=2))

    if not compile_ok or not factory_ok:
        logging.error("Validation failed. Roll back before continuing.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()