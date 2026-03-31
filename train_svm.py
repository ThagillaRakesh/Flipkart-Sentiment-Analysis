"""
train_svm.py
Train SVM fake-review detector on the learn-claude dataset and save artifacts.

Run once:  python3 train_svm.py
Outputs  : models/svm_model.pkl
           models/tfidf_svm.pkl
           models/svm_info.json
"""

import re, json, pickle, sys
import numpy as np
import pandas as pd
import nltk
from nltk.corpus   import stopwords
from nltk.stem     import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm         import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_score,
                             recall_score, f1_score, classification_report)
import os

# ── NLTK data ──────────────────────────────────────────────────────────────
for pkg in ['stopwords', 'wordnet', 'omw-1.4', 'punkt', 'punkt_tab']:
    nltk.download(pkg, quiet=True)

# ── Paths ──────────────────────────────────────────────────────────────────
# Dataset path: pass as CLI argument or set DATASET_PATH env variable
# e.g.  python3 train_svm.py /path/to/fake_reviews.csv
DATASET = (
    sys.argv[1]
    if len(sys.argv) > 1
    else os.environ.get("DATASET_PATH", "fake reviews dataset.csv")
)
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

SVM_PATH   = os.path.join(MODEL_DIR, "svm_model.pkl")
TFIDF_PATH = os.path.join(MODEL_DIR, "tfidf_svm.pkl")
INFO_PATH  = os.path.join(MODEL_DIR, "svm_info.json")

# ── Preprocessing (same as the notebook) ──────────────────────────────────
lemmatizer = WordNetLemmatizer()
STOP_WORDS = set(stopwords.words('english')) - {
    'no', 'not', 'nor', 'never', 'neither', 'without', 'barely', 'hardly'
}

def preprocess(text: str) -> str:
    text   = re.sub(r'http\S+|www\S+', '', str(text).lower())
    text   = re.sub(r'[^a-z\s]', '', text)
    tokens = word_tokenize(text)
    tokens = [lemmatizer.lemmatize(w)
              for w in tokens
              if w not in STOP_WORDS and len(w) > 1]
    return ' '.join(tokens) if tokens else ''

# ── Load dataset ───────────────────────────────────────────────────────────
print(f"Loading dataset: {DATASET}")
df = pd.read_csv(DATASET)
print(f"  Shape  : {df.shape}")
print(f"  Labels : {df['label'].value_counts().to_dict()}")

df.dropna(subset=['text_'], inplace=True)
df['label'] = df['label'].map({'CG': 1, 'OR': 0})   # 1=Fake, 0=Genuine
df = df[['text_', 'label']].copy()

# ── Preprocess ─────────────────────────────────────────────────────────────
print(f"\nPreprocessing {len(df):,} reviews ...")
df['clean_text'] = df['text_'].apply(preprocess).fillna('')
print("  Done.")

# ── TF-IDF ─────────────────────────────────────────────────────────────────
print("\nFitting TF-IDF vectorizer (15 000 features, unigrams+bigrams) ...")
tfidf = TfidfVectorizer(
    max_features = 15000,
    ngram_range  = (1, 2),
    min_df       = 2,
    sublinear_tf = True,
)
X = tfidf.fit_transform(df['clean_text'])
y = df['label'].values
print(f"  Matrix : {X.shape}")

# ── Train/Test split ───────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTrain : {X_train.shape[0]:,}  |  Test : {X_test.shape[0]:,}")

# ── Train SVM ──────────────────────────────────────────────────────────────
print("\nTraining LinearSVC (SVM) ...")
svm = LinearSVC(C=1.0, max_iter=3000, random_state=42)
svm.fit(X_train, y_train)
print("  Done.")

# ── Evaluate ───────────────────────────────────────────────────────────────
preds = svm.predict(X_test)
acc   = round(accuracy_score (y_test, preds) * 100, 2)
prec  = round(precision_score(y_test, preds, zero_division=0) * 100, 2)
rec   = round(recall_score   (y_test, preds, zero_division=0) * 100, 2)
f1    = round(f1_score       (y_test, preds, zero_division=0) * 100, 2)

print("\n" + "=" * 50)
print("  SVM  EVALUATION RESULTS")
print("=" * 50)
print(f"  Accuracy  : {acc}%")
print(f"  Precision : {prec}%")
print(f"  Recall    : {rec}%")
print(f"  F1-Score  : {f1}%")
print("=" * 50)
print()
print(classification_report(y_test, preds, target_names=['Genuine', 'Fake']))

# ── Save artifacts ─────────────────────────────────────────────────────────
with open(SVM_PATH,   'wb') as f: pickle.dump(svm,   f)
with open(TFIDF_PATH, 'wb') as f: pickle.dump(tfidf, f)

info = {
    "model":      "LinearSVC (SVM)",
    "accuracy":   acc,
    "precision":  prec,
    "recall":     rec,
    "f1_score":   f1,
    "features":   15000,
    "ngram":      "(1,2)",
    "train_rows": X_train.shape[0],
    "test_rows":  X_test.shape[0],
    "labels":     {"0": "Genuine", "1": "Fake"},
}
with open(INFO_PATH, 'w') as f:
    json.dump(info, f, indent=2)

print(f"\nSaved:")
print(f"  {SVM_PATH}")
print(f"  {TFIDF_PATH}")
print(f"  {INFO_PATH}")
print("\nSVM model is ready for use in Opinion Miner.")
