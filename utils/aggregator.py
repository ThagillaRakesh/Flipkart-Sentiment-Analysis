"""
utils/aggregator.py
Aggregate per-review sentiment results into a summary.
"""
import statistics
from nlp.sentiment import analyze


def aggregate(genuine_reviews: list, fake_reviews: list, product_rating=None) -> dict:
    """
    Run sentiment analysis on genuine reviews and produce a summary.

    Args:
        genuine_reviews:  list of review strings (fake already removed)
        fake_reviews:     list of fake review strings (for count only)
        product_rating:   overall star rating from the product page (float | None)

    Returns:
        {
            "positive": int,
            "negative": int,
            "neutral":  int,
            "fake":     int,
            "total":    int,
            "overall":  "Positive" | "Neutral" | "Negative",
            "action":   str,
            "avg_compound": float,
            "avg_scores": {"pos", "neu", "neg", "compound"},
            "analyzed": [{"text", "label", "scores"}],  # per-review results
        }
    """
    analyzed = []
    pos = neg = neu = 0

    for text in genuine_reviews:
        result = analyze(text)
        analyzed.append({"text": text, **result})
        if result["label"] == "Positive":
            pos += 1
        elif result["label"] == "Negative":
            neg += 1
        else:
            neu += 1

    total_genuine = len(genuine_reviews)
    avg_compound = (
        statistics.mean([r["scores"]["compound"] for r in analyzed])
        if analyzed else 0.0
    )
    avg_scores = {
        "pos":      statistics.mean([r["scores"]["pos"] for r in analyzed]) if analyzed else 0.0,
        "neu":      statistics.mean([r["scores"]["neu"] for r in analyzed]) if analyzed else 0.0,
        "neg":      statistics.mean([r["scores"]["neg"] for r in analyzed]) if analyzed else 0.0,
        "compound": avg_compound,
    }

    # Decide overall verdict: prefer star rating when available
    if product_rating is not None:
        if product_rating >= 4.5:
            overall, action = "Positive", "Buy the product"
        elif product_rating >= 3.9:
            overall, action = "Neutral", "Check more details before buying"
        else:
            overall, action = "Negative", "Avoid this product"
    elif analyzed:
        if avg_compound >= 0.2:
            overall, action = "Positive", "Buy the product"
        elif avg_compound >= -0.2:
            overall, action = "Neutral", "Check more details before buying"
        else:
            overall, action = "Negative", "Avoid this product"
    else:
        overall, action = "Neutral", "Not enough data to decide"

    return {
        "positive":    pos,
        "negative":    neg,
        "neutral":     neu,
        "fake":        len(fake_reviews),
        "total":       total_genuine + len(fake_reviews),
        "overall":     overall,
        "action":      action,
        "avg_compound": round(avg_compound, 4),
        "avg_scores":  {k: round(v, 4) for k, v in avg_scores.items()},
        "analyzed":    analyzed,
    }
