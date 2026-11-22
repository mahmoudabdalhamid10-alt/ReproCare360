from repro360.report import build_html
from repro360.store import Store


def test_report_is_self_contained_html(tmp_path):
    store = Store(tmp_path / "t.db")
    doc = build_html(store)
    assert doc.startswith("<!doctype html>")
    assert "<style>" in doc and "http" not in doc.split("<body>")[0]


def test_report_includes_lab_rows(tmp_path):
    store = Store(tmp_path / "t.db")
    store.add_lab("concentration", 10.0, "M/mL")
    doc = build_html(store)
    assert "Sperm concentration" in doc
    assert "low" in doc


def test_report_carries_disclaimer(tmp_path):
    store = Store(tmp_path / "t.db")
    assert "does not diagnose" in build_html(store)
