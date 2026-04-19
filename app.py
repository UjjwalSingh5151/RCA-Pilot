import streamlit as st
import pandas as pd
from analyser import scan_variance, check_hypotheses, HYPOTHESIS_LIBRARY

st.set_page_config(
    page_title="Growth RCA Co-pilot",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .stButton > button {
        padding: 10px 24px;
        font-size: 15px;
        border-radius: 8px;
    }
    [data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px;
    }
    .stCheckbox label {
        white-space: normal;
        line-height: 1.5;
    }
    [data-testid="stDataFrame"] {
        overflow-x: auto;
    }
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 0.75rem;
        }
        .stButton > button {
            width: 100%;
        }
        h1 { font-size: 1.4rem; }
        h2 { font-size: 1.2rem; }
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Growth RCA Co-pilot")
st.caption("Forecast vs actuals analysis — upload your Excel file to begin")

uploaded_file = st.file_uploader(
    "Upload Excel file",
    type=["xlsx"],
    help="Needs 3 sheets: actuals, forecast, seasonality"
)

if uploaded_file is None:
    st.info("Upload your Excel file above to get started")
    with st.expander("What format does the file need?"):
        st.markdown("""
**Sheet 1 — actuals**
One row per day. Columns: `date`, `creators_new`, `creators_retained`,
`creators_resurrected`, `creators_churned`, `post_per_creator`,
`click_per_post`, `order_per_click`

**Sheet 2 — forecast**
Same columns as actuals

**Sheet 3 — seasonality**
Columns: `date`, `metric`, `expected_uplift_pct`, `driver`, `notes`
        """)
    st.stop()

with open("uploaded_data.xlsx", "wb") as f:
    f.write(uploaded_file.getbuffer())

st.success("File uploaded successfully")

st.divider()

threshold = st.slider(
    "Flag variance threshold (%)",
    min_value=1,
    max_value=30,
    value=5,
    step=1,
    help="Metrics off from forecast by more than this % will be flagged"
)

st.header("Part 1 — Variance scan")

with st.spinner("Scanning metrics..."):
    all_results, flagged, seasonality = scan_variance("uploaded_data.xlsx", threshold)

total = len(all_results)
flagged_count = len(flagged)
ok_count = total - flagged_count

col1, col2, col3 = st.columns(3)
col1.metric("Total metrics", total)
col2.metric("Flagged", flagged_count)
col3.metric("On track", ok_count)

st.divider()

for r in all_results:
    variance = r["variance_pct"]
    wow = r["wow_pct"]
    is_flagged = r["flagged"]

    if is_flagged:
        border_color = "#e63946" if variance < 0 else "#ffa94d"
        icon = "🔴" if variance < 0 else "🟠"
    else:
        border_color = "#51cf66"
        icon = "🟢"

    st.markdown(f"""
<div style="
    border-left: 4px solid {border_color};
    padding: 10px 16px;
    margin-bottom: 10px;
    background: #fafafa;
    border-radius: 0 8px 8px 0;
">
    <div style="font-weight:600;font-size:15px;margin-bottom:4px">
        {icon} {r['metric'].replace('_', ' ').title()}
    </div>
    <div style="font-size:13px;color:#555;display:flex;gap:24px;flex-wrap:wrap">
        <span>Actual avg: <b>{r['actual_avg']}</b></span>
        <span>Forecast avg: <b>{r['forecast_avg']}</b></span>
        <span>Variance: <b style="color:{border_color}">{variance:+.1f}%</b></span>
        <span>WoW: <b>{wow:+.1f}%</b></span>
    </div>
</div>
""", unsafe_allow_html=True)

if not flagged:
    st.success(f"No metrics flagged at {threshold}% threshold")
    st.stop()

st.warning(f"{flagged_count} metric(s) flagged — select one below to investigate")

st.divider()
st.header("Part 2 — Hypothesis checker")

flagged_names = [r["metric"] for r in flagged]
selected_metric = st.selectbox(
    "Which flagged metric to investigate?",
    flagged_names,
    format_func=lambda x: x.replace("_", " ").title()
)

selected = next(r for r in flagged if r["metric"] == selected_metric)

st.markdown(f"""
<div style="
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 12px 0;
    font-size: 15px;
">
    <b>{selected_metric.replace('_', ' ').title()}</b> is
    <span style="color:#e63946;font-weight:600">{selected['variance_pct']:+.1f}%</span>
    vs forecast &nbsp;|&nbsp; WoW:
    <span style="font-weight:600">{selected['wow_pct']:+.1f}%</span>
</div>
""", unsafe_allow_html=True)

st.divider()
st.subheader("Select hypotheses to test")

left, right = st.columns([3, 2])

with left:
    st.caption("Standard library")
    selected_from_library = []
    for h in HYPOTHESIS_LIBRARY:
        if st.checkbox(h, key=f"lib_{h}"):
            selected_from_library.append(h)

with right:
    st.caption("Add your own")
    custom_hypotheses = []
    for i in range(1, 4):
        h = st.text_input(
            f"Custom hypothesis {i}",
            placeholder="Describe what you think happened...",
            key=f"custom_{i}"
        )
        if h.strip():
            custom_hypotheses.append(h.strip())

all_hypotheses = selected_from_library + custom_hypotheses

st.divider()

if not all_hypotheses:
    st.info("Select at least one hypothesis above to run the analysis")
    st.stop()

st.success(f"{len(all_hypotheses)} hypothesis(es) selected")

if st.button("Run analysis", type="primary"):
    with st.spinner("Checking hypotheses against your data — takes ~5 seconds..."):
        verdict = check_hypotheses(
            "uploaded_data.xlsx",
            selected_metric,
            all_hypotheses
        )
    st.subheader("Verdicts")
    st.markdown(verdict)
    st.divider()
    st.download_button(
        label="Download analysis as markdown",
        data=verdict,
        file_name=f"rca_{selected_metric}.md",
        mime="text/markdown"
    )