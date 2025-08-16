import os
import sys
from typing import Tuple

import numpy as np
import pandas as pd
from backend.ml.csv_loader import read_csv_smart


def _find_column(df: pd.DataFrame, candidates: Tuple[str, ...]) -> str:
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in lower_map:
            return lower_map[cand]
    raise KeyError(f"None of columns {candidates} found in dataset")


def build_team_season_features(raw_csv: str, out_csv: str) -> None:
    df = read_csv_smart(raw_csv)
    # Normalize column names for flexible datasets
    lower_map = {c.lower(): c for c in df.columns}

    season_col = _find_column(df, ("season", "year", "yr"))
    home_col = _find_column(df, ("home", "hometeam"))
    away_col = _find_column(df, ("visitor", "away", "awayteam"))
    hgoal_col = _find_column(df, ("hgoal", "fthg", "home_goals", "hg"))
    agoal_col = _find_column(df, ("vgoal", "ftag", "away_goals", "ag"))

    rows = []
    for _, r in df.iterrows():
        season = r[season_col]
        ht = r[home_col]
        at = r[away_col]
        hg = r[hgoal_col]
        ag = r[agoal_col]
        try:
            hg = float(hg)
            ag = float(ag)
        except Exception:
            # Skip malformed rows
            continue
        # Home
        rows.append(
            dict(
                season=season,
                team=ht,
                wins=float(hg > ag),
                draws=float(hg == ag),
                losses=float(hg < ag),
                goals_for=hg,
                goals_against=ag,
            )
        )
        # Away
        rows.append(
            dict(
                season=season,
                team=at,
                wins=float(ag > hg),
                draws=float(ag == hg),
                losses=float(ag < hg),
                goals_for=ag,
                goals_against=hg,
            )
        )

    m = pd.DataFrame(rows)
    agg = (
        m.groupby(["season", "team"], as_index=False)
        .sum(numeric_only=True)
        .assign(
            points=lambda x: x["wins"] * 3 + x["draws"],
            goal_diff=lambda x: x["goals_for"] - x["goals_against"],
            matches=lambda x: x["wins"] + x["draws"] + x["losses"],
        )
    )
    agg["win_rate"] = (agg["wins"] / agg["matches"]).fillna(0.0)
    agg = agg.drop(columns=["matches"]).copy()

    # Mark champions per season by points then goal_diff
    agg["champion"] = 0
    for season, g in agg.groupby("season"):
        idx = g.sort_values(["points", "goal_diff"], ascending=[False, False]).index[0]
        agg.loc[idx, "champion"] = 1

    # Keep only required numeric features and columns
    cols = [
        "team",
        "season",
        "goals_for",
        "goals_against",
        "goal_diff",
        "wins",
        "draws",
        "losses",
        "points",
        "win_rate",
        "champion",
    ]
    agg[cols].to_csv(out_csv, index=False)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python prepare_england_dataset.py <raw_csv> <out_csv>")
        sys.exit(1)
    build_team_season_features(sys.argv[1], sys.argv[2])


