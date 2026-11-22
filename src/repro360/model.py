"""Lifestyle model: calibrated classifier on the UCI Fertility data.

Flagged as experimental. On this tiny, imbalanced dataset (100 men, 12
"altered") the model does not beat chance by much, if at all; the honest
metrics live in models/metrics.json and are repeated in the README.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import (RepeatedStratifiedKFold, StratifiedKFold,
                                     cross_val_predict, cross_val_score)

from .data import feature_target, load_fertility

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"


def _build() -> CalibratedClassifierCV:
    base = LogisticRegression(max_iter=2000, class_weight="balanced")
    return CalibratedClassifierCV(base, cv=3, method="isotonic")


def evaluate() -> Dict[str, object]:
    df = load_fertility()
    X, y = feature_target(df)

    aucs = []
    for seed in range(3):
        cv_i = RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=seed)
        aucs.extend(cross_val_score(_build(), X, y, cv=cv_i, scoring="roc_auc"))

    # Brier needs out-of-fold probabilities, so use a plain 5-fold partition.
    proba = cross_val_predict(_build(), X, y, cv=StratifiedKFold(5, shuffle=True, random_state=42),
                              method="predict_proba")[:, 1]
    briers = [brier_score_loss(y, proba)]
    dummy = DummyClassifier(strategy="prior").fit(X, y)
    briers_dummy = [brier_score_loss(y, dummy.predict_proba(X)[:, 1])]

    auc_mean = float(np.mean(aucs))
    auc_std = float(np.std(aucs))
    return {
        "n_samples": int(len(df)),
        "n_altered": int(y.sum()),
        "cv": "10x repeated 5-fold (3 seeds)",
        "auc_mean": round(auc_mean, 3),
        "auc_std": round(auc_std, 3),
        "brier": round(float(np.mean(briers)), 3),
        "brier_constant_baseline": round(float(np.mean(briers_dummy)), 3),
        "verdict": (
            "AUC within noise of 0.5 and Brier no better than a constant "
            "prediction: the model does not predict better than chance."
            if abs(auc_mean - 0.5) < 2 * auc_std
            else "AUC above noise; treat with caution, n is tiny."
        ),
        "experimental": True,
    }


def train() -> Dict[str, object]:
    """Evaluate with CV, fit on all data, persist model + metrics."""
    df = load_fertility()
    X, y = feature_target(df)
    metrics = evaluate()
    model = _build().fit(X, y)
    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump({"model": model, "features": list(X.columns)}, MODELS_DIR / "lifestyle_model.joblib")
    with open(MODELS_DIR / "metrics.json", "w") as fh:
        json.dump(metrics, fh, indent=2)
    return metrics


def load_model():
    bundle = joblib.load(MODELS_DIR / "lifestyle_model.joblib")
    return bundle["model"], bundle["features"]


def predict_proba(features: Dict[str, float]) -> float:
    model, cols = load_model()
    row = [[float(features.get(c, 0.0)) for c in cols]]
    return float(model.predict_proba(row)[0][1])


def metrics() -> Dict[str, object]:
    with open(MODELS_DIR / "metrics.json") as fh:
        return json.load(fh)
