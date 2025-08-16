from __future__ import annotations

import os
from typing import Dict, Iterable, List, Tuple

import joblib
import numpy as np
import pandas as pd
from .csv_loader import read_csv_smart
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from .game_winner_model import ARTIFACT_DIR, MODEL_PATH, FEATURES_PATH


def _numeric_cols(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if np.issubdtype(df[c].dtype, np.number)]


def aggregate_team_features(teams_csv: str, players_csv: str | None = None) -> pd.DataFrame:
    teams = read_csv_smart(teams_csv)
    # Try to detect team id column
    team_id_col = next((c for c in teams.columns if c.lower() in ("teamid", "id", "team_id")), None)
    if team_id_col is None:
        raise ValueError("teams.csv must include a teamID/id column")
    
    # Remove duplicates and create a simple team index
    team_numeric = teams[[team_id_col]].drop_duplicates(subset=[team_id_col], keep='first').set_index(team_id_col)
    
    # Add a dummy column to make it a proper DataFrame
    team_numeric['dummy'] = 1.0

    if players_csv and os.path.exists(players_csv):
        players = read_csv_smart(players_csv)
        # Detect join key
        pid_team_col = next((c for c in players.columns if c.lower() in ("teamid", "team_id", "team")), None)
        if pid_team_col is not None:
            # Common useful aggregates if columns exist
            agg_map: Dict[str, Tuple[str, str]] = {}
            for col in players.columns:
                lc = col.lower()
                if lc in ("rating", "overall", "ovr", "score"):
                    agg_map[col] = ("rating_mean", "mean")
                elif lc in ("age",):
                    agg_map[col] = ("age_mean", "mean")
                elif lc in ("value", "marketvalue", "market_value"):
                    agg_map[col] = ("value_sum", "sum")
                elif lc in ("minutes", "mins", "minute_played", "minutesplayed"):
                    agg_map[col] = ("minutes_sum", "sum")
                elif lc in ("goals", "goals_scored"):
                    agg_map[col] = ("goals_sum", "sum")
                elif lc in ("assists",):
                    agg_map[col] = ("assists_sum", "sum")

            if agg_map:
                grouped = players.groupby(pid_team_col).agg(
                    **{new: pd.NamedAgg(column=col, aggfunc=func) for col, (new, func) in agg_map.items()}
                )
                team_numeric = team_numeric.join(grouped, how="left")

    # Fill NaNs with zeros for stability
    team_numeric = team_numeric.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return team_numeric


def build_match_features_for_row(home_id: int, away_id: int, team_feats: pd.DataFrame) -> Dict[str, float]:
    # For each team feature column, build H_/A_ prefixed features
    feature_map: Dict[str, float] = {}
    if home_id not in team_feats.index or away_id not in team_feats.index:
        # If missing team rows, return empty to be skipped
        return feature_map
    for col in team_feats.columns:
        feature_map[f"H_{col}"] = float(team_feats.loc[home_id, col])
        feature_map[f"A_{col}"] = float(team_feats.loc[away_id, col])
    return feature_map


def train_from_games_teams_players(
    games_csv: str,
    teams_csv: str,
    players_csv: str | None = None,
    save_to_paths: Tuple[str, str] | None = None,
) -> Dict[str, object]:
    df = read_csv_smart(games_csv)
    # Detect columns
    def find(col_names: Iterable[str]) -> str:
        lower = {c.lower(): c for c in df.columns}
        for name in col_names:
            if name.lower() in lower:
                return lower[name.lower()]
        raise KeyError(f"None of {col_names} found in games.csv")

    home_team_col = find(["homeTeamID", "home", "home_id"]) 
    away_team_col = find(["awayTeamID", "away", "away_id"]) 
    home_goals_col = find(["homeGoals", "FTHG", "home_goals"]) 
    away_goals_col = find(["awayGoals", "FTAG", "away_goals"]) 

    team_feats = aggregate_team_features(teams_csv, players_csv)

    rows: List[Dict[str, float]] = []
    labels: List[str] = []
    for _, r in df.iterrows():
        try:
            hid = int(r[home_team_col])
            aid = int(r[away_team_col])
        except Exception:
            continue
        feats = build_match_features_for_row(hid, aid, team_feats)
        if not feats:
            continue
        rows.append(feats)
        hg = float(r[home_goals_col])
        ag = float(r[away_goals_col])
        if hg > ag:
            labels.append("Home")
        elif ag > hg:
            labels.append("Away")
        else:
            labels.append("Draw")

    if not rows:
        raise ValueError("No training rows produced. Check teams/players files have matching team IDs with games.csv")

    X = pd.DataFrame(rows)
    y = pd.Series(labels)

    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    clf = RandomForestClassifier(n_estimators=300, random_state=42)
    clf.fit(X_train, y_train)
    acc = accuracy_score(y_test, clf.predict(X_test))

    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    model_path, features_path = (save_to_paths if save_to_paths else (MODEL_PATH, FEATURES_PATH))
    joblib.dump(clf, model_path)
    with open(features_path, "w", encoding="utf-8") as f:
        import json
        json.dump({"features": list(X.columns)}, f)

    return {"trained_samples": int(len(X)), "features": list(X.columns), "accuracy": float(acc)}


def _detect_col(df: pd.DataFrame, options: list[str]) -> str | None:
    lower = {c.lower(): c for c in df.columns}
    for o in options:
        if o.lower() in lower:
            return lower[o.lower()]
    return None


def rank_mvp_candidates(
    players_csv: str,
    home_team_id: int,
    away_team_id: int,
    top_k: int = 5,
) -> list[dict]:
    if not os.path.exists(players_csv):
        return []
    p = read_csv_smart(players_csv)

    team_col = _detect_col(p, ["teamID", "team_id", "team"])
    name_col = _detect_col(p, ["name", "player", "player_name"])
    id_col = _detect_col(p, ["playerID", "player_id", "id"]) or name_col

    if team_col is None or name_col is None:
        return []

    subset = p[p[team_col].isin([home_team_id, away_team_id])].copy()
    if subset.empty:
        return []

    # Score components (optional, if present)
    rating_col = _detect_col(subset, ["rating", "overall", "ovr", "score"]) 
    goals_col = _detect_col(subset, ["goals", "goals_scored"]) 
    assists_col = _detect_col(subset, ["assists"]) 
    minutes_col = _detect_col(subset, ["minutes", "mins", "minute_played", "minutesplayed"]) 

    # Normalize helpers
    def norm(series: pd.Series) -> pd.Series:
        s = pd.to_numeric(series, errors="coerce").fillna(0.0)
        if s.max() == s.min():
            return pd.Series(0.0, index=s.index)
        return (s - s.min()) / (s.max() - s.min())

    score = pd.Series(0.0, index=subset.index)
    if rating_col:
        score = score + 0.45 * norm(subset[rating_col])
    if goals_col:
        score = score + 0.30 * norm(subset[goals_col])
    if assists_col:
        score = score + 0.15 * norm(subset[assists_col])
    if minutes_col:
        score = score + 0.10 * norm(subset[minutes_col])

    subset["_score"] = score
    subset = subset.sort_values("_score", ascending=False).head(top_k)

    total = subset["_score"].sum() or 1.0
    results: list[dict] = []
    for _, r in subset.iterrows():
        results.append(
            {
                "playerId": None if id_col is None else r[id_col],
                "name": str(r[name_col]),
                "teamId": int(r[team_col]) if not pd.isna(r[team_col]) else None,
                "score": float(r["_score"]),
                "probability": float(r["_score"]) / float(total),
            }
        )
    return results


def rank_top_players_for_team(
    players_csv: str,
    team_id: int,
    top_k: int = 5,
) -> list[dict]:
    """Return top-K players for a single team using the same weighted heuristic.

    Heuristic weights (if columns exist): rating 45%, goals 30%, assists 15%, minutes 10%.
    """
    if not os.path.exists(players_csv):
        return []
    p = read_csv_smart(players_csv)

    team_col = _detect_col(p, ["teamID", "team_id", "team"])
    name_col = _detect_col(p, ["name", "player", "player_name"])
    id_col = _detect_col(p, ["playerID", "player_id", "id"]) or name_col
    if team_col is None or name_col is None:
        return []
    subset = p[p[team_col] == team_id].copy()
    if subset.empty:
        return []

    rating_col = _detect_col(subset, ["rating", "overall", "ovr", "score"]) 
    goals_col = _detect_col(subset, ["goals", "goals_scored"]) 
    assists_col = _detect_col(subset, ["assists"]) 
    minutes_col = _detect_col(subset, ["minutes", "mins", "minute_played", "minutesplayed"]) 

    def norm(series: pd.Series) -> pd.Series:
        s = pd.to_numeric(series, errors="coerce").fillna(0.0)
        if s.max() == s.min():
            return pd.Series(0.0, index=s.index)
        return (s - s.min()) / (s.max() - s.min())

    score = pd.Series(0.0, index=subset.index)
    if rating_col:
        score = score + 0.45 * norm(subset[rating_col])
    if goals_col:
        score = score + 0.30 * norm(subset[goals_col])
    if assists_col:
        score = score + 0.15 * norm(subset[assists_col])
    if minutes_col:
        score = score + 0.10 * norm(subset[minutes_col])

    subset["_score"] = score
    subset = subset.sort_values("_score", ascending=False).head(top_k)

    total = subset["_score"].sum() or 1.0
    out: list[dict] = []
    for _, r in subset.iterrows():
        out.append({
            "playerId": None if id_col is None else r[id_col],
            "name": str(r[name_col]),
            "teamId": int(team_id),
            "score": float(r["_score"]),
            "probability": float(r["_score"]) / float(total),
        })
    return out


