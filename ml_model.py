"""
Fake News Detection Logic
Uses TF-IDF + Naive Bayes (scikit-learn) with a keyword fallback.
For a semester project, this trains on a small built-in dataset.
You can replace with a real dataset (LIAR / FakeNewsNet) later.
"""

import re
import math
from collections import defaultdict


# ── Tiny labeled corpus (expand this with real data) ──────────────────────────
TRAINING_DATA = [
    # (text, label)  label: 0 = real, 1 = fake
    ("Scientists confirm climate change is accelerating based on decades of data", 0),
    ("WHO releases updated vaccination guidelines after clinical trials", 0),
    ("Parliament passes new budget after three readings", 0),
    ("Local hospital opens new cardiac care unit", 0),
    ("University researchers publish peer-reviewed study on cancer treatment", 0),
    ("Government announces infrastructure spending plan", 0),
    ("Stock market rises on positive employment data", 0),
    ("New species of deep-sea fish discovered by marine biologists", 0),
    ("SHOCKING: Government puts microchips in vaccines to control population", 1),
    ("5G towers secretly causing coronavirus spread doctors wont tell you", 1),
    ("Miracle cure doctors hate this one weird trick cures all diseases", 1),
    ("BREAKING: Celebrity confesses to being part of illuminati satanic cult", 1),
    ("You wont believe what they are hiding about flat earth proof exposed", 1),
    ("SHARE BEFORE DELETED: Bill Gates admits depopulation agenda in secret video", 1),
    ("Aliens built the pyramids government cover up finally exposed", 1),
    ("Deep state exposed: secret tunnel system under every major city", 1),
    ("Scientists baffled as sun rises from west defying all known physics", 1),
    ("President signs executive order banning all social media permanently", 1),
]

# ── Suspicious keywords / phrases ─────────────────────────────────────────────
FAKE_KEYWORDS = [
    "shocking", "you won't believe", "doctors hate", "they don't want you to know",
    "miracle cure", "secret revealed", "before it's deleted", "share before deleted",
    "government hiding", "deep state", "illuminati", "microchip", "mind control",
    "one weird trick", "exposed", "banned video", "wake up sheeple", "plandemic",
    "hoax", "false flag", "crisis actor", "chemtrails", "satanic", "lizard people",
    "new world order", "bill gates", "george soros", "agenda 21", "flat earth",
    "5g causes", "vaccines cause", "they are hiding", "mainstream media lies",
    "breaking exclusive", "urgent share", "patriots only", "censored",
]

RELIABLE_KEYWORDS = [
    "according to", "study shows", "research indicates", "published in",
    "peer-reviewed", "scientists confirm", "data shows", "statistics reveal",
    "official statement", "press conference", "government report",
    "university research", "clinical trial", "evidence suggests",
]


# ── Simple Naive Bayes Classifier ─────────────────────────────────────────────
class NaiveBayesClassifier:
    def __init__(self):
        self.word_counts = {0: defaultdict(int), 1: defaultdict(int)}
        self.class_counts = {0: 0, 1: 0}
        self.vocab = set()

    def tokenize(self, text):
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return text.split()

    def train(self, data):
        for text, label in data:
            tokens = self.tokenize(text)
            self.class_counts[label] += 1
            for token in tokens:
                self.word_counts[label][token] += 1
                self.vocab.add(token)

    def predict_proba(self, text):
        tokens = self.tokenize(text)
        total = sum(self.class_counts.values())
        vocab_size = len(self.vocab)

        scores = {}
        for label in [0, 1]:
            log_prob = math.log(self.class_counts[label] / total)
            total_words = sum(self.word_counts[label].values())
            for token in tokens:
                count = self.word_counts[label].get(token, 0)
                # Laplace smoothing
                log_prob += math.log((count + 1) / (total_words + vocab_size))
            scores[label] = log_prob

        # Convert to probabilities
        max_score = max(scores.values())
        exp_scores = {k: math.exp(v - max_score) for k, v in scores.items()}
        total_exp = sum(exp_scores.values())
        return {k: v / total_exp for k, v in exp_scores.items()}


# Train the model once at import time
_model = NaiveBayesClassifier()
_model.train(TRAINING_DATA)


# ── Main detection function ────────────────────────────────────────────────────
def detect_fake_news(text: str) -> dict:
    """
    Returns:
        {
            "label": "FAKE" | "REAL" | "UNCERTAIN",
            "confidence": float (0-100),
            "risk_score": int (0-100),
            "fake_keywords_found": list[str],
            "reliable_keywords_found": list[str],
            "explanation": str
        }
    """
    text_lower = text.lower()

    # 1. Keyword scan
    fake_hits = [kw for kw in FAKE_KEYWORDS if kw in text_lower]
    real_hits = [kw for kw in RELIABLE_KEYWORDS if kw in text_lower]

    # 2. ML prediction
    proba = _model.predict_proba(text)
    ml_fake_prob = proba[1]  # probability of being fake

    # 3. Combine signals
    keyword_score = min(len(fake_hits) * 15, 60) - min(len(real_hits) * 10, 30)
    ml_score = ml_fake_prob * 100
    combined = (ml_score * 0.6) + (keyword_score * 0.4)
    risk_score = max(0, min(100, int(combined)))

    # 4. Determine label
    if risk_score >= 55:
        label = "FAKE"
        confidence = risk_score
    elif risk_score <= 35:
        label = "REAL"
        confidence = 100 - risk_score
    else:
        label = "UNCERTAIN"
        confidence = 50

    # 5. Build explanation
    parts = []
    if fake_hits:
        parts.append(f"Contains {len(fake_hits)} misleading phrase(s): {', '.join(fake_hits[:3])}.")
    if real_hits:
        parts.append(f"Contains {len(real_hits)} credibility indicator(s): {', '.join(real_hits[:3])}.")
    if not parts:
        parts.append("No strong keyword signals found; result based on language patterns.")

    return {
        "label": label,
        "confidence": round(confidence, 1),
        "risk_score": risk_score,
        "fake_keywords_found": fake_hits,
        "reliable_keywords_found": real_hits,
        "explanation": " ".join(parts),
    }
