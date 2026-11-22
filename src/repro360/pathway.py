"""Care Pathway: questionnaire -> ordered next-steps checklist.

Each step links to knowledge-base entries so the user can read why it is
suggested. Thresholds are approximations of published guidance (see the
project README limitations): hormone tests are suggested below about
10 M/mL concentration, genetic tests below about 5 M/mL. They must be
confirmed by a clinician.
"""

from __future__ import annotations

from typing import Dict, List, Optional

HORMONE_THRESHOLD = 10.0  # M/mL, approximate
GENETIC_THRESHOLD = 5.0   # M/mL, approximate


def _step(order: int, title: str, why: str, sources: List[str]) -> Dict[str, object]:
    return {"order": order, "title": title, "why": why, "sources": sources}


def next_steps(
    trying_months: Optional[float] = None,
    has_semen_analysis: bool = False,
    concentration: Optional[float] = None,
    smokes: Optional[bool] = None,
    heavy_alcohol: Optional[bool] = None,
    sitting_hours: Optional[float] = None,
) -> Dict[str, object]:
    """Build an ordered checklist from questionnaire answers."""
    steps: List[Dict[str, object]] = []

    if trying_months is not None and trying_months >= 12:
        steps.append(_step(
            10, "Book a fertility workup for both partners",
            "12 months of unprotected sex without pregnancy meets the common definition of infertility.",
            ["kb_infertility_definition"],
        ))
    elif trying_months is not None and trying_months >= 6:
        steps.append(_step(
            12, "Keep trying, and plan a checkup if you reach 12 months",
            "Most couples conceive within a year; evaluation is standard after 12 months (6 if the female partner is 35+).",
            ["kb_infertility_definition"],
        ))

    if not has_semen_analysis:
        steps.append(_step(
            20, "Get a baseline semen analysis",
            "It is the first, cheapest and most informative male fertility test.",
            ["kb_semen_analysis_basics", "kb_who_reference"],
        ))
    elif concentration is not None:
        if concentration < GENETIC_THRESHOLD:
            steps.append(_step(
                21, "Ask a urologist about genetic tests (karyotype, CFTR)",
                f"Very low concentration (below ~{GENETIC_THRESHOLD:.0f} M/mL) can have genetic causes. Threshold approximate - clinician confirms.",
                ["kb_genetic_testing"],
            ))
        if concentration < HORMONE_THRESHOLD:
            steps.append(_step(
                22, "Ask about hormone blood tests (FSH, LH, testosterone)",
                f"Concentration below ~{HORMONE_THRESHOLD:.0f} M/mL is a common trigger for a hormone workup. Threshold approximate - clinician confirms.",
                ["kb_hormone_testing"],
            ))
        steps.append(_step(
            23, "Repeat the semen analysis after ~10-12 weeks if anything was low",
            "A single test is noisy; the 74-day sperm cycle means retesting too early measures noise.",
            ["kb_sperm_cycle"],
        ))

    if smokes:
        steps.append(_step(
            30, "Stop smoking",
            "Smoking is consistently linked to worse semen parameters; quitting is the single highest-yield lifestyle change.",
            ["kb_smoking"],
        ))
    if heavy_alcohol:
        steps.append(_step(
            31, "Cut alcohol to low levels",
            "Heavy drinking is associated with reduced testosterone and semen quality.",
            ["kb_alcohol"],
        ))
    if sitting_hours is not None and sitting_hours >= 8:
        steps.append(_step(
            32, "Break up long sitting time and keep the groin cool",
            "Prolonged sitting and heat exposure are linked to reduced sperm quality in several studies.",
            ["kb_heat_sitting"],
        ))

    steps.append(_step(
        90, "Adopt the general evidence-based habits",
        "Sleep, exercise, weight and heat avoidance all have supporting evidence.",
        ["kb_lifestyle_overview"],
    ))

    steps.sort(key=lambda s: s["order"])
    for i, s in enumerate(steps, 1):
        s["order"] = i
    return {"steps": steps, "note": "Educational guidance, not a medical plan. Confirm thresholds with a clinician."}
