import pytest
from fastapi.testclient import TestClient

from repro360.api import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_reference_table():
    res = client.get("/api/reference")
    assert len(res.json()["parameters"]) == 8


def test_semen_assess():
    res = client.post("/api/semen/assess", json={"measurements": {"concentration": 10.0, "volume": 2.0}})
    assert res.json()["low"] == ["concentration"]


def test_semen_parse():
    res = client.post("/api/semen/parse", json={"text": "Volume: 2.1 mL\npH: 7.0"})
    body = res.json()
    assert body["measurements"] == {"volume": 2.1, "ph": 7.0}
    assert any(r["status"] == "low" for r in body["results"])


def test_triage_text_endpoint_and_validation():
    ok = client.post("/api/triage/text", json={"text": "sudden severe pain in my left testicle"})
    assert ok.json()["level"] == "emergency"
    bad = client.post("/api/triage/text", json={"text": "x"})
    assert bad.status_code == 422


def test_checklist_endpoint(tmp_path, monkeypatch):
    res = client.post("/api/triage/checklist", json={"answers": {"painless_lump": True}})
    assert res.json()["level"] == "urgent"


def test_pathway_endpoint():
    res = client.post("/api/pathway/next-steps", json={"trying_months": 14, "has_semen_analysis": False})
    titles = [s["title"] for s in res.json()["steps"]]
    assert any("workup" in t for t in titles)


def test_evidence_search_and_rejection():
    hit = client.post("/api/evidence/search", json={"query": "does weed reduce sperm count", "k": 2})
    assert hit.json()["results"][0]["id"] == "kb_cannabis"
    miss = client.post("/api/evidence/search", json={"query": "best chocolate cake recipe"})
    assert miss.json()["rejected"] is True


def test_evidence_entry_404():
    assert client.get("/api/evidence/entries/nope").status_code == 404
    ok = client.get("/api/evidence/entries/kb_smoking")
    assert ok.status_code == 200


def test_journal_and_report(tmp_path, monkeypatch):
    from repro360.store import Store
    store = Store(tmp_path / "api.db")
    import repro360.api as api_mod
    monkeypatch.setattr(api_mod, "_store", store)

    assert client.post("/api/journal/entries", json={"category": "note", "note": "hi"}).status_code == 201
    assert client.post("/api/journal/labs", json={"parameter": "volume", "value": 2.0, "unit": "mL"}).status_code == 201
    summary = client.get("/api/journal/summary").json()
    assert summary["n_entries"] == 1
    res = client.post("/api/report")
    assert res.status_code == 200 and res.text.startswith("<!doctype html>")
