"""Safety Center: red-flag checklist triage.

The checklist can only *raise* urgency, never lower it. Any red-flag answer
escalates the result; unanswered questions never downgrade it. The levels
are, from lowest to highest: ok < routine < urgent < emergency.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

LEVELS = ["ok", "routine", "urgent", "emergency"]


@dataclass(frozen=True)
class ChecklistItem:
    key: str
    question: str
    level: str  # level when answered "yes"
    advice: str


CHECKLIST: List[ChecklistItem] = [
    ChecklistItem(
        "sudden_severe_pain",
        "Sudden, severe pain in one testicle",
        "emergency",
        "Possible testicular torsion. Go to an emergency department now - hours matter.",
    ),
    ChecklistItem(
        "swelling_with_fever",
        "Testicular swelling together with fever",
        "urgent",
        "See a doctor today; this can be an infection that needs treatment.",
    ),
    ChecklistItem(
        "painless_lump",
        "A painless lump or hard area in a testicle",
        "urgent",
        "Book a urology appointment within days. Most lumps are benign, but this must be checked.",
    ),
    ChecklistItem(
        "blood_in_semen_persistent",
        "Blood in semen more than once, or with pain",
        "routine",
        "Usually benign once, but recurring episodes deserve a routine urology visit.",
    ),
    ChecklistItem(
        "infertility_12_months",
        "12 months of unprotected sex without pregnancy",
        "routine",
        "Both partners should get a fertility workup; start with a semen analysis.",
    ),
    ChecklistItem(
        "gynaecomastia_or_low_libido",
        "Breast tissue growth, very low libido or loss of body hair",
        "routine",
        "Possible hormonal issue; ask a doctor about hormone blood tests.",
    ),
]


def max_level(levels: List[str]) -> str:
    if not levels:
        return "ok"
    return max(levels, key=lambda lv: LEVELS.index(lv))


def evaluate_checklist(answers: Dict[str, bool]) -> Dict[str, object]:
    """Evaluate {item_key: bool} answers. Unknown keys are ignored.

    Missing answers are treated as "no answer given", never as "no", so the
    result can only stay conservative.
    """
    flags = []
    for item in CHECKLIST:
        if answers.get(item.key):
            flags.append(
                {
                    "key": item.key,
                    "question": item.question,
                    "level": item.level,
                    "advice": item.advice,
                }
            )
    level = max_level([f["level"] for f in flags])
    return {
        "level": level,
        "flags": flags,
        "answered": {k: bool(v) for k, v in answers.items() if k in {i.key for i in CHECKLIST}},
        "note": "This checklist can only raise urgency, never rule anything out.",
    }


def checklist_items() -> List[dict]:
    return [asdict(i) for i in CHECKLIST]
