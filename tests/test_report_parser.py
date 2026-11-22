from repro360.report_parser import parse_report, parse_pairs


REPORT = """Semen analysis report
Volume: 2.1 mL
Sperm concentration: 45 million/mL
Total motility (PR+NP): 38%
Progressive motility: 32%
Vitality: 60%
Morphology normal forms: 3%
pH: 7.4
Doctor comment: repeat in 3 months
"""


def test_parses_common_labels():
    result = parse_report(REPORT)
    assert result.measurements["volume"] == 2.1
    assert result.measurements["concentration"] == 45.0
    assert result.measurements["progressive_motility"] == 32.0
    assert result.measurements["ph"] == 7.4


def test_unparsed_lines_kept():
    result = parse_report(REPORT)
    assert any("Doctor comment" in line for line in result.unparsed_lines)


def test_decimal_comma():
    result = parse_report("Volume: 2,5 mL")
    assert result.measurements["volume"] == 2.5


def test_empty_text():
    result = parse_report("")
    assert result.measurements == {}
    assert result.unparsed_lines == []


def test_matched_line_recorded():
    result = parse_report("Volume: 2.1 mL")
    assert "volume" in result.matched


def test_parse_pairs_normalizes_labels():
    out = parse_pairs([("Sperm concentration", 30.0), ("pH", 7.3)])
    assert out == {"concentration": 30.0, "ph": 7.3}
