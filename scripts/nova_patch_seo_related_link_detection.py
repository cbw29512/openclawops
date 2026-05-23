from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path


# Objective:
# Make the SEO Growth Research Report smarter about related links.
#
# State logic:
# - The report already knows which slugs are related.
# - The report currently recommends related links even when they already exist.
# - This patch makes it check the live HTML before adding the recommendation.
#
# This script DOES:
# - back up nova_nothingbuta_seo_growth_research_report.py
# - replace the unconditional related-link recommendation block
# - keep the script report-only
#
# This script DOES NOT:
# - edit public site files
# - commit
# - push
# - publish
# - change GitHub Pages
# - add analytics, ads, affiliate links, lead capture, or outreach


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("nothingbuta_seo_related_link_detection_patch")


ROOT = Path(r"C:\Users\dmchris\OpenClawOps")
SCRIPT_PATH = ROOT / "scripts" / "nova_nothingbuta_seo_growth_research_report.py"


OLD_BLOCK = '''        related = related_slugs(slug)
        if related:
            opportunities.append(
                {
                    "type": "internal_link_cluster",
                    "severity": "medium",
                    "recommendation": f"Add a small related-tools section linking to: {', '.join(related)}.",
                    "why_it_matters": "Relevant tool-to-tool links help users discover adjacent utilities without sending them to the root hub.",
                }
            )
'''


NEW_BLOCK = '''        related = related_slugs(slug)
        if related:
            # Only recommend related links that are actually missing from the page.
            # This prevents the report from repeatedly flagging pages we already improved.
            missing_related = [
                item
                for item in related
                if f"../{item}/" not in html and f"/nothingbuta/{item}/" not in html
            ]

            if missing_related:
                opportunities.append(
                    {
                        "type": "internal_link_cluster",
                        "severity": "medium",
                        "recommendation": f"Add a small related-tools section linking to missing related tools: {', '.join(missing_related)}.",
                        "why_it_matters": "Relevant tool-to-tool links help users discover adjacent utilities without sending them to the root hub.",
                    }
                )
'''


def main() -> int:
    try:
        if not SCRIPT_PATH.exists():
            raise RuntimeError(f"Missing SEO research script: {SCRIPT_PATH}")

        text = SCRIPT_PATH.read_text(encoding="utf-8")

        if "missing_related = [" in text:
            print("NOTHINGBUTA SEO RELATED-LINK DETECTION PATCH: PASS")
            print("already_patched: True")
            print("script:", SCRIPT_PATH)
            return 0

        if OLD_BLOCK not in text:
            raise RuntimeError("Expected old internal_link_cluster block not found. Refusing blind patch.")

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = SCRIPT_PATH.with_suffix(f".py.bak-related-link-detection-{stamp}")
        shutil.copy2(SCRIPT_PATH, backup_path)

        updated = text.replace(OLD_BLOCK, NEW_BLOCK, 1)
        SCRIPT_PATH.write_text(updated, encoding="utf-8")

        print("NOTHINGBUTA SEO RELATED-LINK DETECTION PATCH: PASS")
        print("already_patched: False")
        print("backup:", backup_path)
        print("script:", SCRIPT_PATH)
        return 0

    except Exception as exc:
        logger.exception("Related-link detection patch failed")
        print("NOTHINGBUTA SEO RELATED-LINK DETECTION PATCH: FAILED")
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
