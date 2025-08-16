from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from .csv_loader import read_csv_smart


ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_PATH = os.path.join(ARTIFACT_DIR, "game_winner_rf.joblib")
FEATURES_PATH = os.path.join(ARTIFACT_DIR, "game_winner_rf_features.json")


def train_game_winner_model(games_csv: str, teams_csv: str = None, players_csv: str = None) -> Dict[str, object]:
    """Train a game winner prediction model"""
    print(f"Training game winner model with {games_csv}")
    
    # Load games data
    games_df = read_csv_smart(games_csv)
    
    # Create winner column if not exists
    if 'winner' not in games_df.columns:
        def get_winner(row):
            if row["homeGoals"] > row["awayGoals"]:
                return "Home"
            elif row["awayGoals"] > row["homeGoals"]:
                return "Away"
            else:
                return "Draw"
        
        games_df["winner"] = games_df.apply(get_winner, axis=1)
    
    # Select features (use available columns)
    available_features = []
    feature_candidates = [
        "homeProbability", "drawProbability", "awayProbability",
        "B365H", "B365D", "B365A", "BWH", "BWD", "BWA",
        "IWH", "IWD", "IWA", "PSH", "PSD", "PSA",
        "WHH", "WHD", "WHA", "VCH", "VCD", "VCA",
        "PSCH", "PSCD", "PSCA"
    ]
    
    for feature in feature_candidates:
        if feature in games_df.columns:
            available_features.append(feature)
    
    if not available_features:
        # Fallback to basic features
        available_features = ["homeGoals", "awayGoals"]
    
    print(f"Using features: {available_features}")
    
    # Prepare data
    X = games_df[available_features].fillna(0)
    y = games_df["winner"]
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # Save model
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    
    # Save features
    with open(FEATURES_PATH, "w", encoding="utf-8") as f:
        json.dump({"features": available_features}, f, indent=2)
    
    return {
        "trained_samples": len(games_df),
        "features": available_features,
        "accuracy": accuracy,
        "model_path": MODEL_PATH
    }


def predict_game_winner(home_team_id: int, away_team_id: int, games_csv: str, teams_csv: str = None) -> Dict[str, object]:
    """Predict game winner between two teams"""
    # Load model
    model_instance = GameWinnerModel()
    if not model_instance.load():
        raise RuntimeError("Model not trained. Train first.")
    
    # Get team features (simplified for now)
    # In a real implementation, you'd get team stats from teams_csv
    feature_map = {
        "homeProbability": 0.4,
        "awayProbability": 0.35,
        "drawProbability": 0.25
    }
    
    # Add any other available features
    for feature in model_instance.required_features():
        if feature not in feature_map:
            feature_map[feature] = 0.0
    
    # Make prediction
    result = model_instance.predict(feature_map)
    return result


class GameWinnerModel:
    def __init__(self) -> None:
        self._model = None
        self._features: Optional[List[str]] = None

    @property
    def is_ready(self) -> bool:
        return os.path.exists(MODEL_PATH) and os.path.exists(FEATURES_PATH)

    def load(self) -> bool:
        if not self.is_ready:
            return False
        if self._model is None:
            self._model = joblib.load(MODEL_PATH)
        if self._features is None:
            with open(FEATURES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._features = list(data.get("features", []))
        return True

    def required_features(self) -> List[str]:
        if self._features is None and self.is_ready:
            self.load()
        return self._features or []

    def predict(self, feature_map: Dict[str, float]) -> Dict[str, object]:
        if not self.load():
            raise RuntimeError("Game winner model artifacts not found. Train first.")
        x = [float(feature_map.get(name, 0.0)) for name in self._features]
        proba = self._model.predict_proba([x])[0]
        winner = self._model.predict([x])[0]
        return {
            "winner": str(winner),
            "probabilities": {str(label): float(p) for label, p in zip(self._model.classes_, proba)},
            "features_used": self._features,
        }


