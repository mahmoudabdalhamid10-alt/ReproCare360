# Architecture

ReproCare 360 is a small layered system. Everything runs locally; there are no
accounts and no external calls.

```
+-------------------+        +-------------------+
| Streamlit dashboard|        |   FastAPI API      |
| app/streamlit_app  |        |  src/repro360/api  |
+---------+---------+        +---------+---------+
          |                            |
          +-------------+--------------+
                        |
              src/repro360 core library
  +----------------------------------------------------+
  | who_reference | report_parser | tracking | safety  |
  | triage_text   | pathway       | evidence | model   |
  | store (SQLite journal)        | report (HTML)      |
  +----------------------------------------------------+
          |                |                 |
     data/ (KB +       models/           reports/
     eval queries,     (trained          (eval output)
     UCI fertility)     artifacts)
```

## Module responsibilities

| Module | Responsibility | Key dependency |
|---|---|---|
| `who_reference.py` | WHO 2021 lower reference limits for 8 semen parameters | none |
| `report_parser.py` | Pasted lab report text -> measurements | `who_reference` |
| `store.py` | SQLite journal (entries, labs, habits, triage history) | sqlite3 |
| `tracking.py` | Trends, 74-day repeat-test timing | none |
| `safety.py` | Red-flag checklist; can only raise urgency | none |
| `triage_text.py` | Free-text triage rules with negation handling | `safety` |
| `pathway.py` | Questionnaire -> ordered next steps with KB sources | none |
| `evidence.py` | Stemming + synonym expansion + TF-IDF/BM25 fusion over the KB | `data/knowledge_base.json` |
| `evidence_eval.py` | Dev/held-out evaluation, writes `reports/` | `evidence` |
| `data.py` | UCI Fertility loader (sitting-hours /16 assumption) | pandas |
| `model.py` | Calibrated classifier, honest CV metrics, joblib artifact | scikit-learn |
| `report.py` | Self-contained HTML report | `store`, `who_reference`, `tracking` |
| `api.py` | 17 REST endpoints over the library | FastAPI |

## Design rules

- **Conservative triage.** Both checklist and text triage can only raise
  urgency. Silence never means "all clear".
- **Retrieval, not generation.** Evidence AI returns curated passages with
  their source family; weak matches are rejected instead of answered.
- **Local-first data.** The journal is a single SQLite file
  (`REPRO360_DB` overrides the path). The Docker compose volume keeps it
  between container runs.
- **Honesty in numbers.** Measured eval results live in
  `reports/evidence_eval.md` and `models/metrics.json` and are quoted in the
  README, including the ones that look bad.

## Data flow example (Semen Lab)

1. User pastes a lab report in the dashboard or POSTs to `/api/semen/parse`.
2. `report_parser` extracts known parameters; unknown lines are returned for
   manual entry, never guessed.
3. `who_reference.assess` compares each value with the lower limit.
4. Results are stored via `store` so `tracking` can show trends and the
   74-day retest window.
