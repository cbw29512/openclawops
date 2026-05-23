from __future__ import annotations

import json
import logging
import re

from .models import PageOptimizationConfig, RelatedTool


logger = logging.getLogger(__name__)


def replace_meta_description(html: str, description: str) -> tuple[str, bool]:
    try:
        pattern = re.compile(
            r'<meta\s+name=["\']description["\']\s+content=["\'][^"\']*["\']\s*/?>',
            flags=re.IGNORECASE,
        )
        replacement = f'<meta name="description" content="{description}">'

        if pattern.search(html):
            return pattern.sub(replacement, html, count=1), True

        return re.sub(r"</head>", f"  {replacement}\n</head>", html, count=1, flags=re.IGNORECASE), True
    except Exception as exc:
        logger.exception("Failed to replace meta description")
        raise RuntimeError("Failed to replace meta description") from exc


def inject_structured_data(html: str, config: PageOptimizationConfig) -> tuple[str, bool]:
    try:
        if config.schema_marker in html:
            return html, False

        data = {
            "@context": "https://schema.org",
            "@type": "WebApplication",
            "name": config.app_name,
            "url": config.app_url,
            "applicationCategory": config.application_category,
            "operatingSystem": "Any",
            "description": config.new_meta_description,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        }
        block = (
            f'<script type="application/ld+json" id="{config.schema_marker}">\n'
            f"{json.dumps(data, indent=2)}\n"
            "</script>"
        )

        return re.sub(r"</head>", block + "\n</head>", html, count=1, flags=re.IGNORECASE), True
    except Exception as exc:
        logger.exception("Failed to inject structured data")
        raise RuntimeError("Failed to inject structured data") from exc


def build_related_cards(tools: list[RelatedTool]) -> str:
    try:
        cards = []
        for tool in tools:
            cards.append(
                f"""
      <a class="nba-related-card" href="../{tool.slug}/">
        <strong>{tool.name}</strong>
        <span>{tool.why}</span>
      </a>
""".rstrip()
            )
        return "\n".join(cards)
    except Exception as exc:
        logger.exception("Failed to build related cards")
        raise RuntimeError("Failed to build related cards") from exc


def build_content_section(config: PageOptimizationConfig) -> str:
    try:
        related_cards = build_related_cards(config.related_tools)

        return f"""
<section class="nba-growth-section" id="{config.content_marker}" aria-labelledby="{config.section_label}">
  <style>
    .nba-growth-section {{
      margin: 1.5rem auto 2rem;
      padding: 1.2rem;
      border: 1px solid rgba(15, 23, 42, 0.12);
      border-radius: 24px;
      background: rgba(255,255,255,0.94);
      box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
    }}
    .nba-growth-section h2 {{ margin: 0 0 0.7rem; font-size: clamp(1.35rem, 3vw, 2rem); }}
    .nba-growth-section h3 {{ margin: 1rem 0 0.4rem; font-size: 1.05rem; }}
    .nba-growth-section p {{ color: #475569; line-height: 1.65; margin: 0.35rem 0; }}
    .nba-related-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 0.75rem; margin-top: 0.85rem; }}
    .nba-related-card {{ display: grid; gap: 0.35rem; padding: 0.85rem; border: 1px solid rgba(15, 23, 42, 0.12); border-radius: 16px; background: rgba(248, 250, 252, 0.92); text-decoration: none; color: inherit; }}
    .nba-related-card span {{ color: #475569; line-height: 1.45; }}
  </style>

  <h2 id="{config.section_label}">{config.section_heading}</h2>
  <h3>{config.how_to_heading}</h3>
  <p>{config.how_to_body}</p>
  <h3>{config.result_heading}</h3>
  <p>{config.result_body}</p>
  <h3>{config.next_heading}</h3>
  <p>{config.next_body}</p>
  <h3>Related tools</h3>
  <div class="nba-related-grid">
{related_cards}
  </div>
</section>
""".strip()
    except Exception as exc:
        logger.exception("Failed to build content section")
        raise RuntimeError("Failed to build content section") from exc


def inject_content_section(html: str, config: PageOptimizationConfig) -> tuple[str, bool]:
    try:
        if config.content_marker in html:
            return html, False

        section = build_content_section(config)

        if re.search(r"</main>", html, flags=re.IGNORECASE):
            return re.sub(r"</main>", section + "\n</main>", html, count=1, flags=re.IGNORECASE), True

        return re.sub(r"</body>", section + "\n</body>", html, count=1, flags=re.IGNORECASE), True
    except Exception as exc:
        logger.exception("Failed to inject content section")
        raise RuntimeError("Failed to inject content section") from exc
