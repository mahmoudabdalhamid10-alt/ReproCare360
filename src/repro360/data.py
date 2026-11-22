"""Load the UCI Fertility dataset.

Source: UCI Machine Learning Repository, "Fertility" (100 volunteers,
9 features + diagnosis: N = normal, O = altered). All features were
normalized by the donors; the sitting-hours scale is not documented, so
this project assumes a 16-hour maximum (see README limitations).
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

FEATURES = [
    "season",
    "age",
    "childish_diseases",
    "accident",
    "surgical_intervention",
    "high_fevers",
    "alcohol",
    "smoking",
    "sitting_hours",
]
TARGET = "diagnosis"
SITTING_HOURS_MAX = 16.0  # assumed; the donors did not document the scale


def load_fertility(path: Path | None = None) -> pd.DataFrame:
    path = path or (DATA_DIR / "fertility.csv")
    df = pd.read_csv(path)
    df["sitting_hours_denorm"] = df["sitting_hours"] * SITTING_HOURS_MAX
    return df


def feature_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    X = df[FEATURES]
    y = (df[TARGET] == "O").astype(int)  # 1 = altered
    return X, y
