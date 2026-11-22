from repro360.pathway import next_steps


def test_baseline_advice_without_analysis():
    result = next_steps(trying_months=3, has_semen_analysis=False)
    titles = [s["title"] for s in result["steps"]]
    assert any("baseline semen analysis" in t for t in titles)


def test_twelve_months_triggers_workup():
    result = next_steps(trying_months=14, has_semen_analysis=False)
    assert any("fertility workup" in s["title"] for s in result["steps"])


def test_low_concentration_triggers_hormone_and_genetic():
    result = next_steps(has_semen_analysis=True, concentration=3.0)
    titles = [s["title"] for s in result["steps"]]
    assert any("genetic" in t.lower() for t in titles)
    assert any("hormone" in t.lower() for t in titles)


def test_steps_are_ordered_and_sourced():
    result = next_steps(trying_months=20, smokes=True, sitting_hours=10)
    orders = [s["order"] for s in result["steps"]]
    assert orders == list(range(1, len(orders) + 1))
    assert all(s["sources"] for s in result["steps"])
