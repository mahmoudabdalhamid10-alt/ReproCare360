from repro360.who_reference import PARAMETERS, assess, low_parameters, reference_table


def test_eight_parameters_defined():
    assert len(PARAMETERS) == 8


def test_who_2021_limits_values():
    assert PARAMETERS["concentration"].lower_limit == 16.0
    assert PARAMETERS["total_count"].lower_limit == 39.0
    assert PARAMETERS["progressive_motility"].lower_limit == 30.0
    assert PARAMETERS["normal_morphology"].lower_limit == 4.0


def test_assess_flags_low_values():
    results = assess({"concentration": 10.0, "volume": 2.0})
    by_key = {r.key: r for r in results}
    assert by_key["concentration"].status == "low"
    assert by_key["volume"].status == "ok"


def test_boundary_value_is_ok():
    results = assess({"concentration": 16.0})
    assert results[0].status == "ok"


def test_unknown_keys_ignored():
    assert assess({"unknown_param": 5.0}) == []


def test_low_parameters_keys():
    assert low_parameters({"ph": 7.0}) == ["ph"]


def test_reference_table_shape():
    table = reference_table()
    assert len(table) == 8
    assert {"key", "label", "unit", "lower_limit"} <= set(table[0])


def test_ph_is_lower_limit():
    assert assess({"ph": 7.1})[0].status == "low"
