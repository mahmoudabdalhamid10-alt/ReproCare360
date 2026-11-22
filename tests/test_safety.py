from repro360.safety import CHECKLIST, evaluate_checklist, max_level


def test_no_flags_means_ok():
    result = evaluate_checklist({item.key: False for item in CHECKLIST})
    assert result["level"] == "ok"
    assert result["flags"] == []


def test_emergency_beats_routine():
    result = evaluate_checklist({"sudden_severe_pain": True, "infertility_12_months": True})
    assert result["level"] == "emergency"
    assert len(result["flags"]) == 2


def test_missing_answers_never_downgrade():
    # answering only one urgent flag (others unanswered) still escalates
    result = evaluate_checklist({"painless_lump": True})
    assert result["level"] == "urgent"


def test_unknown_keys_ignored():
    result = evaluate_checklist({"not_a_real_key": True})
    assert result["level"] == "ok"


def test_max_level_ordering():
    assert max_level(["routine", "emergency", "urgent"]) == "emergency"
    assert max_level([]) == "ok"
