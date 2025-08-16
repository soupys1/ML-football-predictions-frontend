"""
Train a match-outcome classifier on a games.csv file (match-level data).

- Auto-detects common target columns (e.g., FTR/result/winner)
- Handles basic preprocessing for numeric/categorical features
 - Encodes categorical columns (label encode for high-cardinality, one-hot for low)
 - Fills missing values
 - Splits train/test and reports accuracy + classification report

Usage:
  python scripts/train_match_outcomes.py --csv backend/data/games.csv [--target FTR] [--model random_forest]
"""

from __future__ import annotations

import argparse
from typing import List, Tuple

import numpy as np
import pandas as pd
from backend.ml.csv_loader import read_csv_smart
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC


POSSIBLE_TARGETS: Tuple[str, ...] = (
    "FTR",
    "result",
    "winner",
    "outcome",
    "match_result",
    "full_time_result",
)


class FootballDataTrainer:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df: pd.DataFrame | None = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.scaler = StandardScaler()
        self.model = None
        self.feature_names: List[str] | None = None
        self.target_column: str | None = None
        self.label_encoder: LabelEncoder | None = None

    def load_data(self) -> bool:
        try:
            self.df = read_csv_smart(self.csv_path)
            print(f"Loaded: {self.csv_path} shape={self.df.shape}")
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False

    def create_football_features(self, target_col: str) -> pd.DataFrame:
        df_processed = self.df.copy()
        # Create common engineered features when present
        if {"FTHG", "FTAG"}.issubset(df_processed.columns):
            df_processed["goal_difference"] = df_processed["FTHG"] - df_processed["FTAG"]
            df_processed["total_goals"] = df_processed["FTHG"] + df_processed["FTAG"]
        return df_processed

    def preprocess_data(self, target_column: str, test_size: float = 0.2) -> bool:
        if self.df is None:
            print("Please load data first!")
            return False
        if target_column not in self.df.columns:
            print(f"Target column '{target_column}' not found. Columns: {list(self.df.columns)}")
            return False
        self.target_column = target_column

        df_processed = self.create_football_features(target_column)
        X = df_processed.drop([target_column], axis=1)
        y = df_processed[target_column]

        # Drop identifiers and raw date strings (minimal)
        drop_cols: List[str] = []
        for col in X.columns:
            low = col.lower()
            if low in {"id", "match_id", "index", "unnamed: 0"}:
                drop_cols.append(col)
            elif X[col].dtype == "object" and ("date" in low or "time" in low):
                drop_cols.append(col)
        if drop_cols:
            X = X.drop(columns=drop_cols)

        # Fill missing values
        if X.isnull().values.any():
            num_cols = X.select_dtypes(include=[np.number]).columns
            if len(num_cols) > 0:
                X[num_cols] = X[num_cols].fillna(X[num_cols].median())
            cat_cols = X.select_dtypes(include=["object"]).columns
            if len(cat_cols) > 0:
                X[cat_cols] = X[cat_cols].fillna(X[cat_cols].mode().iloc[0])

        # Encode categorical features
        cat_cols = X.select_dtypes(include=["object"]).columns.tolist()
        if cat_cols:
            for col in list(cat_cols):
                nunique = X[col].nunique()
                if nunique > 10:
                    le = LabelEncoder()
                    X[col] = le.fit_transform(X[col].astype(str))
                else:
                    X = pd.get_dummies(X, columns=[col], prefix=col, drop_first=True)

        # Encode target if categorical string
        if y.dtype == "object" or str(y.dtype).startswith("category"):
            self.label_encoder = LabelEncoder()
            y = self.label_encoder.fit_transform(y.astype(str))
            print(f"Target classes: {list(self.label_encoder.classes_)}")

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        self.feature_names = X.columns.tolist()
        # Precompute scaled variants for linear/SVM
        self.X_train_scaled = self.scaler.fit_transform(self.X_train)
        self.X_test_scaled = self.scaler.transform(self.X_test)
        print(f"Train: {self.X_train.shape}, Test: {self.X_test.shape}, Features: {len(self.feature_names)}")
        return True

    def train_model(self, model_type: str = "random_forest") -> bool:
        if self.X_train is None:
            print("Call preprocess_data first")
            return False
        models = {
            "random_forest": RandomForestClassifier(n_estimators=200, random_state=42),
            "gradient_boosting": GradientBoostingClassifier(random_state=42),
            "logistic_regression": LogisticRegression(max_iter=1000, random_state=42),
            "svm": SVC(probability=True, random_state=42),
        }
        if model_type not in models:
            print(f"Unknown model_type '{model_type}'. Choose from {list(models)}")
            return False
        self.model = models[model_type]
        if model_type in {"svm", "logistic_regression"}:
            self.model.fit(self.X_train_scaled, self.y_train)
            y_pred = self.model.predict(self.X_test_scaled)
        else:
            self.model.fit(self.X_train, self.y_train)
            y_pred = self.model.predict(self.X_test)
        acc = accuracy_score(self.y_test, y_pred)
        print(f"Accuracy: {acc:.4f}")
        if self.label_encoder is not None:
            target_names = list(self.label_encoder.classes_)
            print(classification_report(self.y_test, y_pred, target_names=target_names))
        else:
            print(classification_report(self.y_test, y_pred))
        return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Path to games.csv")
    parser.add_argument("--target", default=None, help="Target column (auto if omitted)")
    parser.add_argument("--model", default="random_forest", help="Model type: random_forest|gradient_boosting|logistic_regression|svm")
    args = parser.parse_args()

    trainer = FootballDataTrainer(args.csv)
    if not trainer.load_data():
        return

    target = args.target
    if target is None:
        cols_lower = {c.lower(): c for c in trainer.df.columns}
        for cand in POSSIBLE_TARGETS:
            if cand.lower() in cols_lower:
                target = cols_lower[cand.lower()]
                print(f"Auto-detected target column: {target}")
                break
    if target is None:
        print(f"Could not auto-detect target. Please pass --target one of {POSSIBLE_TARGETS}")
        return

    if not trainer.preprocess_data(target):
        return
    trainer.train_model(args.model)


if __name__ == "__main__":
    main()


