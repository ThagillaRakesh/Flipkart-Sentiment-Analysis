"""
nlp/fake_detector.py
SVM-based fake review detector.

Model   : LinearSVC trained on 40,432 reviews (20,216 fake / 20,216 genuine)
Features: TF-IDF (15,000 features, unigrams + bigrams, sublinear_tf=True)
Accuracy: 91.55%  |  Precision: 91.63%  |  Recall: 91.47%  |  F1: 91.55%

Labels  : CG (Computer Generated) → Fake
          OR (Original Review)     → Genuine

Sentiment analysis is applied ONLY on reviews classified as Genuine.
"""

import os, re, pickle, json
import nltk
from nltk.corpus   import stopwords
from nltk.stem     import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# ── NLTK data ──────────────────────────────────────────────────────────────
for _pkg in ['stopwords', 'wordnet', 'omw-1.4', 'punkt', 'punkt_tab']:
    try:
        nltk.download(_pkg, quiet=True)
    except Exception:
        pass

# ── Model paths ────────────────────────────────────────────────────────────
_HERE      = os.path.dirname(__file__)
_MODEL_DIR = os.path.join(_HERE, '..', 'models')
_SVM_PATH  = os.path.join(_MODEL_DIR, 'svm_model.pkl')
_TFIDF_PATH= os.path.join(_MODEL_DIR, 'tfidf_svm.pkl')
_INFO_PATH = os.path.join(_MODEL_DIR, 'svm_info.json')

# ── Load model once at import time ─────────────────────────────────────────
_svm   = None
_tfidf = None
_info  = {}

def _load_model():
    global _svm, _tfidf, _info
    if _svm is not None:
        return True
    try:
        with open(_SVM_PATH,   'rb') as f: _svm   = pickle.load(f)
        with open(_TFIDF_PATH, 'rb') as f: _tfidf = pickle.load(f)
        if os.path.exists(_INFO_PATH):
            with open(_INFO_PATH) as f: _info = json.load(f)
        return True
    except FileNotFoundError:
        return False

_MODEL_READY = _load_model()
if not _MODEL_READY:
    import sys
    print("[fake_detector] WARNING: SVM model files not found. "
          "Falling back to weak rule-based detector. "
          "Run train_svm.py to generate model files.", file=sys.stderr)

# ── Preprocessing (identical to training pipeline) ─────────────────────────
_lemmatizer = WordNetLemmatizer()
_STOP_WORDS = set(stopwords.words('english')) - {
    'no', 'not', 'nor', 'never', 'neither', 'without', 'barely', 'hardly'
}

def _preprocess(text: str) -> str:
    text   = re.sub(r'http\S+|www\S+', '', str(text).lower())
    text   = re.sub(r'[^a-z\s]', '', text)
    tokens = word_tokenize(text)
    tokens = [_lemmatizer.lemmatize(w)
              for w in tokens
              if w not in _STOP_WORDS and len(w) > 1]
    return ' '.join(tokens) if tokens else ''


# ── Public API ─────────────────────────────────────────────────────────────

def model_info() -> dict:
    """Return SVM model performance metadata."""
    return _info.copy()


def is_fake(text: str) -> dict:
    """
    Classify a single review using the SVM model.

    Returns:
        {
            "fake":   bool,
            "label":  "Fake" | "Genuine",
            "method": "SVM" | "rule-based-fallback",
        }
    """
    if _MODEL_READY:
        clean = _preprocess(text)
        vec   = _tfidf.transform([clean])
        pred  = int(_svm.predict(vec)[0])   # 1=Fake, 0=Genuine
        return {
            "fake":   pred == 1,
            "label":  "Fake" if pred == 1 else "Genuine",
            "method": "SVM",
        }

    # ── Fallback: rule-based (if model files missing) ──────────────────────
    words   = text.split()
    reasons = []
    if len(words) < 5:
        reasons.append("Too short")
    from collections import Counter
    if words:
        most = Counter(w.lower() for w in words).most_common(1)[0][1]
        if most / len(words) > 0.30:
            reasons.append("Repeated words")
    if len(re.findall(r'[!?]{2,}', text)) >= 2:
        reasons.append("Excess punctuation")
    fake = len(reasons) >= 2
    return {
        "fake":   fake,
        "label":  "Fake" if fake else "Genuine",
        "method": "rule-based-fallback",
    }


def filter_reviews(reviews: list, ratings: list = None) -> tuple:
    """
    Classify a list of review texts using the SVM model.
    Sentiment analysis should be applied ONLY on genuine_reviews.

    Args:
        reviews : list of raw review strings
        ratings : unused (kept for API compatibility with old rule-based version)

    Returns:
        (genuine_reviews, fake_reviews, fake_details)
        genuine_reviews : list[str]  — pass these to sentiment analysis
        fake_reviews    : list[str]
        fake_details    : list[{"text": str, "label": "Fake", "method": str}]
    """
    genuine, fake_list, fake_details = [], [], []

    for text in reviews:
        verdict = is_fake(text)
        if verdict["fake"]:
            fake_list.append(text)
            fake_details.append({
                "text":   text,
                "label":  verdict["label"],
                "method": verdict["method"],
            })
        else:
            genuine.append(text)

    return genuine, fake_list, fake_details
