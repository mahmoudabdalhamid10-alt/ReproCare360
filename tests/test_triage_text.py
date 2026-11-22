import pytest

from repro360.triage_text import analyze_text

# 15 labelled regression sentences (developer-written; see README limitations)
CASES = [
    ("sudden severe pain in my left testicle", "emergency"),
    ("woke up at 3am with severe testicular pain that came out of nowhere", "emergency"),
    ("my testicle feels twisted and hurts badly", "emergency"),
    ("my scrotum is swollen and I have a fever of 39", "urgent"),
    ("swelling down there plus fever since yesterday", "urgent"),
    ("I found a small lump on my right testicle", "urgent"),
    ("there is a hard spot in my ball that does not hurt", "urgent"),
    ("I saw blood in my urine this morning", "urgent"),
    ("blood in my semen twice this month", "routine"),
    ("it burns when I pee", "routine"),
    ("dull ache in my testicle after long standing", "routine"),
    ("we have been trying for a baby for over a year", "routine"),
    ("my sex drive is very low lately", "routine"),
    ("unusual discharge since last week", "routine"),
    ("I feel fine, just checking in", "ok"),
]


@pytest.mark.parametrize("text,expected", CASES)
def test_labelled_sentences(text, expected):
    assert analyze_text(text)["level"] == expected


def test_negation_prevents_match():
    result = analyze_text("no blood in urine, no lump, feeling good")
    assert result["level"] == "ok"
    assert result["flags"] == []


def test_triage_only_raises_urgency():
    result = analyze_text("mild headache")
    assert "can miss things" in result["note"]


def test_matched_text_is_reported():
    result = analyze_text("I found a lump")
    assert result["flags"][0]["matched"]


def test_empty_flags_for_unrelated_text():
    result = analyze_text("what is the capital of france")
    assert result["flags"] == []
