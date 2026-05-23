from __future__ import annotations


def classify(item: dict) -> dict:
    impressions = int(item.get("impressions", 0))
    clicks = int(item.get("clicks", 0))
    ctr = float(item.get("ctr", 0.0))
    position = float(item.get("position", 0.0))

    opportunity_type = "watch"
    recommendation = "Keep watching until more search data accumulates."
    score = 0

    if impressions >= 50 and ctr < 0.02:
        opportunity_type = "high_impressions_low_ctr"
        recommendation = "Review title/meta angle and page promise before changing content."
        score += 5

    if 5 <= position <= 20 and impressions > 0:
        opportunity_type = "striking_distance"
        recommendation = "Consider strengthening helpful content and internal links."
        score += 4

    if impressions >= 10 and clicks == 0:
        opportunity_type = "visible_but_no_clicks"
        recommendation = "Investigate whether the search snippet is compelling enough."
        score += 3

    if clicks >= 25:
        score += 2

    monetization = "not_ready"
    if clicks >= 50 or impressions >= 500:
        monetization = "candidate_review_only"

    return {
        **item,
        "traffic_score": score,
        "opportunity_type": opportunity_type,
        "recommendation": recommendation,
        "monetization_readiness": monetization,
    }
