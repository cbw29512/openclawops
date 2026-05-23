from pathlib import Path


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
LEGACY_PATH = ROOT / "scripts" / "nothingbuta_factory" / "legacy_factory.py"
CATALOG_PATH = ROOT / "scripts" / "nothingbuta_factory" / "renderer_catalog_v2.py"

legacy = LEGACY_PATH.read_text(encoding="utf-8")
catalog = CATALOG_PATH.read_text(encoding="utf-8")

anchor = 'document.getElementById("out").innerHTML = html ||'

print("legacy_pack2_marker:", "RENDERER_EXPANSION_PACK_2_FORMULAS" in legacy)
print("catalog_pack2_marker:", "RENDERER_EXPANSION_PACK_2_CONFIGS" in catalog)
print("formula_anchor_present:", anchor in legacy)