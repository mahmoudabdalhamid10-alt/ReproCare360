"""WHO 2021 (6th edition) lower reference limits for semen analysis.

The limits below are the 5th centile lower reference limits published in the
WHO laboratory manual for the examination and processing of human semen,
6th edition (2021). They are *lower* limits: a value below the limit is
flagged as "low", at or above it is "ok".

This module only compares numbers; it never interprets them medically.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Parameter:
    key: str
    label: str
    unit: str
    lower_limit: float


# The 8 parameters tracked by the Semen Lab module.
PARAMETERS: Dict[str, Parameter] = {
    "volume": Parameter("volume", "Semen volume", "mL", 1.4),
    "concentration": Parameter("concentration", "Sperm concentration", "M/mL", 16.0),
    "total_count": Parameter("total_count", "Total sperm number", "M", 39.0),
    "progressive_motility": Parameter("progressive_motility", "Progressive motility", "%", 30.0),
    "total_motility": Parameter("total_motility", "Total motility", "%", 42.0),
    "vitality": Parameter("vitality", "Vitality", "%", 54.0),
    "normal_morphology": Parameter("normal_morphology", "Normal forms", "%", 4.0),
    "ph": Parameter("ph", "pH", "", 7.2),
}


@dataclass
class ParameterResult:
    key: str
    label: str
    value: float
    unit: str
    lower_limit: float
    status: str  # "ok" | "low"

    def as_dict(self) -> dict:
        return asdict(self)


def assess(measurements: Dict[str, float]) -> List[ParameterResult]:
    """Compare measured values against the WHO lower reference limits.

    Unknown parameter keys are ignored silently so callers can pass a
    superset of fields; missing parameters are simply not reported.
    """
    results: List[ParameterResult] = []
    for key, param in PARAMETERS.items():
        if key not in measurements or measurements[key] is None:
            continue
        value = float(measurements[key])
        status = "ok" if value >= param.lower_limit else "low"
        results.append(
            ParameterResult(
                key=key,
                label=param.label,
                value=value,
                unit=param.unit,
                lower_limit=param.lower_limit,
                status=status,
            )
        )
    return results


def low_parameters(measurements: Dict[str, float]) -> List[str]:
    """Return just the keys of parameters below the lower limit."""
    return [r.key for r in assess(measurements) if r.status == "low"]


def reference_table() -> List[dict]:
    """The full reference table, used by the API and the dashboard."""
    return [asdict(p) for p in PARAMETERS.values()]


def find_parameter(name: str) -> Optional[Parameter]:
    return PARAMETERS.get(name)
