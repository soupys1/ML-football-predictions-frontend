from __future__ import annotations

import argparse
import json
import os
from typing import List

import joblib
import pandas as pd
from backend.ml.csv_loader import read_csv_smart
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


FEATURES: List[str] = [
    "homeProbability", "drawProbability", "awayProbability",
    "B365H", "B365D", "B365A",
    "BWH", "BWD", "BWA",
    "IWH", "IWD", "IWA",
    "PSH", "PSD", "PSA",
    "WHH", "WHD", "WHA",
    "VCH", "VCD", "VCA",
    "PSCH", "PSCD", "PSCA",
]


def derive_winner_label(row) -> str:
    if row["homeGoals"] > row["awayGoals"]:
        return "Home"
    if row["awayGoals"] > row["homeGoals"]:
        return "Away"
    return "Draw"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Path to games.csv")
    parser.add_argument("--outdir", default=os.path.join(os.path.dirname(__file__), "..", "ml", "artifacts"))
    args = parser.parse_args()

    df = read_csv_smart(args.csv)

    # Ensure required columns exist
    missing_for_label = [c for c in ["homeGoals", "awayGoals"] if c not in df.columns]
    if missing_for_label:
        raise SystemExit(f"Missing required columns for label: {missing_for_label}")

    # Winner label
    df["winner"] = df.apply(derive_winner_label, axis=1)

    # Filter to available features
    available_features = [c for c in FEATURES if c in df.columns]
    if not available_features:
        raise SystemExit("None of the expected feature columns were found in the CSV")

    X = df[available_features].copy()
    y = df["winner"].copy()

    # Drop rows with missing values in used columns
    data = pd.concat([X, y], axis=1).dropna()
    X = data[available_features]
    y = data["winner"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print("Accuracy:", round(acc, 4))
    print(classification_report(y_test, y_pred))

    # Save artifacts
    os.makedirs(args.outdir, exist_ok=True)
    model_path = os.path.join(args.outdir, "game_winner_rf.joblib")
    cols_path = os.path.join(args.outdir, "game_winner_rf_features.json")
    joblib.dump(model, model_path)
    with open(cols_path, "w", encoding="utf-8") as f:
        json.dump({"features": available_features}, f)
    print(f"Saved model to {model_path}")
    print(f"Saved feature list to {cols_path}")


if __name__ == "__main__":
    main()


