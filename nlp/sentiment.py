"""
nlp/sentiment.py
VADER-based sentiment analysis with custom negation handling.
"""
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

_NEGATION_WORDS = {
    "not", "no", "never", "none", "n't", "hardly", "scarcely", "barely",
    "without", "neither", "nor",
}


def _apply_negation(text: str, compound: float) -> float:
    tokens = re.findall(r"\b\w+'?\w*\b", text.lower())
    if any(t in _NEGATION_WORDS for t in tokens):
        return compound * 0.85
    return compound


def analyze(text: str) -> dict:
    scores = _analyzer.polarity_scores(text)
    scores["compound"] = _apply_negation(text, scores["compound"])
    c = scores["compound"]
    label = "Positive" if c > 0.2 else ("Negative" if c < -0.2 else "Neutral")
    return {"label": label, "scores": scores}
