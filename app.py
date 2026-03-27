"""
app.py — Opinion Miner Flask backend
Routes:
  GET  /              → serve index.html
  POST /analyze       → text sentiment analysis (JSON)
  POST /analyze-url   → Flipkart / Amazon URL scrape + analysis (JSON)
"""
import sys
import os

# Make sure sub-packages resolve correctly when run from any directory
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify, url_for

from nlp.preprocessor     import preprocess
from nlp.sentiment        import analyze
from nlp.fake_detector    import filter_reviews, model_info as fake_model_info
from nlp.aspect_sentiment import analyze_aspects
from utils.aggregator     import aggregate
from utils.visualizer     import sentiment_bar_chart, score_bar_chart, wordcloud_chart

app = Flask(__name__)

# Emoji + audio for each sentiment verdict
_SENTIMENT_META = {
    "Positive": {"emoji": "😊", "audio": "positive.wav"},
    "Neutral":  {"emoji": "😐", "audio": "neutral.wav"},
    "Negative": {"emoji": "😞", "audio": "negative.wav"},
}

def _verdict_meta(label: str) -> dict:
    meta = _SENTIMENT_META.get(label, {"emoji": "🤔", "audio": None})
    audio_url = url_for("static", filename=f"audio/{meta['audio']}") if meta["audio"] else None
    return {"emoji": meta["emoji"], "audio_url": audio_url}


# ── /analyze — single text input ─────────────────────────────────────────────

@app.route("/analyze", methods=["POST"])
def analyze_text():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or request.form.get("text", "")).strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    cleaned = preprocess(text)
    result  = analyze(cleaned if cleaned else text)

    meta = _verdict_meta(result["label"])
    return jsonify({
        "label":     result["label"],
        "scores":    result["scores"],
        "emoji":     meta["emoji"],
        "audio_url": meta["audio_url"],
    })


# ── /analyze-url — Flipkart or Amazon URL ────────────────────────────────────

@app.route("/analyze-url", methods=["POST"])
def analyze_url():
    data = request.get_json(silent=True) or {}
    url  = (data.get("url") or request.form.get("url", "")).strip()

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    if "flipkart.com" not in url.lower():
        return jsonify({"error": "Only Flipkart product URLs are supported"}), 400

    # ── Scrape ────────────────────────────────────────────────────────────────
    from scraper.flipkart_scraper import scrape
    platform = "Flipkart"

    scraped = scrape(url)

    if scraped["error"] and not scraped["reviews"]:
        return jsonify({
            "error":    scraped["error"],
            "title":    scraped.get("title"),
            "rating":   scraped.get("rating"),
            "reviews":  [],
            "platform": platform,
        }), 200

    raw_reviews    = scraped["reviews"]   # list of {"text": str, "rating": int|None}
    product_rating = scraped.get("rating")

    # Extract parallel lists
    review_texts   = [r["text"]       for r in raw_reviews]
    review_ratings = [r.get("rating") for r in raw_reviews]

    # ── Fake detection ────────────────────────────────────────────────────────
    genuine, fake_list, fake_details = filter_reviews(review_texts, review_ratings)

    # ── Aggregate sentiment (genuine reviews only) ────────────────────────────
    summary = aggregate(genuine, fake_list, product_rating=product_rating)

    # ── Aspect-based sentiment (genuine reviews only) ─────────────────────────
    aspects = analyze_aspects(genuine)

    # ── Visualizations ────────────────────────────────────────────────────────
    bar_chart = sentiment_bar_chart(
        summary["positive"], summary["neutral"],
        summary["negative"], summary["fake"]
    )
    avg = summary["avg_scores"]
    score_chart = score_bar_chart(avg["pos"], avg["neu"], avg["neg"])

    pos_texts = [r["text"] for r in summary["analyzed"] if r["label"] == "Positive"]
    neg_texts = [r["text"] for r in summary["analyzed"] if r["label"] == "Negative"]
    wc_pos = wordcloud_chart(pos_texts, "Positive")
    wc_neg = wordcloud_chart(neg_texts, "Negative")

    meta = _verdict_meta(summary["overall"])
    return jsonify({
        "platform":      platform,
        "title":         scraped.get("title"),
        "rating":        product_rating,
        "images":        scraped.get("images", []),
        "positive":      summary["positive"],
        "negative":      summary["negative"],
        "neutral":       summary["neutral"],
        "fake":          summary["fake"],
        "total":         summary["total"],
        "overall":       summary["overall"],
        "action":        summary["action"],
        "avg_compound":  summary["avg_compound"],
        "avg_scores":    summary["avg_scores"],
        "aspects":       aspects,
        "reviews":       summary["analyzed"],
        "fake_details":  fake_details,
        "emoji":         meta["emoji"],
        "audio_url":     meta["audio_url"],
        "charts": {
            "bar":      bar_chart,
            "scores":   score_chart,
            "wc_pos":   wc_pos,
            "wc_neg":   wc_neg,
        },
        "error":    scraped.get("error"),
        "svm_info": fake_model_info(),
    })


# ── /model-info — SVM model metadata ─────────────────────────────────────────

@app.route("/model-info")
def model_info_route():
    return jsonify(fake_model_info())


# ── / — serve UI ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
