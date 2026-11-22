"""ReproCare 360 Streamlit dashboard (8 pages).

Run from the repo root:  streamlit run app/streamlit_app.py   (or ``make app``)
Talks to the core library directly, so it works without the REST API.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repro360 import DISCLAIMER  # noqa: E402
from repro360.evidence import KnowledgeBase  # noqa: E402
from repro360.pathway import next_steps  # noqa: E402
from repro360.report import build_html  # noqa: E402
from repro360.report_parser import parse_report  # noqa: E402
from repro360.safety import checklist_items, evaluate_checklist  # noqa: E402
from repro360.store import Store  # noqa: E402
from repro360.tracking import next_test_date, parameter_series, trend  # noqa: E402
from repro360.triage_text import analyze_text  # noqa: E402
from repro360.who_reference import PARAMETERS, assess, reference_table  # noqa: E402

st.set_page_config(page_title="ReproCare 360", page_icon="🩺", layout="wide")

PAGES = [
    "Home",
    "Semen Lab",
    "My Journal",
    "Safety Center",
    "Care Pathway",
    "Evidence AI",
    "Lifestyle model (experimental)",
    "Report",
]

page = st.sidebar.radio("Page", PAGES)
st.sidebar.caption(DISCLAIMER)


def get_store() -> Store:
    if "store" not in st.session_state:
        st.session_state.store = Store()
    return st.session_state.store


def get_kb() -> KnowledgeBase:
    if "kb" not in st.session_state:
        st.session_state.kb = KnowledgeBase()
    return st.session_state.kb


_LEVEL_EMOJI = {"ok": "✅", "routine": "🟡", "urgent": "🟠", "emergency": "🔴"}


def _show_triage(result: dict) -> None:
    level = str(result["level"])
    st.markdown(f"### {_LEVEL_EMOJI.get(level, '')} {level.upper()}")
    for flag in result["flags"]:
        st.markdown(f"- **{flag.get('label', flag.get('key'))}** ({flag.get('level')}): {flag.get('advice')}")
    st.caption(str(result.get("note", "")))


# -- pages ----------------------------------------------------------------

if page == "Home":
    st.title("ReproCare 360")
    st.subheader("Private, evidence-based male reproductive health awareness")
    st.warning(DISCLAIMER)
    st.markdown(
        """
        - **Semen Lab** - compare your analysis against WHO 2021 lower reference limits
        - **My Journal** - anonymous local journal; data never leaves this device
        - **Safety Center** - red-flag checklist and free-text triage (conservative by design)
        - **Care Pathway** - ordered next steps, each linked to sources
        - **Evidence AI** - search a curated knowledge base; returns passages, not generated text
        - **Report** - one self-contained HTML summary you can print to PDF
        """
    )
    st.info("Every learned component is evaluated and the numbers, including the weak ones, are in the README.")

elif page == "Semen Lab":
    st.title("Semen Lab")
    tab_form, tab_paste, tab_ref = st.tabs(["Enter values", "Paste a lab report", "WHO reference"])
    with tab_form:
        with st.form("semen_form"):
            cols = st.columns(2)
            values = {}
            for i, (key, p) in enumerate(PARAMETERS.items()):
                with cols[i % 2]:
                    raw = st.text_input(f"{p.label} ({p.unit or 'pH'})", key=f"m_{key}")
                    if raw.strip():
                        try:
                            values[key] = float(raw.replace(",", "."))
                        except ValueError:
                            st.error(f"{p.label}: not a number")
            if st.form_submit_button("Assess") and values:
                for r in assess(values):
                    (st.success if r.status == "ok" else st.error)(
                        f"{r.label}: {r.value:g} {r.unit} (limit ≥ {r.lower_limit:g}) - {r.status}"
                    )
                store = get_store()
                for k, v in values.items():
                    store.add_lab(k, v, PARAMETERS[k].unit)
                st.caption("Saved to the local journal.")
    with tab_paste:
        text = st.text_area("Paste the report text (one finding per line)")
        if st.button("Parse") and text.strip():
            parsed = parse_report(text)
            if parsed.measurements:
                st.write("Recognized:", parsed.measurements)
                for r in assess(parsed.measurements):
                    (st.success if r.status == "ok" else st.error)(
                        f"{r.label}: {r.value:g} {r.unit} - {r.status}"
                    )
            if parsed.unparsed_lines:
                st.caption("Could not recognize these lines:")
                st.write(parsed.unparsed_lines)
    with tab_ref:
        st.table(reference_table())

elif page == "My Journal":
    st.title("My Journal")
    store = get_store()
    with st.form("entry_form"):
        category = st.selectbox("Category", ["note", "symptom", "habit", "test", "medication"])
        note = st.text_area("Note")
        if st.form_submit_button("Add entry") and note.strip():
            store.add_entry(category, note.strip())
            st.success("Saved locally.")
    st.subheader("Repeat-test timing")
    labs = store.labs()
    if labs:
        last = dt.date.fromtimestamp(max(float(r["created_at"]) for r in labs))
        timing = next_test_date(last)
        if timing["ready"]:
            st.success(f"Last test {timing['last_test']}: a repeat test is now meaningful.")
        else:
            st.info(
                f"Last test {timing['last_test']}: a repeat becomes meaningful around "
                f"{timing['earliest_meaningful']} ({timing['days_remaining']} days, one 74-day sperm cycle)."
            )
        st.subheader("Trends")
        for key in {str(r["parameter"]) for r in labs}:
            series = parameter_series(labs, key)
            label = PARAMETERS.get(key)
            name = label.label if label else key
            st.write(f"**{name}** ({len(series)} results): {trend(series)}")
            st.line_chart(series)
    else:
        st.caption("No lab results yet - add them in the Semen Lab page.")
    st.subheader("Recent entries")
    for e in store.entries(20):
        when = dt.datetime.fromtimestamp(float(e["created_at"])).strftime("%Y-%m-%d %H:%M")
        st.markdown(f"**{e['category']}** · `{when}`  \n{e['note']}")

elif page == "Safety Center":
    st.title("Safety Center")
    st.caption("This tool can only raise urgency, never rule anything out.")
    tab_check, tab_text = st.tabs(["Red-flag checklist", "Describe in your own words"])
    with tab_check:
        with st.form("checklist_form"):
            answers = {}
            for item in checklist_items():
                answers[item["key"]] = st.checkbox(item["question"])
            if st.form_submit_button("Check"):
                result = evaluate_checklist(answers)
                get_store().add_triage(str(result["level"]), list(result["flags"]))
                _show_triage(result)
    with tab_text:
        text = st.text_area("What are you feeling?")
        if st.button("Triage") and text.strip():
            result = analyze_text(text)
            get_store().add_triage(str(result["level"]), list(result["flags"]))
            _show_triage(result)

elif page == "Care Pathway":
    st.title("Care Pathway")
    with st.form("pathway_form"):
        trying = st.number_input("Months trying to conceive", min_value=0, value=0, step=1)
        has_analysis = st.checkbox("I already have a semen analysis")
        concentration = None
        if has_analysis:
            raw = st.text_input("Sperm concentration (M/mL), if known")
            if raw.strip():
                try:
                    concentration = float(raw.replace(",", "."))
                except ValueError:
                    st.error("Concentration: not a number")
        smokes = st.checkbox("I smoke")
        heavy_alcohol = st.checkbox("I drink heavily")
        sitting = st.number_input("Hours sitting per day", min_value=0, max_value=24, value=8)
        if st.form_submit_button("Build my next steps"):
            result = next_steps(
                trying_months=float(trying) or None,
                has_semen_analysis=has_analysis,
                concentration=concentration,
                smokes=smokes or None,
                heavy_alcohol=heavy_alcohol or None,
                sitting_hours=float(sitting),
            )
            kb = get_kb()
            for s in result["steps"]:
                with st.expander(f"{s['order']}. {s['title']}", expanded=s["order"] <= 2):
                    st.write(s["why"])
                    for src in s["sources"]:
                        entry = kb.get(src)
                        if entry:
                            st.caption(f"{entry['title']} ({entry['source']})")
            st.caption(result["note"])

elif page == "Evidence AI":
    st.title("Evidence AI")
    st.caption("Returns curated source passages, never generated text. Weak matches are rejected.")
    query = st.text_input("Ask a question (plain language works, e.g. 'does weed reduce sperm count')")
    k = st.slider("Passages", 1, 5, 3)
    if st.button("Search") and query.strip():
        res = get_kb().search(query, k=k)
        if res["rejected"]:
            st.warning("No confident match in the knowledge base. Try rephrasing, or ask a clinician.")
        for entry in res["results"]:
            with st.expander(f"{entry['title']} · score {entry['score']}"):
                st.write(entry["text"])
                st.caption(f"Source family: {entry['source']} - verify against the original guideline.")

elif page == "Lifestyle model (experimental)":
    st.title("Lifestyle model")
    st.caption("Trained on the real UCI Fertility dataset (100 men, 12 altered).")
    try:
        from repro360.model import metrics, predict_proba
        m = metrics()
        with st.expander("Model metrics - read this first", expanded=False):
            st.json(m)
            st.warning(
                "The honest result: on this dataset the model does not predict better than chance, "
                "so treat any single prediction as a demo, not evidence."
            )
        st.subheader("Evidence-based habit guidance comes first")
        st.markdown(
            "- Do not smoke\n- Limit alcohol\n- Healthy weight and moderate exercise\n"
            "- Enough sleep\n- Keep the groin cool; break up long sitting\n"
            "- Review medications and any steroid use with a doctor"
        )
        with st.expander("Run the experimental model anyway"):
            age = st.slider("Age", 18, 50, 30)
            sitting = st.slider("Hours sitting per day", 0, 16, 8)
            smokes = st.selectbox("Smoking", ["never", "occasional", "daily"])
            alcohol = st.selectbox("Alcohol", ["rarely", "1-2/week", "3-5/week", "daily"])
            if st.button("Predict"):
                features = {
                    "season": 0.0, "age": (age - 18) / 18.0, "childish_diseases": 0,
                    "accident": 0, "surgical_intervention": 0, "high_fevers": 0,
                    "alcohol": {"rarely": 0.2, "1-2/week": 0.4, "3-5/week": 0.6, "daily": 1.0}[alcohol],
                    "smoking": {"never": -1, "occasional": 0, "daily": 1}[smokes],
                    "sitting_hours": sitting / 16.0,
                }
                p = predict_proba(features)
                st.write(f"Estimated probability of an *altered* result: **{p:.0%}**")
                st.caption("Experimental demo on 100 rows; not medical evidence.")
    except FileNotFoundError:
        st.info("Model not trained yet. Run `make train` once to build models/ from the UCI data.")

elif page == "Report":
    st.title("Report")
    st.caption("One self-contained HTML file - print it to PDF from your browser.")
    store = get_store()
    html_doc = build_html(store)
    st.download_button("Download report.html", html_doc, file_name="reprocare_report.html", mime="text/html")
    st.components.v1.html(html_doc, height=600, scrolling=True)
