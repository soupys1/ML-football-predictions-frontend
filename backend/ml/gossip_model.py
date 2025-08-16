from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Tuple

import joblib
import pandas as pd
from .csv_loader import read_csv_smart
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.model_selection import train_test_split


MODEL_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "tfidf_vectorizer.joblib")
CLASSIFIER_PATH = os.path.join(MODEL_DIR, "pac_classifier.joblib")


@dataclass
class GossipPrediction:
    is_gossip: bool
    label: str
    confidence: Optional[float]


class GossipDetector:
    def __init__(self) -> None:
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.classifier: Optional[PassiveAggressiveClassifier] = None
        self._keywords = {
            "rumor", "rumour", "gossip", "leaked", "spotted", "dating",
            "breakup", "split", "engaged", "married", "pregnant", "secret",
            "scandal", "affair", "caught", "exclusive"
        }

    def ensure_trained(self, training_csv_path: str) -> None:
        os.makedirs(MODEL_DIR, exist_ok=True)
        if os.path.exists(VECTORIZER_PATH) and os.path.exists(CLASSIFIER_PATH):
            self.vectorizer = joblib.load(VECTORIZER_PATH)
            self.classifier = joblib.load(CLASSIFIER_PATH)
            return

        training_csv_path = os.path.abspath(training_csv_path)
        if not os.path.exists(training_csv_path):
            # No dataset available; skip
            return

        df = read_csv_smart(training_csv_path)
        labels = df["label"]
        x_train, _x_test, y_train, _y_test = train_test_split(
            df["text"], labels, test_size=0.2, random_state=7
        )

        vectorizer = TfidfVectorizer(stop_words="english", max_df=0.7)
        tfidf_train = vectorizer.fit_transform(x_train)

        classifier = PassiveAggressiveClassifier(max_iter=50)
        classifier.fit(tfidf_train, y_train)

        joblib.dump(vectorizer, VECTORIZER_PATH)
        joblib.dump(classifier, CLASSIFIER_PATH)

        self.vectorizer = vectorizer
        self.classifier = classifier

    def _heuristic(self, text: str) -> GossipPrediction:
        if not text:
            return GossipPrediction(is_gossip=False, label="unknown", confidence=None)
        lowered = text.lower()
        hit = any(k in lowered for k in self._keywords)
        return GossipPrediction(is_gossip=hit, label="heuristic_gossip" if hit else "heuristic_clean", confidence=None)

    def predict(self, text: str) -> GossipPrediction:
        if not text or not text.strip():
            return GossipPrediction(is_gossip=False, label="unknown", confidence=None)

        # If no trained model, fall back to heuristics
        if not self.vectorizer or not self.classifier:
            return self._heuristic(text)

        tfidf = self.vectorizer.transform([text])
        label = self.classifier.predict(tfidf)[0]
        # PassiveAggressiveClassifier has decision_function but not calibrated probabilities
        try:
            score = self.classifier.decision_function(tfidf)[0]
            confidence = float(abs(score))
        except Exception:
            score = 0.0
            confidence = None
        label_lower = str(label).lower()
        is_gossip = label_lower in {"gossip", "fake", "rumor", "rumour"}
        # If model seems uncertain, combine with heuristic
        if abs(score) < 0.5:
            heuristic = self._heuristic(text)
            # Prefer a positive heuristic if model is unsure
            if heuristic.is_gossip:
                return GossipPrediction(is_gossip=True, label=f"{label_lower}+heuristic", confidence=confidence)
        return GossipPrediction(is_gossip=is_gossip, label=str(label), confidence=confidence)


