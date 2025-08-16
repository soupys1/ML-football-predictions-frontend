from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional, Sequence

import joblib
import numpy as np
import pandas as pd
from .csv_loader import read_csv_smart
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
PIPELINE_PATH = os.path.join(ARTIFACT_DIR, "football_pipeline.joblib")
COLUMNS_PATH = os.path.join(ARTIFACT_DIR, "feature_columns.joblib")


DEFAULT_FEATURES: Sequence[str] = (
    "attack_strength",
    "defense_strength",
    "goal_diff",
    "win_rate",
)


@dataclass
class TeamProba:
    team: str
    probability: float


class FootballChampionModel:
    def __init__(self) -> None:
        self.pipeline: Optional[Pipeline] = None
        self.feature_columns: List[str] = []

    def _build_pipeline(self, feature_columns: Sequence[str]) -> Pipeline:
        numeric_features = list(feature_columns)
        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "num",
                    Pipeline(
                        steps=[
                            ("imputer", SimpleImputer(strategy="median")),
                            ("scaler", StandardScaler()),
                        ]
                    ),
                    numeric_features,
                )
            ],
            remainder="drop",
        )
        # Logistic regression works well for calibrated probabilities
        clf = LogisticRegression(max_iter=200)
        return Pipeline(steps=[("prep", preprocessor), ("clf", clf)])

    def load(self) -> bool:
        if os.path.exists(PIPELINE_PATH) and os.path.exists(COLUMNS_PATH):
            self.pipeline = joblib.load(PIPELINE_PATH)
            self.feature_columns = joblib.load(COLUMNS_PATH)
            return True
        return False

    def save(self) -> None:
        os.makedirs(ARTIFACT_DIR, exist_ok=True)
        joblib.dump(self.pipeline, PIPELINE_PATH)
        joblib.dump(self.feature_columns, COLUMNS_PATH)

    def train_from_dataframe(self, df: pd.DataFrame, features: Optional[Sequence[str]] = None) -> None:
        if features is None:
            # Infer features if not provided
            features = [
                c
                for c in df.columns
                if c not in {"team", "season", "champion"} and np.issubdtype(df[c].dtype, np.number)
            ] or list(DEFAULT_FEATURES)

        if "champion" not in df.columns:
            raise ValueError("Dataset must include a 'champion' column with 1 for champions, 0 otherwise")
        if "team" not in df.columns:
            raise ValueError("Dataset must include a 'team' column")

        X = df[features].copy()
        y = df["champion"].astype(int).values
        self.feature_columns = list(features)
        self.pipeline = self._build_pipeline(self.feature_columns)
        self.pipeline.fit(X, y)
        self.save()

    def train_from_csv(self, csv_path: str, features: Optional[Sequence[str]] = None) -> None:
        df = read_csv_smart(csv_path)
        self.train_from_dataframe(df, features)

    def predict_proba(self, df_candidates: pd.DataFrame) -> List[TeamProba]:
        if not self.pipeline or not self.feature_columns:
            raise RuntimeError("Model not trained. Train first.")
        if "team" not in df_candidates.columns:
            raise ValueError("Candidates must include a 'team' column")
        X = df_candidates[self.feature_columns].copy()
        probs = self.pipeline.predict_proba(X)[:, 1]
        return [TeamProba(team=t, probability=float(p)) for t, p in zip(df_candidates["team"].values, probs)]


