# Model card: Lifestyle model (experimental)

## Summary

A calibrated logistic-regression classifier that estimates the probability of
an *altered* semen diagnosis from lifestyle and history features. **It does
not predict better than chance on the available data** and is shipped as an
honest demo, behind an "experimental" expander in the dashboard.

## Data

- UCI Machine Learning Repository, "Fertility" dataset: 100 volunteers,
  9 features, diagnosis Normal (88) vs Altered (12).
- Features: season, age, childish diseases, accident/trauma, surgical
  intervention, high fevers in the last year, alcohol frequency, smoking
  habit, hours sitting per day.
- All features were normalized by the donors. The sitting-hours scale is not
  documented; this project assumes a 16-hour maximum (`data.py`).

## Model

- `LogisticRegression(class_weight="balanced")` inside
  `CalibratedClassifierCV(cv=3, method="isotonic")`.
- Training: `make train` writes `models/lifestyle_model.joblib` and
  `models/metrics.json`.

## Evaluation

- 10x repeated 5-fold cross-validation (3 seeds) for AUC; plain 5-fold
  out-of-fold predictions for the Brier score, compared against a constant
  baseline.
- Measured: **AUC 0.57 +/- 0.19, Brier 0.107 vs 0.106 constant baseline.**
- Verdict (in `models/metrics.json`): AUC within noise of 0.5 and Brier no
  better than a constant prediction.

## Intended use

- Demonstrating an honest ML evaluation loop inside a health-awareness
  project.

## Out-of-scope use

- Any individual risk assessment, screening, or medical decision. With
  n=100 and 12 positive cases, the model cannot support one.

## Limitations

- Tiny, imbalanced, single-source dataset from 2013.
- Self-reported lifestyle features; unknown normalization scales.
- No external validation, no calibration on new data, no subgroup analysis.
