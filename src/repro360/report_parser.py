"""Parse a pasted semen-analysis lab report into structured measurements.

Lab printouts differ wildly between labs, so this parser is deliberately
simple: each line is scanned for a known parameter label followed by a
number. Lines that cannot be understood are returned untouched so the user
can enter them manually. Nothing is guessed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .who_reference import PARAMETERS

# label variants (lowercase, no punctuation) -> parameter key
LABELS: Dict[str, str] = {
    "volume": "volume",
    "semen volume": "volume",
    "ejaculate volume": "volume",
    "concentration": "concentration",
    "sperm concentration": "concentration",
    "sperm count": "concentration",
    "count": "concentration",
    "density": "concentration",
    "total sperm number": "total_count",
    "total count": "total_count",
    "total sperm count": "total_count",
    "progressive motility": "progressive_motility",
    "progressive": "progressive_motility",
    "pr": "progressive_motility",
    "motility": "total_motility",
    "total motility": "total_motility",
    "pr np": "total_motility",
    "vitality": "vitality",
    "viability": "vitality",
    "live spermatozoa": "vitality",
    "morphology": "normal_morphology",
    "normal forms": "normal_morphology",
    "normal morphology": "normal_morphology",
    "normal forms strict": "normal_morphology",
    "ph": "ph",
}

_NUMBER = re.compile(r"(-?\d+(?:[.,]\d+)?)")


@dataclass
class ParseResult:
    measurements: Dict[str, float] = field(default_factory=dict)
    unparsed_lines: List[str] = field(default_factory=list)
    matched: Dict[str, str] = field(default_factory=dict)  # key -> original line


def _normalise_label(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[/()%\[\].:*-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _match_label(line: str) -> Optional[str]:
    norm = _normalise_label(line)
    # longest label first so "total sperm number" wins over "count"
    for label in sorted(LABELS, key=len, reverse=True):
        if label in norm:
            return LABELS[label]
    return None


def parse_report(text: str) -> ParseResult:
    """Parse free text (one finding per line) into measurements.

    The first number on a matched line is taken as the value; ranges like
    "39-60" therefore resolve to the first figure, which mirrors how labs
    print "result (reference range)" only when the result comes first.
    """
    result = ParseResult()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        key = _match_label(line)
        if key is None:
            result.unparsed_lines.append(line)
            continue
        tail = line[line.lower().find(":") + 1:] if ":" in line else line
        match = _NUMBER.search(tail)
        if not match:
            result.unparsed_lines.append(line)
            continue
        value = float(match.group(1).replace(",", "."))
        result.measurements[key] = value
        result.matched[key] = line
    return result


def parse_pairs(pairs: List[Tuple[str, float]]) -> Dict[str, float]:
    """Normalize (label, value) pairs from a form into parameter keys."""
    out: Dict[str, float] = {}
    for label, value in pairs:
        key = _match_label(label) or _normalise_label(label)
        if key in PARAMETERS:
            out[key] = float(value)
    return out
