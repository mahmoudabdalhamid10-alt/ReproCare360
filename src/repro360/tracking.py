"""Trend and timing helpers for the journal.

Spermatogenesis takes roughly 74 days, so a lifestyle change (or a fever,
or a course of medication) needs about 10-12 weeks before it can show up in
a semen analysis. Retesting earlier mostly measures noise.
"""

from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional, Sequence

SPERM_CYCLE_DAYS = 74


def trend(values: Sequence[float]) -> str:
    """Classify a series as 'improving', 'declining' or 'stable'.

    Uses a plain least-squares slope; a series shorter than 3 points is
    always 'insufficient_data'. A slope within +/-5% of the mean per step
    counts as stable.
    """
    if len(values) < 3:
        return "insufficient_data"
    n = len(values)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(values) / n
    denom = sum((x - mean_x) ** 2 for x in xs)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values)) / denom
    if mean_y == 0:
        return "stable" if slope == 0 else ("improving" if slope > 0 else "declining")
    rel = slope / abs(mean_y)
    if abs(rel) < 0.05:
        return "stable"
    return "improving" if slope > 0 else "declining"


def next_test_date(last_test: dt.date, today: Optional[dt.date] = None) -> Dict[str, object]:
    """When a repeat semen test becomes meaningful after ``last_test``."""
    today = today or dt.date.today()
    earliest = last_test + dt.timedelta(days=SPERM_CYCLE_DAYS)
    remaining = (earliest - today).days
    return {
        "last_test": last_test.isoformat(),
        "earliest_meaningful": earliest.isoformat(),
        "days_remaining": max(0, remaining),
        "ready": remaining <= 0,
        "cycle_days": SPERM_CYCLE_DAYS,
    }


def parameter_series(lab_rows: List[Dict[str, object]], parameter: str) -> List[float]:
    """Extract the value series for one parameter from store rows."""
    return [float(r["value"]) for r in lab_rows if r.get("parameter") == parameter]
