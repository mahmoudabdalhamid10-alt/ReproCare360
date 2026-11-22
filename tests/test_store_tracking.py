import datetime as dt

from repro360.store import Store
from repro360.tracking import next_test_date, parameter_series, trend


def test_store_roundtrip_entries(tmp_path):
    store = Store(tmp_path / "t.db")
    store.add_entry("note", "felt fine")
    entries = store.entries()
    assert len(entries) == 1
    assert entries[0]["note"] == "felt fine"


def test_store_lab_filter(tmp_path):
    store = Store(tmp_path / "t.db")
    store.add_lab("concentration", 20.0, "M/mL")
    store.add_lab("volume", 2.0, "mL")
    assert len(store.labs("concentration")) == 1
    assert len(store.labs()) == 2


def test_store_triage_history_flags_decoded(tmp_path):
    store = Store(tmp_path / "t.db")
    store.add_triage("urgent", [{"key": "lump"}])
    history = store.triage_history()
    assert history[0]["level"] == "urgent"
    assert history[0]["flags"] == [{"key": "lump"}]


def test_store_habits(tmp_path):
    store = Store(tmp_path / "t.db")
    store.add_habit("smoking", "quit")
    assert store.habits()[0]["value"] == "quit"


def test_store_creates_file(tmp_path):
    path = tmp_path / "sub" / "dir" / "t.db"
    Store(path)
    assert path.exists()


def test_trend_insufficient_data():
    assert trend([1.0, 2.0]) == "insufficient_data"


def test_trend_improving_declining_stable():
    assert trend([10, 20, 30, 40]) == "improving"
    assert trend([40, 30, 20, 10]) == "declining"
    assert trend([20, 20.4, 19.6, 20.2]) == "stable"


def test_next_test_date_cycle():
    last = dt.date(2026, 1, 1)
    timing = next_test_date(last, today=dt.date(2026, 1, 2))
    assert timing["ready"] is False
    assert timing["days_remaining"] == 73
    timing2 = next_test_date(last, today=dt.date(2026, 4, 1))
    assert timing2["ready"] is True


def test_parameter_series():
    rows = [{"parameter": "ph", "value": 7.4}, {"parameter": "volume", "value": 2.0}]
    assert parameter_series(rows, "ph") == [7.4]
