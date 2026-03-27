"""
nlp/aspect_sentiment.py
Aspect-Based Sentiment Analysis

Splits each review into sentences, maps sentences to product aspects via
keyword matching, then runs VADER on each matched sentence.

Aspects: Quality, Delivery, Value, Performance, Battery, Camera, Display, Design, Service
"""

import re
import nltk

nltk.download("punkt",     quiet=True)
nltk.download("punkt_tab", quiet=True)

from nltk.tokenize import sent_tokenize
from nlp.sentiment import analyze

# ── Aspect keyword map ────────────────────────────────────────────────────────
ASPECTS = {
    "Quality": [
        "quality", "build", "material", "durable", "durability", "sturdy",
        "solid", "flimsy", "premium", "well made", "poorly made", "cheap feel",
        "good quality", "bad quality", "excellent quality", "poor quality",
        "well built", "feels cheap", "feels premium",
    ],
    "Delivery": [
        "delivery", "shipping", "shipped", "package", "packaging", "arrived",
        "dispatch", "courier", "received", "deliver", "late", "on time",
        "damaged", "packed", "seal", "box", "transit",
    ],
    "Value": [
        "price", "value", "worth", "expensive", "cheap", "cost", "money",
        "affordable", "overpriced", "budget", "deal", "waste of money",
        "value for money", "not worth",
    ],
    "Performance": [
        "performance", "speed", "fast", "slow", "works", "working", "function",
        "efficient", "powerful", "lag", "smooth", "hang", "crash", "response",
        "perform", "excellent performance", "poor performance",
    ],
    "Battery": [
        "battery", "charge", "charging", "backup", "drain", "power",
        "standby", "discharge", "long battery", "battery life",
    ],
    "Camera": [
        "camera", "photo", "picture", "image", "selfie", "video",
        "megapixel", "photography", "shoot", "capture", "lens", "zoom",
    ],
    "Display": [
        "display", "screen", "brightness", "resolution", "colour", "color",
        "bright", "vivid", "amoled", "lcd", "refresh", "hd", "4k",
    ],
    "Design": [
        "design", "look", "looks", "finish", "appearance", "slim",
        "lightweight", "thin", "heavy", "beautiful", "stylish", "sleek",
        "attractive", "ugly",
    ],
    "Service": [
        "service", "support", "seller", "return", "refund", "warranty",
        "replacement", "exchange", "customer care", "after sales",
    ],
}


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_aspects(reviews: list) -> dict:
    """
    Analyze sentiment per aspect across a list of genuine review strings.

    Returns:
        {
          "Quality": {
              "positive": int, "neutral": int, "negative": int,
              "total": int, "avg_compound": float, "verdict": str,
              "samples": [str, ...]   # up to 3 example sentences
          },
          ...   # only aspects that were mentioned at least once
        }
    """
    aspect_data = {asp: {"scores": [], "samples": []} for asp in ASPECTS}

    for review_text in reviews:
        # Split into sentences
        try:
            sentences = sent_tokenize(str(review_text))
        except Exception:
            sentences = [s.strip() for s in re.split(r"[.!?]+", str(review_text))
                         if len(s.strip()) > 4]

        for sentence in sentences:
            low = sentence.lower()
            for aspect, keywords in ASPECTS.items():
                if any(kw in low for kw in keywords):
                    result = analyze(sentence)
                    aspect_data[aspect]["scores"].append(result)
                    if len(aspect_data[aspect]["samples"]) < 3:
                        aspect_data[aspect]["samples"].append(sentence.strip())

    output = {}
    for aspect, data in aspect_data.items():
        scores = data["scores"]
        if not scores:
            continue  # skip aspects with zero mentions

        pos   = sum(1 for s in scores if s["label"] == "Positive")
        neu   = sum(1 for s in scores if s["label"] == "Neutral")
        neg   = sum(1 for s in scores if s["label"] == "Negative")
        total = len(scores)
        avg_c = sum(s["scores"]["compound"] for s in scores) / total

        if avg_c >= 0.05:
            verdict = "Positive"
        elif avg_c <= -0.05:
            verdict = "Negative"
        else:
            verdict = "Neutral"

        output[aspect] = {
            "positive":    pos,
            "neutral":     neu,
            "negative":    neg,
            "total":       total,
            "avg_compound": round(avg_c, 4),
            "verdict":     verdict,
            "samples":     data["samples"],
        }

    return output
