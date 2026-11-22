"""ReproCare 360 REST API.

17 endpoints, pydantic validation, OpenAPI docs at /docs.
Run with: uvicorn repro360.api:app --reload --port 8000  (or ``make api``)
"""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from . import DISCLAIMER
from .evidence import KnowledgeBase
from .report import build_html
from .report_parser import parse_report
from .safety import checklist_items, evaluate_checklist
from .store import Store
from .tracking import next_test_date, parameter_series, trend
from .triage_text import analyze_text
from .pathway import next_steps
from .who_reference import assess, reference_table
import datetime as dt

app = FastAPI(title="ReproCare 360", version="0.1.0", description=DISCLAIMER)

_kb: Optional[KnowledgeBase] = None
_store: Optional[Store] = None


def get_kb() -> KnowledgeBase:
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
    return _kb


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store


# -- request models -------------------------------------------------------

class SemenAssessIn(BaseModel):
    measurements: Dict[str, float]


class ParseIn(BaseModel):
    text: str


class ChecklistIn(BaseModel):
    answers: Dict[str, bool]


class TriageTextIn(BaseModel):
    text: str = Field(min_length=3)


class PathwayIn(BaseModel):
    trying_months: Optional[float] = None
    has_semen_analysis: bool = False
    concentration: Optional[float] = None
    smokes: Optional[bool] = None
    heavy_alcohol: Optional[bool] = None
    sitting_hours: Optional[float] = None


class SearchIn(BaseModel):
    query: str = Field(min_length=2)
    k: int = Field(default=3, ge=1, le=10)


class JournalEntryIn(BaseModel):
    category: str = Field(min_length=1, max_length=60)
    note: str = Field(min_length=1, max_length=4000)


class LabIn(BaseModel):
    parameter: str
    value: float
    unit: str = ""


# -- endpoints ------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "disclaimer": DISCLAIMER}  # 1


@app.get("/api/reference")
def reference():
    return {"who_edition": "2021 (6th)", "parameters": reference_table()}  # 2


@app.post("/api/semen/assess")
def semen_assess(body: SemenAssessIn):
    results = assess(body.measurements)
    return {"results": [r.as_dict() for r in results],
            "low": [r.key for r in results if r.status == "low"]}  # 3


@app.post("/api/semen/parse")
def semen_parse(body: ParseIn):
    parsed = parse_report(body.text)
    results = assess(parsed.measurements)
    return {
        "measurements": parsed.measurements,
        "unparsed_lines": parsed.unparsed_lines,
        "results": [r.as_dict() for r in results],
    }  # 4


@app.get("/api/triage/checklist")
def triage_checklist_items():
    return {"items": checklist_items()}  # 5


@app.post("/api/triage/checklist")
def triage_checklist(body: ChecklistIn):
    result = evaluate_checklist(body.answers)
    get_store().add_triage(str(result["level"]), list(result["flags"]))
    return result  # 6


@app.post("/api/triage/text")
def triage_text(body: TriageTextIn):
    result = analyze_text(body.text)
    get_store().add_triage(str(result["level"]), list(result["flags"]))
    return result  # 7


@app.post("/api/pathway/next-steps")
def pathway(body: PathwayIn):
    return next_steps(**body.model_dump())  # 8


@app.post("/api/evidence/search")
def evidence_search(body: SearchIn):
    return get_kb().search(body.query, k=body.k)  # 9


@app.get("/api/evidence/entries")
def evidence_entries():
    kb = get_kb()
    return {"entries": [{"id": e["id"], "title": e["title"], "source": e["source"]} for e in kb.entries]}  # 10


@app.get("/api/evidence/entries/{entry_id}")
def evidence_entry(entry_id: str):
    entry = get_kb().get(entry_id)
    if not entry:
        raise HTTPException(404, "entry not found")
    return entry  # 11


@app.post("/api/journal/entries", status_code=201)
def journal_add(body: JournalEntryIn):
    return get_store().add_entry(body.category, body.note)  # 12


@app.get("/api/journal/entries")
def journal_list(limit: int = 100):
    return {"entries": get_store().entries(limit)}  # 13


@app.post("/api/journal/labs", status_code=201)
def labs_add(body: LabIn):
    return get_store().add_lab(body.parameter, body.value, body.unit)  # 14


@app.get("/api/journal/labs")
def labs_list(parameter: Optional[str] = None, limit: int = 200):
    return {"labs": get_store().labs(parameter, limit)}  # 15


@app.get("/api/journal/summary")
def journal_summary():
    store = get_store()
    labs = store.labs()
    summary: Dict[str, object] = {"parameters": {}}
    params: Dict[str, object] = {}
    for key in {str(r["parameter"]) for r in labs}:
        series = parameter_series(labs, key)
        params[key] = {"n": len(series), "trend": trend(series)}
    summary["parameters"] = params
    dated = [r for r in labs if r.get("created_at")]
    if dated:
        last = dt.date.fromtimestamp(max(float(r["created_at"]) for r in dated))
        summary["repeat_timing"] = next_test_date(last)
    summary["n_entries"] = len(store.entries())
    return summary  # 16


@app.post("/api/report", response_class=HTMLResponse)
def report():
    return build_html(get_store())  # 17
