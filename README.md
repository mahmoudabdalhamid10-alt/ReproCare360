# ReproCare 360

An open, privacy-first platform for male reproductive health awareness, built for the
Future Health Digital Innovation Challenge (Male Reproductive Health statement).

> Educational tool only. It does not diagnose or treat. Urgent symptoms need immediate medical care.

**What makes it different:** every learned component is evaluated and the numbers are shown as they
are, including the weak ones (see [Honest results](#honest-results)). Retrieval returns source
passages instead of generated text, the triage can only raise urgency, and all data stays in a local file.

## Modules

| Module | Code | What it does |
|---|---|---|
| Semen Lab | `who_reference.py`, `report_parser.py` | 8 parameters vs WHO 2021 lower reference limits; paste a lab report and it is parsed |
| My Journal | `store.py`, `tracking.py` | Anonymous local SQLite journal, trend over time, repeat-test timing (74-day sperm cycle) |
| Safety Center | `safety.py`, `triage_text.py` | Checklist plus free-text triage with negation handling; conservative by design |
| Care Pathway | `pathway.py` | Questionnaire to an ordered next-steps checklist, each step linked to knowledge-base sources |
| Evidence AI | `evidence.py`, `evidence_eval.py` | Stemming + synonym expansion + TF-IDF/BM25 fusion over 32 curated entries, with an eval harness |
| Lifestyle model | `model.py`, `data.py` | Calibrated classifier on the real UCI Fertility data, flagged as experimental |
| Reports | `report.py` | Self-contained HTML report (print to PDF) |
| REST API | `api.py` | 17 endpoints, pydantic validation, OpenAPI docs at `/docs` |
| Dashboard | `app/streamlit_app.py` | 8-page Streamlit UI |

Architecture diagram: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Model card: [docs/MODEL_CARD.md](docs/MODEL_CARD.md).
Submission outline: [docs/PITCH.md](docs/PITCH.md).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
make test            # or: PYTHONPATH=src python -m pytest -q      (51 tests)
make app             # dashboard  -> http://localhost:8501
make api             # REST API   -> http://localhost:8000/docs
make eval            # retrieval evaluation -> reports/evidence_eval.md
```

On Windows without `make`, set `PYTHONPATH=src` (PowerShell: `$env:PYTHONPATH="src"`) and run the commands inside the Makefile.

### API example

```bash
curl -X POST localhost:8000/api/triage/text -H 'content-type: application/json' \
     -d '{"text":"sudden severe pain in my left testicle"}'
# {"level":"emergency","flags":[{"key":"sudden_testicular_pain", ...}], ...}

curl -X POST localhost:8000/api/evidence/search -H 'content-type: application/json' \
     -d '{"query":"does weed reduce sperm count","k":2}'
```

## Honest results

**Evidence AI retrieval** (queries written by the developer; 69 dev queries used while tuning, 20 held-out
queries written afterwards and never tuned on):

| Configuration | Dev R@1 | Held-out R@1 | Held-out R@3 | Held-out MRR |
|---|---|---|---|---|
| TF-IDF only | 0.61 | 0.60 | 0.85 | 0.72 |
| BM25 only | 0.64 | 0.60 | 0.85 | 0.72 |
| Hybrid fusion | 0.62 | 0.55 | 0.85 | 0.69 |
| **Hybrid + query expansion** | **0.86** | **0.80** | 0.85 | 0.82 |

Held-out n=20, so uncertainty is wide (about ±0.18 on R@1). Fusion alone gave no measurable gain; the improvement
comes from expanding lay terms ("weed" to "cannabis"). 5 of 5 unrelated queries were correctly rejected.
Full table and misses: `reports/evidence_eval.md`.

**Lifestyle model** (real UCI Fertility data, 100 men, 12 "altered", 10x repeated 5-fold CV):
AUC 0.51 ± 0.22 and a Brier score no better than a constant prediction. The model **does not predict
better than chance**, so the dashboard hides its score behind an "experimental" expander and leads with
evidence-based habit guidance instead.

**Free-text triage** is rule-based and covered by 15 labelled regression sentences. It was written and tested by the
same developer, so it has not been validated on real patient language.

## Limitations (read before using or presenting)

- Knowledge-base entries are short summaries written for this project and labelled with the guideline family they
  reflect (WHO manual, EAU guidelines). **Verify each entry against the original source and add exact citations
  before submission.**
- Sitting-hours scale of the UCI file is not documented; `data.py` assumes a 16-hour maximum.
- The care pathway thresholds (hormone tests below about 10 million/mL, genetic tests below about 5 million/mL) are
  approximations of published guidance and must be confirmed by a clinician.
- The Dockerfile and compose file were written but **not built** in the authoring environment (no Docker daemon).
  The API and dashboard were run directly and tested.
- Not a medical device; no regulatory review.

## Project layout

```
src/repro360/   core library (modules above)
app/            Streamlit dashboard
data/           knowledge_base.json, eval_queries.json, fertility.csv (UCI)
models/         trained model + metrics.json
reports/        evidence_eval.{json,md}
tests/          51 tests (unit, API, report)
docs/           architecture, model card, pitch outline
```

## Docker (untested build)

```bash
docker compose up --build    # API :8000, dashboard :8501, shared volume for the journal DB
```
