"""
nlp/preprocessor.py
Text preprocessing pipeline:
  lowercase → remove punctuation → tokenize →
  remove stopwords (keep negations) → stem/lemmatize
"""
import re
import nltk

# Download required NLTK data on first use (silent if already present)
for _pkg in ("stopwords", "punkt", "wordnet", "punkt_tab"):
    try:
        nltk.download(_pkg, quiet=True)
    except Exception:
        pass

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

_STOP = set(stopwords.words("english"))
_NEGATIONS = {"not", "no", "never", "none", "n't", "hardly", "scarcely", "barely",
               "without", "neither", "nor"}
# Keep negations: remove them from the stopword set so they aren't stripped
_STOP -= _NEGATIONS

_lemmatizer = WordNetLemmatizer()


def preprocess(text: str) -> str:
    """
    Full preprocessing pipeline.
    Returns a cleaned, lemmatized string ready for sentiment analysis.
    """
    # 1. Lowercase
    text = text.lower()
    # 2. Remove punctuation (keep apostrophes for contractions like "n't")
    text = re.sub(r"[^\w\s']", " ", text)
    # 3. Tokenize
    tokens = word_tokenize(text)
    # 4. Remove stopwords (negations preserved)
    tokens = [t for t in tokens if t not in _STOP]
    # 5. Lemmatize
    tokens = [_lemmatizer.lemmatize(t) for t in tokens]
    return " ".join(tokens)


def tokenize(text: str) -> list:
    """Return a list of lowercased word tokens (no punctuation, no stopwords)."""
    return preprocess(text).split()
