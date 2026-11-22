"""Free-text symptom triage.

Rule-based pattern matching with simple negation handling. Conservative by
design: the rules can only raise urgency, never rule anything out, and any
text that matches nothing returns a baseline "routine self-check" message
rather than reassurance. It was written and tested by the developer and has
not been validated on real patient language.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from .safety import LEVELS, max_level

_NEGATION = re.compile(r"\b(no|not|without|never|neither|dont|don't|denies)\b", re.I)


@dataclass(frozen=True)
class Rule:
    key: str
    pattern: re.Pattern
    level: str
    label: str
    advice: str


def _rx(*alternatives: str) -> re.Pattern:
    return re.compile("|".join(alternatives), re.I)


RULES: List[Rule] = [
    Rule(
        "sudden_testicular_pain",
        _rx(r"sudden(ly)? .{0,30}(severe )?pain", r"severe .{0,20}pain .{0,30}(testicle|testicular|ball|groin|scrotum)",
            r"severe .{0,15}(testicular|testicle|scrotal|groin|ball)[a-z]* .{0,10}pain",
            r"(testicle|testicular|ball) .{0,20}(is |feels )?(so |very )?(painful|killing)"),
        "emergency",
        "Sudden severe testicular pain",
        "Possible testicular torsion. Go to an emergency department now - hours matter.",
    ),
    Rule(
        "testicular_twist",
        _rx(r"twist(ed)? .{0,20}(testicle|ball)", r"(testicle|ball) .{0,20}twist"),
        "emergency",
        "Pain suggesting torsion",
        "Possible testicular torsion. Go to an emergency department now - hours matter.",
    ),
    Rule(
        "swelling_fever",
        _rx(r"(swollen|swelling) .{0,40}(fever|hot|temperature)", r"fever .{0,40}(swollen|swelling|testicle|scrotum)"),
        "urgent",
        "Swelling with fever",
        "See a doctor today; this can be an infection that needs treatment.",
    ),
    Rule(
        "lump",
        _rx(r"\blump\b", r"\bbump\b", r"hard (area|spot|mass|node)", r"\bswollen (testicle|ball|node)"),
        "urgent",
        "Lump or hard area",
        "Book a urology appointment within days. Most lumps are benign, but this must be checked.",
    ),
    Rule(
        "blood_in_semen",
        _rx(r"blood in (my )?(semen|sperm|ejaculate)", r"blood .{0,15}(ejaculat|semen|sperm)",
            r"(semen|sperm|ejaculate) .{0,15}blood"),
        "routine",
        "Blood in semen",
        "Usually benign once, but recurring episodes deserve a routine urology visit.",
    ),
    Rule(
        "blood_in_urine",
        _rx(r"blood in (my )?urine", r"urine .{0,15}blood", r"pee(ing)? blood"),
        "urgent",
        "Blood in urine",
        "Blood in urine always needs a medical check. Book a doctor's appointment soon.",
    ),
    Rule(
        "pain_urination",
        _rx(r"(pain|burn|sting).{0,20}(urinat|pee)", r"(urinat|pee).{0,20}(pain|burn|sting)"),
        "routine",
        "Pain when urinating",
        "Often a urinary or prostate infection; book a routine doctor visit and mention STI testing.",
    ),
    Rule(
        "discharge",
        _rx(r"\bdischarge\b", r"pus"),
        "routine",
        "Penile discharge",
        "Needs STI testing; book a routine visit or a sexual-health clinic.",
    ),
    Rule(
        "infertility_duration",
        _rx(r"(trying|try) .{0,25}(year|12 months|18 months|2 years)", r"(no|not) pregnant .{0,20}(year|months)"),
        "routine",
        "Difficulty conceiving",
        "After 12 months of trying, both partners should get a fertility workup; start with a semen analysis.",
    ),
    Rule(
        "low_libido_hormonal",
        _rx(r"(low|no|lost) (sex ?drive|libido)", r"(sex ?drive|libido) .{0,25}(low|gone|dropped|disappeared)",
            r"breast (tissue|growth|enlargement)", r"(losing|loss of) (body |facial )?hair"),
        "routine",
        "Possible hormonal symptoms",
        "Possible hormonal issue; ask a doctor about hormone blood tests.",
    ),
    Rule(
        "dull_ache",
        _rx(r"(dull|mild) (ache|pain|discomfort) .{0,30}(testicle|scrotum|groin|ball)",
            r"(testicle|scrotum|groin|ball) .{0,20}(dull|mild) (ache|pain)"),
        "routine",
        "Ongoing dull ache",
        "A persistent dull ache (for example a varicocele) is worth a routine urology visit.",
    ),
]


def _is_negated(text: str, start: int) -> bool:
    """True when a negation word appears shortly before the match."""
    window = text[max(0, start - 40):start]
    return bool(_NEGATION.search(window))


def analyze_text(text: str) -> Dict[str, object]:
    """Triage a free-text symptom description."""
    flags = []
    for rule in RULES:
        for match in rule.pattern.finditer(text):
            if _is_negated(text, match.start()):
                continue
            flags.append(
                {
                    "key": rule.key,
                    "label": rule.label,
                    "level": rule.level,
                    "advice": rule.advice,
                    "matched": match.group(0).strip(),
                }
            )
            break  # one hit per rule is enough
    level = max_level([f["level"] for f in flags])
    if not flags:
        note = (
            "No red-flag pattern matched. This tool can miss things: if something "
            "worries you, or symptoms persist or worsen, see a doctor."
        )
        level = "ok"
    else:
        note = "This triage can only raise urgency, never rule anything out."
    return {
        "level": level,
        "flags": flags,
        "note": note,
        "disclaimer": "Rule-based screening, not a diagnosis.",
      }
