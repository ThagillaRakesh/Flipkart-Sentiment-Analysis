"""
make_ppt.py  —  Generate Opinion Miner project presentation
Run: python3 make_ppt.py
Output: Opinion_Miner_Presentation.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import textwrap

# ── Color Palette ──────────────────────────────────────────────────────────────
DARK_BG    = RGBColor(0x0D, 0x1B, 0x2A)   # deep navy
ACCENT     = RGBColor(0x00, 0xB4, 0xD8)   # cyan-blue
ACCENT2    = RGBColor(0xFF, 0x9F, 0x1C)   # amber
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xD0, 0xD8, 0xE8)
SUBTITLE   = RGBColor(0xA0, 0xC4, 0xDB)
GREEN      = RGBColor(0x2E, 0xCC, 0x71)
RED        = RGBColor(0xE7, 0x4C, 0x3C)

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

BLANK = prs.slide_layouts[6]   # completely blank


# ── Helpers ───────────────────────────────────────────────────────────────────

def add_rect(slide, l, t, w, h, fill, alpha=None):
    shape = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    shape.line.fill.background()
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    return shape


def add_text(slide, text, l, t, w, h,
             size=20, bold=False, color=WHITE, align=PP_ALIGN.LEFT,
             italic=False, wrap=False):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.color.rgb = color
    run.font.italic = italic
    return tb


def add_bullet_box(slide, items, l, t, w, h,
                   size=17, color=LIGHT_GRAY, indent_color=ACCENT,
                   title=None, title_size=20, title_color=ACCENT):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True

    if title:
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = title
        run.font.size  = Pt(title_size)
        run.font.bold  = True
        run.font.color.rgb = title_color

    for item in items:
        p = tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_before = Pt(3)
        run = p.add_run()
        run.text = item
        run.font.size  = Pt(size)
        run.font.color.rgb = color


def slide_bg(slide):
    """Full dark background."""
    add_rect(slide, 0, 0, 13.33, 7.5, DARK_BG)


def accent_bar(slide, y=0.9, h=0.04):
    """Thin horizontal accent line under heading."""
    add_rect(slide, 0.6, y, 12.1, h, ACCENT)


def slide_title(slide, text, y=0.25):
    add_text(slide, text, 0.6, y, 12, 0.65,
             size=30, bold=True, color=ACCENT, align=PP_ALIGN.LEFT)
    accent_bar(slide, y=y + 0.65)


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — Title / First Page
# ═══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_bg(sl)

# Big gradient strip
add_rect(sl, 0, 2.4, 13.33, 3.0, RGBColor(0x05, 0x29, 0x4E))

# Decorative accent blocks
add_rect(sl, 0, 2.4,  0.18, 3.0, ACCENT)
add_rect(sl, 0, 6.8, 13.33, 0.7, RGBColor(0x04, 0x1C, 0x31))

# Title
add_text(sl, "Opinion Miner", 0.6, 2.6, 12, 1.0,
         size=52, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
add_text(sl, "AI-Powered Product Review Sentiment Analyser",
         0.6, 3.65, 12, 0.55,
         size=22, bold=False, color=ACCENT, align=PP_ALIGN.CENTER, italic=True)

# Subtitle strip
add_text(sl, "Flipkart Review Scraping  •  VADER Sentiment  •  Fake Review Detection  •  TTS Verdict",
         0.6, 6.82, 12, 0.36,
         size=13, color=SUBTITLE, align=PP_ALIGN.CENTER)

# Top label
add_text(sl, "PROJECT PRESENTATION", 0.6, 0.22, 12, 0.4,
         size=13, color=SUBTITLE, align=PP_ALIGN.CENTER)
add_rect(sl, 4.5, 0.7, 4.3, 0.05, ACCENT)

add_text(sl, "Department of Computer Science & Engineering",
         0.6, 1.05, 12, 0.35, size=14, color=LIGHT_GRAY, align=PP_ALIGN.CENTER)
add_text(sl, "2025 – 2026", 0.6, 1.45, 12, 0.35,
         size=14, color=SUBTITLE, align=PP_ALIGN.CENTER)


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — Introduction
# ═══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_bg(sl)
slide_title(sl, "Introduction")

add_text(sl,
    "What is Opinion Miner?",
    0.6, 1.15, 12, 0.45, size=20, bold=True, color=ACCENT2)

points = [
    "●  Opinion Miner is a full-stack web application that automatically scrapes customer reviews\n"
    "    from Flipkart and produces an intelligent sentiment verdict — Positive, Neutral, or Negative.",
    "",
    "●  Users paste any Flipkart product URL or type their own review text; the system returns\n"
    "    a detailed analysis in minutes.",
    "",
    "●  The application combines Natural Language Processing (NLP), machine learning lexicons,\n"
    "    rule-based fake review filtering, and interactive visualisations in a single pipeline.",
    "",
    "●  A Text-to-Speech (TTS) engine announces the final verdict aloud with a matching emoji,\n"
    "    making the result instantly understandable.",
]
add_bullet_box(sl, points, 0.6, 1.65, 12.1, 5.2, size=16, color=LIGHT_GRAY)

# Right-side decorative strip
add_rect(sl, 12.8, 1.0, 0.15, 6.0, ACCENT)


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — Problem Statement
# ═══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_bg(sl)
slide_title(sl, "Problem Statement")

# 3 problem cards
card_data = [
    (ACCENT,  "😓  Information Overload",
     "A popular product can have 1000+ reviews. Reading all of them\nbefore purchasing is impractical and time-consuming."),
    (ACCENT2, "🤖  Fake Reviews",
     "Studies show 30-40% of online reviews are fake or incentivised.\nThey mislead buyers and distort product perception."),
    (GREEN,   "📊  No Quick Verdict",
     "Existing platforms show raw star averages but never tell you\n'Should I buy this?' in plain, actionable language."),
]

for i, (col, heading, body) in enumerate(card_data):
    x = 0.5 + i * 4.28
    add_rect(sl, x, 1.2, 4.0, 3.6, RGBColor(0x0A, 0x24, 0x3A))
    add_rect(sl, x, 1.2, 4.0, 0.07, col)
    add_text(sl, heading, x+0.15, 1.35, 3.7, 0.55, size=16, bold=True, color=col)
    add_text(sl, body,    x+0.15, 1.98, 3.7, 2.6,  size=14, color=LIGHT_GRAY, wrap=True)

add_text(sl,
    "➤  There is a clear need for an automated, intelligent system that reads, filters,\n"
    "    analyses, and summarises product reviews — delivering a trustworthy, instant verdict.",
    0.6, 5.1, 12.1, 1.0, size=16, color=WHITE, italic=True)
add_rect(sl, 0.6, 5.05, 12.1, 0.04, ACCENT2)


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — Existing Platforms & Drawbacks
# ═══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_bg(sl)
slide_title(sl, "Existing Platforms & Their Drawbacks")

# Table-style layout
headers = ["Platform", "What It Offers", "Key Drawbacks"]
col_x   = [0.5, 3.5, 8.2]
col_w   = [2.8, 4.5, 4.8]

# Header row
for j, h in enumerate(headers):
    add_rect(sl, col_x[j], 1.15, col_w[j]-0.05, 0.45, ACCENT)
    add_text(sl, h, col_x[j]+0.1, 1.18, col_w[j]-0.1, 0.4,
             size=15, bold=True, color=DARK_BG)

rows = [
    ("Flipkart / Amazon\n(built-in)",
     "Star ratings, review listing,\nhelpful votes",
     "No NLP analysis · No fake detection\nNo buy/avoid recommendation"),
    ("Google Reviews",
     "Aggregate star rating\nfor businesses",
     "No product-level analysis\nNo text sentiment breakdown"),
    ("Trustpilot",
     "Verified review aggregation\nfor companies",
     "Not product-specific · Manual\nNo auto sentiment scoring"),
    ("ReviewMeta /\nFakespot",
     "Fake review detection\nfor Amazon only",
     "Amazon-only · No sentiment analysis\nNo visual breakdown or audio"),
    ("SentimentR /\nMonkeyLearn",
     "General sentiment API",
     "No scraping · No fake detection\nRequires developer integration"),
]

for i, (p, o, d) in enumerate(rows):
    y = 1.7 + i * 0.97
    bg = RGBColor(0x0A, 0x22, 0x38) if i % 2 == 0 else RGBColor(0x08, 0x1C, 0x2E)
    for j, col_x_val in enumerate(col_x):
        add_rect(sl, col_x_val, y, col_w[j]-0.05, 0.88, bg)
    add_text(sl, p, col_x[0]+0.1, y+0.05, col_w[0]-0.1, 0.8, size=12, bold=True, color=ACCENT)
    add_text(sl, o, col_x[1]+0.1, y+0.05, col_w[1]-0.1, 0.8, size=12, color=LIGHT_GRAY, wrap=True)
    add_text(sl, d, col_x[2]+0.1, y+0.05, col_w[2]-0.1, 0.8, size=12, color=RGBColor(0xFF,0xAA,0x80), wrap=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — Proposed Solution
# ═══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_bg(sl)
slide_title(sl, "Proposed Solution — Opinion Miner")

features = [
    ("🔍  Automated Scraping",
     "Selenium scrapes up to 400+ reviews across 50 pages\nfrom any Flipkart product URL automatically."),
    ("🧠  VADER Sentiment Model",
     "VADER (Valence Aware Dictionary & sEntiment Reasoner)\nclassifies each review as Positive / Neutral / Negative."),
    ("🤖  Fake Review Detector",
     "4-rule heuristic engine flags and excludes fake reviews\nbefore sentiment is calculated."),
    ("📊  Visual Dashboard",
     "Sentiment bar chart, score distribution chart, and\nPositive/Negative word clouds — all generated live."),
    ("🔊  TTS Audio Verdict",
     "pyttsx3 speaks the final verdict aloud with a\nmatching emoji (😊 / 😐 / 😞)."),
    ("✍️  Direct Text Analysis",
     "Users can also type any review text directly\nfor instant single-sentence sentiment scoring."),
]

for i, (heading, body) in enumerate(features):
    col = i % 2
    row = i // 2
    x = 0.5 + col * 6.45
    y = 1.2 + row * 1.85
    add_rect(sl, x, y, 6.15, 1.65, RGBColor(0x07, 0x22, 0x3A))
    add_rect(sl, x, y, 0.07, 1.65, ACCENT if col == 0 else ACCENT2)
    add_text(sl, heading, x+0.2, y+0.1, 5.9, 0.5,  size=15, bold=True, color=ACCENT if col==0 else ACCENT2)
    add_text(sl, body,    x+0.2, y+0.6, 5.9, 1.0,  size=13, color=LIGHT_GRAY, wrap=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — Technologies Used
# ═══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_bg(sl)
slide_title(sl, "Technologies & Models Used")

categories = [
    ("⚙️  Backend / Framework",   ACCENT,
     ["Python 3.12", "Flask (REST API + Jinja2 templating)",
      "BeautifulSoup4 (HTML parsing)"]),
    ("🌐  Web Scraping",           ACCENT2,
     ["Selenium WebDriver (headless Chrome)", "ChromeDriver (automated browser)",
      "Smart WebDriverWait (element-aware timing)"]),
    ("🧠  NLP & ML Models",        GREEN,
     ["VADER — NLTK SentimentIntensityAnalyzer",
      "  ↳ Compound score: pos ≥ 0.05 | neg ≤ −0.05",
      "NLTK — Tokenizer, Stopword removal, WordNetLemmatizer",
      "Custom Negation Heuristic (compound × 0.85 on negation words)"]),
    ("🤖  Fake Review Detection",  RGBColor(0xFF,0x6B,0x6B),
     ["Rule 1: Length < 5 words → Too short",
      "Rule 2: Repeated words > 30% → Spam pattern",
      "Rule 3: ≥ 2 occurrences of !! or ?? → Excess punctuation",
      "Rule 4: High star + negative sentiment → Rating mismatch",
      "≥ 2 rules triggered → Review flagged FAKE"]),
    ("📊  Visualisation",          RGBColor(0xA8,0x6C,0xFF),
     ["Matplotlib (bar charts)", "WordCloud library (word clouds)",
      "Base64 PNG encoding (embedded in JSON)"]),
    ("🔊  Text-to-Speech",         RGBColor(0xFF,0xC3,0x00),
     ["pyttsx3 — offline TTS engine",
      "Pre-generated WAV files: positive / neutral / negative",
      "HTML5 <audio> player with auto-play"]),
]

cols = [0.35, 6.85]
for i, (cat, col, items) in enumerate(categories):
    x = cols[i % 2]
    y = 1.1 + (i // 2) * 2.1
    add_rect(sl, x, y, 6.3, 1.9, RGBColor(0x07, 0x1E, 0x34))
    add_rect(sl, x, y, 6.3, 0.06, col)
    add_text(sl, cat, x+0.12, y+0.1, 6.1, 0.45, size=14, bold=True, color=col)
    add_bullet_box(sl, items, x+0.15, y+0.55, 6.0, 1.3, size=12, color=LIGHT_GRAY)


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — System Architecture
# ═══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_bg(sl)
slide_title(sl, "System Architecture")

# Pipeline flow diagram
steps = [
    ("User\nInput",       "URL or\nText",      ACCENT),
    ("Scraper\nModule",   "Selenium\n+BS4",    ACCENT2),
    ("NLP\nPipeline",     "NLTK\nPreprocess",  GREEN),
    ("Sentiment\nEngine", "VADER\nModel",      RGBColor(0xA8,0x6C,0xFF)),
    ("Fake\nDetector",    "4-Rule\nHeuristic", RGBColor(0xFF,0x6B,0x6B)),
    ("Aggregator\n+UI",   "Flask\nResponse",   RGBColor(0xFF,0xC3,0x00)),
]

box_w, box_h = 1.7, 1.2
start_x, y = 0.55, 2.1

for i, (title, subtitle, col) in enumerate(steps):
    x = start_x + i * 2.12
    add_rect(sl, x, y, box_w, box_h, RGBColor(0x07, 0x22, 0x3A))
    add_rect(sl, x, y, box_w, 0.07, col)
    add_text(sl, title,    x+0.08, y+0.12, box_w-0.1, 0.5, size=13, bold=True, color=col, align=PP_ALIGN.CENTER)
    add_text(sl, subtitle, x+0.08, y+0.65, box_w-0.1, 0.45, size=11, color=LIGHT_GRAY, align=PP_ALIGN.CENTER)
    # Arrow
    if i < len(steps) - 1:
        ax = x + box_w + 0.05
        add_text(sl, "→", ax, y + 0.42, 0.35, 0.35, size=20, bold=True, color=ACCENT)

# Output row
outputs = [
    ("Sentiment Label",    "Positive / Neutral / Negative",  GREEN),
    ("Review Stats",       "Genuine · Fake · Total counts",   ACCENT),
    ("Charts",             "Bar chart + Score chart + Word clouds", ACCENT2),
    ("TTS Audio + Emoji",  "Spoken verdict  😊 😐 😞",        RGBColor(0xFF,0xC3,0x00)),
]

add_text(sl, "Outputs:", 0.55, 3.65, 2, 0.4, size=14, bold=True, color=WHITE)
for i, (lbl, val, col) in enumerate(outputs):
    x = 0.55 + i * 3.18
    add_rect(sl, x, 4.1, 3.0, 1.0, RGBColor(0x05, 0x1A, 0x2E))
    add_rect(sl, x, 4.1, 0.07, 1.0, col)
    add_text(sl, lbl, x+0.15, 4.15, 2.8, 0.4, size=13, bold=True, color=col)
    add_text(sl, val, x+0.15, 4.58, 2.8, 0.45, size=11, color=LIGHT_GRAY, wrap=True)

# Data flow note
add_text(sl,
    "Flask serves the frontend (index.html). JavaScript fetches /analyze or /analyze-url via POST.\n"
    "All NLP runs server-side; charts are Base64-encoded PNGs embedded in the JSON response.",
    0.55, 5.3, 12.2, 0.8, size=13, color=SUBTITLE, italic=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — Modules
# ═══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_bg(sl)
slide_title(sl, "System Modules")

modules = [
    ("scraper/\nflipkart_scraper.py",
     ACCENT,
     ["Selenium headless Chrome driver",
      "Handles 3 Flipkart layout variants (gMdEY7 · vQDoqR · RNW css-1jxf684)",
      "Paginated scraping — up to 50 pages per session",
      "Smart WebDriverWait + READ MORE expansion",
      "Noise & ad filtering; cross-page deduplication"]),
    ("nlp/\npreprocessor.py",
     GREEN,
     ["Lowercasing, punctuation removal",
      "NLTK word tokenisation",
      "Stopword removal (negations preserved: not, no, never…)",
      "WordNet Lemmatisation"]),
    ("nlp/\nsentiment.py",
     ACCENT2,
     ["VADER SentimentIntensityAnalyzer",
      "Compound score → Positive (≥0.05) · Neutral · Negative (≤−0.05)",
      "Custom negation heuristic: compound × 0.85 when negation present"]),
    ("nlp/\nfake_detector.py",
     RGBColor(0xFF,0x6B,0x6B),
     ["Rule 1 — Too short (< 5 words)",
      "Rule 2 — Repeated words > 30% of total",
      "Rule 3 — Excess punctuation (≥2 occurrences of !! or ??)",
      "Rule 4 — Star rating vs sentiment mismatch",
      "≥ 2 rules triggered → FAKE (excluded from analysis)"]),
    ("utils/\naggregator.py",
     RGBColor(0xA8,0x6C,0xFF),
     ["Counts Positive / Neutral / Negative / Fake",
      "Calculates avg compound score",
      "Overall verdict logic: majority class wins",
      "Generates buy/avoid action recommendation"]),
    ("utils/\nvisualizer.py  +  TTS",
     RGBColor(0xFF,0xC3,0x00),
     ["Matplotlib sentiment bar chart",
      "VADER score bar chart (pos · neu · neg)",
      "WordCloud for positive & negative reviews",
      "pyttsx3 WAV files: positive.wav · neutral.wav · negative.wav"]),
]

cols_x = [0.35, 4.55, 8.75]
for i, (name, col, items) in enumerate(modules):
    x = cols_x[i % 3]
    y = 1.1 + (i // 3) * 2.9
    add_rect(sl, x, y, 3.9, 2.65, RGBColor(0x07, 0x1E, 0x34))
    add_rect(sl, x, y, 3.9, 0.06, col)
    add_text(sl, name, x+0.12, y+0.1, 3.7, 0.6, size=12, bold=True, color=col)
    add_bullet_box(sl, items, x+0.12, y+0.72, 3.7, 1.9, size=11, color=LIGHT_GRAY)


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — Future Work
# ═══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_bg(sl)
slide_title(sl, "Future Work & Enhancements")

future = [
    ("🤗  Transformer-Based Sentiment",
     ACCENT,
     "Replace VADER with BERT / RoBERTa fine-tuned on e-commerce reviews\n"
     "for significantly higher accuracy on sarcasm and domain-specific language."),
    ("🏪  Multi-Platform Scraping",
     ACCENT2,
     "Extend scraper to Amazon, Meesho, Myntra, and Snapdeal\n"
     "for cross-platform review aggregation and comparison."),
    ("🧬  ML-Based Fake Detection",
     GREEN,
     "Train a supervised classifier (Random Forest / XGBoost) on labelled\n"
     "fake/genuine review datasets instead of hand-crafted rules."),
    ("📱  Mobile Application",
     RGBColor(0xA8,0x6C,0xFF),
     "Build an Android / iOS app so users can scan product QR codes\n"
     "and get instant sentiment verdict on their phone."),
    ("🗣️  Multilingual Support",
     RGBColor(0xFF,0x6B,0x6B),
     "Support Hindi, Tamil, Telugu and other regional language reviews\n"
     "using multilingual NLP models (mBERT, IndicBERT)."),
    ("⚡  Real-Time API",
     RGBColor(0xFF,0xC3,0x00),
     "Package as a public REST API so third-party apps and browser\n"
     "extensions can query sentiment for any product on the fly."),
]

for i, (heading, col, body) in enumerate(future):
    c = i % 2
    r = i // 2
    x = 0.4 + c * 6.48
    y = 1.15 + r * 1.9
    add_rect(sl, x, y, 6.2, 1.7, RGBColor(0x07, 0x1E, 0x34))
    add_rect(sl, x, y, 0.07, 1.7, col)
    add_text(sl, heading, x+0.2, y+0.1,  6.0, 0.5, size=15, bold=True, color=col)
    add_text(sl, body,    x+0.2, y+0.62, 6.0, 1.0, size=13, color=LIGHT_GRAY, wrap=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — Conclusion
# ═══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_bg(sl)
slide_title(sl, "Conclusion")

add_text(sl,
    "Opinion Miner successfully bridges the gap between raw customer reviews and actionable purchase decisions.",
    0.6, 1.1, 12.1, 0.55, size=17, bold=True, color=WHITE, wrap=True)

conclusions = [
    ("✅  Automated Pipeline",
     "End-to-end flow from URL input → scraping → NLP → verdict in under 5 minutes."),
    ("✅  Accurate Sentiment",
     "VADER with custom negation heuristic delivers reliable Positive/Neutral/Negative classification."),
    ("✅  Fake Review Shield",
     "4-rule detector removes manipulative reviews before sentiment is calculated,\n"
     "ensuring the verdict reflects genuine buyer experiences."),
    ("✅  Accessible Output",
     "Visual charts, per-review breakdown, TTS audio verdict, and emoji make\n"
     "results understandable for all users — not just technical ones."),
    ("✅  Scalable Design",
     "Modular architecture (scraper / nlp / utils) makes it straightforward\n"
     "to add new platforms, languages, or ML models in the future."),
]

for i, (heading, body) in enumerate(conclusions):
    y = 1.75 + i * 1.0
    add_rect(sl, 0.6, y, 12.1, 0.85, RGBColor(0x07, 0x1E, 0x34))
    add_rect(sl, 0.6, y, 0.07, 0.85, ACCENT)
    add_text(sl, heading, 0.8,  y+0.05, 3.5, 0.4, size=14, bold=True, color=ACCENT)
    add_text(sl, body,    4.35, y+0.05, 8.3, 0.7, size=13, color=LIGHT_GRAY, wrap=True)

add_rect(sl, 0.6, 6.85, 12.1, 0.05, ACCENT2)
add_text(sl, "Thank You  ·  Questions Welcome",
         0.6, 6.9, 12.1, 0.4, size=16, bold=True, color=ACCENT2, align=PP_ALIGN.CENTER)


# ── Save ───────────────────────────────────────────────────────────────────────
out = "Opinion_Miner_Presentation.pptx"
prs.save(out)
print(f"Saved: {out}")
