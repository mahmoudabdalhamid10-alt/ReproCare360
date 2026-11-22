"""Retrieval evaluation harness.

Run with ``python -m repro360.evidence_eval`` (or ``make eval``). Scores the
ranker on the dev and held-out query sets and writes
``reports/evidence_eval.json`` and ``reports/evidence_eval.md``.

The dev queries were written while tuning; the held-out queries were
written afterwards and never tuned on. With n=20 held-out, the uncertainty
on R@1 is about +/-0.18.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .data import DATA_DIR
from .evidence import KnowledgeBase

ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT / "reports"

METHODS = [
    ("TF-IDF only", "tfidf", False),
    ("BM25 only", "bm25", False),
    ("Hybrid fusion", "hybrid", False),
    ("Hybrid + query expansion", "hybrid", True),
]


def _rank_of(kb: KnowledgeBase, query: str, relevant_id: str, method: str, expand: bool) -> int | None:
    res = kb.search(query, k=len(kb.entries), method=method, expand=expand, min_score=0.0)
    for i, entry in enumerate(res["results"], 1):
        if entry["id"] == relevant_id:
            return i
    return None


def evaluate_split(kb: KnowledgeBase, rows: List[Dict[str, str]], method: str, expand: bool) -> Dict[str, object]:
    r1 = r3 = 0
    rr_total = 0.0
    misses = []
    for row in rows:
        rank = _rank_of(kb, row["query"], row["relevant_id"], method, expand)
        if rank == 1:
            r1 += 1
        if rank is not None and rank <= 3:
            r3 += 1
        if rank:
            rr_total += 1.0 / rank
        else:
            misses.append(row["query"])
    n = len(rows)
    return {
        "n": n,
        "recall_at_1": round(r1 / n, 3),
        "recall_at_3": round(r3 / n, 3),
        "mrr": round(rr_total / n, 3),
        "misses": misses,
    }


def run() -> Dict[str, object]:
    kb = KnowledgeBase()
    with open(DATA_DIR / "eval_queries.json", encoding="utf-8") as fh:
        queries = json.load(fh)

    table: List[Dict[str, object]] = []
    for label, method, expand in METHODS:
        dev = evaluate_split(kb, queries["dev"], method, expand)
        held = evaluate_split(kb, queries["held_out"], method, expand)
        table.append({"configuration": label, "dev": dev, "held_out": held})

    rejected = 0
    details = []
    for q in queries["unrelated"]:
        res = kb.search(q, k=3, method="hybrid", expand=True)
        details.append({"query": q, "rejected": bool(res["rejected"])})
        rejected += int(bool(res["rejected"]))
    rejection = {"total": len(queries["unrelated"]), "rejected": rejected, "details": details}

    REPORTS_DIR.mkdir(exist_ok=True)
    out = {"table": table, "unrelated_rejection": rejection}
    with open(REPORTS_DIR / "evidence_eval.json", "w") as fh:
        json.dump(out, fh, indent=2)

    lines = [
        "# Evidence AI retrieval evaluation",
        "",
        "Dev queries were written while tuning; held-out queries were written afterwards and never tuned on.",
        "",
        "| Configuration | Dev R@1 | Held-out R@1 | Held-out R@3 | Held-out MRR |",
        "|---|---|---|---|---|",
    ]
    for row in table:
        lines.append(
            f"| {row['configuration']} | {row['dev']['recall_at_1']:.2f} | "
            f"{row['held_out']['recall_at_1']:.2f} | {row['held_out']['recall_at_3']:.2f} | "
            f"{row['held_out']['mrr']:.2f} |"
        )
    lines += [
        "",
        f"Held-out n={table[0]['held_out']['n']}, so uncertainty is wide (about +/-0.18 on R@1).",
        "",
        "## Held-out misses (hybrid + expansion)",
        "",
    ]
    best = table[-1]
    misses = best["held_out"]["misses"] or ["(none)"]
    lines += [f"- {m}" for m in misses]
    lines += [
        "",
        "## Unrelated-query rejection",
        "",
        f"{rejection['rejected']} of {rejection['total']} unrelated queries were correctly rejected.",
    ]
    lines += [f"- {'REJECTED' if d['rejected'] else 'ANSWERED'}: {d['query']}" for d in rejection["details"]]
    lines.append("")
    with open(REPORTS_DIR / "evidence_eval.md", "w") as fh:
        fh.write("\n".join(lines))

    print("\n".join(lines))
    return out


if __name__ == "__main__":
    run()
