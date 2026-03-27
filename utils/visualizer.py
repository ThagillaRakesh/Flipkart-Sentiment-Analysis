"""
utils/visualizer.py
Generate base64-encoded chart images for embedding in JSON / HTML responses.
"""
import io
import base64
import matplotlib
matplotlib.use("Agg")  # non-interactive backend — no display required
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


_COLORS = {
    "Positive": "#4caf50",
    "Neutral":  "#ff9800",
    "Negative": "#f44336",
    "Fake":     "#9e9e9e",
}


def _fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def sentiment_bar_chart(pos: int, neu: int, neg: int, fake: int = 0) -> str:
    """
    Bar chart showing Positive / Neutral / Negative / Fake counts.
    Returns base64-encoded PNG string.
    """
    labels = ["Positive", "Neutral", "Negative", "Fake"]
    values = [pos, neu, neg, fake]
    colors = [_COLORS[l] for l in labels]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, values, color=colors, edgecolor="white", width=0.5)
    ax.bar_label(bars, padding=3, fontsize=11, fontweight="bold")
    ax.set_ylabel("Review Count", fontsize=11)
    ax.set_title("Sentiment Distribution", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylim(0, max(values) * 1.25 + 1)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=11)
    fig.tight_layout()
    return _fig_to_b64(fig)


def score_bar_chart(pos: float, neu: float, neg: float) -> str:
    """
    Horizontal bar chart of average VADER score components.
    Returns base64-encoded PNG string.
    """
    labels = ["Positive", "Neutral", "Negative"]
    values = [pos, neu, neg]
    colors = [_COLORS[l] for l in labels]

    fig, ax = plt.subplots(figsize=(6, 3))
    bars = ax.barh(labels, values, color=colors, edgecolor="white", height=0.4)
    ax.bar_label(bars, fmt="%.3f", padding=3, fontsize=10)
    ax.set_xlim(0, 1.15)
    ax.set_xlabel("Average Score", fontsize=10)
    ax.set_title("Average VADER Score Components", fontsize=12, fontweight="bold", pad=10)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _fig_to_b64(fig)


def wordcloud_chart(texts: list, label: str) -> str:
    """
    Word cloud for a list of review strings.
    Returns base64-encoded PNG string, or empty string if wordcloud not installed.
    """
    try:
        from wordcloud import WordCloud
    except ImportError:
        return ""

    combined = " ".join(texts)
    if not combined.strip():
        return ""

    color = _COLORS.get(label, "#607d8b")
    wc = WordCloud(
        width=600, height=300,
        background_color="white",
        color_func=lambda *a, **kw: color,
        max_words=80,
    ).generate(combined)

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(f"{label} Reviews – Word Cloud", fontsize=12, fontweight="bold")
    fig.tight_layout()
    return _fig_to_b64(fig)
