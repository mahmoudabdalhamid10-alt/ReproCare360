"""Self-contained HTML report (print to PDF from the browser).

Pulls together journal, lab results vs WHO limits, triage history and
habits into one static HTML document with inline CSS. No external assets,
so the file works offline and prints cleanly.
"""

from __future__ import annotations

import datetime as dt
import html
from typing import Dict, List, Optional

from . import DISCLAIMER
from .store import Store
from .tracking import SPERM_CYCLE_DAYS, trend
from .who_reference import PARAMETERS


def _esc(x: object) -> str:
    return html.escape(str(x))


def _lab_section(labs: List[Dict[str, object]]) -> str:
    if not labs:
        return "<p class='muted'>No lab results recorded yet.</p>"
    latest: Dict[str, Dict[str, object]] = {}
    for row in labs:
        latest.setdefault(str(row["parameter"]), row)
    rows = []
    for key, param in PARAMETERS.items():
        if key not in latest:
            continue
        row = latest[key]
        value = float(row["value"])
        status = "ok" if value >= param.lower_limit else "low"
        cls = "ok" if status == "ok" else "low"
        rows.append(
            f"<tr><td>{_esc(param.label)}</td><td>{value:g} {_esc(param.unit)}</td>"
            f"<td>&ge; {param.lower_limit:g} {_esc(param.unit)}</td>"
            f"<td class='{cls}'>{status}</td></tr>"
        )
    trend_cells = []
    for key in latest:
        series = [float(r["value"]) for r in labs if r["parameter"] == key]
        if len(series) >= 3:
            trend_cells.append(f"<li>{_esc(PARAMETERS[key].label)}: {trend(series)}</li>")
    trend_html = f"<ul>{''.join(trend_cells)}</ul>" if trend_cells else ""
    return (
        "<table><thead><tr><th>Parameter</th><th>Latest</th>"
        "<th>WHO 2021 lower limit</th><th>Status</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>{trend_html}"
    )


def _entries_section(entries: List[Dict[str, object]]) -> str:
    if not entries:
        return "<p class='muted'>No journal entries yet.</p>"
    items = []
    for e in entries[:30]:
        when = dt.datetime.fromtimestamp(float(e["created_at"])).strftime("%Y-%m-%d %H:%M")
        items.append(f"<li><b>{_esc(e['category'])}</b> <span class='muted'>{when}</span><br>{_esc(e['note'])}</li>")
    return f"<ul>{''.join(items)}</ul>"


def _triage_section(history: List[Dict[str, object]]) -> str:
    if not history:
        return "<p class='muted'>No triage checks recorded.</p>"
    items = []
    for h in history[:10]:
        when = dt.datetime.fromtimestamp(float(h["created_at"])).strftime("%Y-%m-%d %H:%M")
        flags = ", ".join(_esc(f.get("label", f.get("key", ""))) for f in h.get("flags", [])) or "no flags"
        items.append(f"<li><b class='{_esc(h['level'])}'>{_esc(h['level'])}</b> <span class='muted'>{when}</span> - {flags}</li>")
    return f"<ul>{''.join(items)}</ul>"


def build_html(store: Store, title: str = "ReproCare 360 report") -> str:
    labs = store.labs()
    entries = store.entries()
    history = store.triage_history()
    today = dt.date.today().isoformat()
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{_esc(title)}</title>
<style>
body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 760px; margin: 2rem auto; padding: 0 1rem; color: #17202a; }}
h1 {{ border-bottom: 3px solid #2e86c1; padding-bottom: .3rem; }}
h2 {{ color: #1a5276; margin-top: 2rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #d5dbdb; padding: .4rem .6rem; text-align: left; }}
th {{ background: #eaf2f8; }}
.ok {{ color: #1e8449; font-weight: 600; }}
.low, .urgent, .emergency {{ color: #c0392b; font-weight: 600; }}
.routine {{ color: #b9770e; font-weight: 600; }}
.muted {{ color: #7f8c8d; }}
footer {{ margin-top: 3rem; font-size: .85rem; color: #7f8c8d; border-top: 1px solid #d5dbdb; padding-top: .6rem; }}
</style></head><body>
<h1>{_esc(title)}</h1>
<p class="muted">Generated {today} &middot; data stays on this device</p>
<h2>Semen analysis (vs WHO 2021 lower reference limits)</h2>
{_lab_section(labs)}
<p class="muted">A repeat test is meaningful about {SPERM_CYCLE_DAYS} days after the previous one (one sperm cycle).</p>
<h2>Journal</h2>
{_entries_section(entries)}
<h2>Safety checks</h2>
{_triage_section(history)}
<footer>{_esc(DISCLAIMER)}</footer>
</body></html>"""


def save_report(store: Store, path: str) -> str:
    html_doc = build_html(store)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html_doc)
    return path
