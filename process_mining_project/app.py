import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Process Mining Dashboard", page_icon="📊", layout="wide")
st.title("📊 Business Process Mining & Bottleneck Detection")
st.caption("Analyze event logs, discover process paths, and identify delays and rework.")

DEFAULT_FILE = Path(__file__).parent / "data" / "sample_event_log.csv"

@st.cache_data
def load_csv(file_or_path):
    return pd.read_csv(file_or_path)

def prepare_data(df):
    required = {"Case ID", "Activity", "Timestamp"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
    df = df.copy()
    df["Case ID"] = df["Case ID"].astype(str)
    df["Activity"] = df["Activity"].astype(str)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df = df.dropna(subset=["Case ID", "Activity", "Timestamp"])
    df = df.sort_values(["Case ID", "Timestamp"])
    return df

uploaded = st.sidebar.file_uploader("Upload event log (CSV)", type=["csv"])

if uploaded is not None:
    for encoding in ("utf-8-sig", "cp1252", "latin1"):
        try:
            uploaded.seek(0)
            raw = pd.read_csv(uploaded, encoding=encoding)
            st.write("Detected columns:", raw.columns.tolist())
            break
            break
        except UnicodeDecodeError:
            continue


else:
    raw = load_csv(DEFAULT_FILE)
    st.sidebar.info("Using the included sample dataset. Upload your own CSV to analyze another process.")

try:
    df = prepare_data(raw)
except Exception as exc:
    st.error(str(exc))
    st.markdown("Required columns: `Case ID`, `Activity`, `Timestamp`. Optional: `Resource`, `Department`, `Status`.")
    st.stop()

if df.empty:
    st.warning("No valid event rows were found in this file.")
    st.stop()

# Build activity-level duration by calculating the time to the next event within each case.
df["Next Timestamp"] = df.groupby("Case ID")["Timestamp"].shift(-1)
df["Duration Hours"] = (df["Next Timestamp"] - df["Timestamp"]).dt.total_seconds() / 3600

def case_summary(group):
    group = group.sort_values("Timestamp")
    return pd.Series({
        "Start": group["Timestamp"].min(),
        "End": group["Timestamp"].max(),
        "Cycle Time Hours": (group["Timestamp"].max() - group["Timestamp"].min()).total_seconds() / 3600,
        "Event Count": len(group),
        "Process Path": " → ".join(group["Activity"].tolist()),
        "Unique Activities": group["Activity"].nunique(),
    })

cases = df.groupby("Case ID").apply(case_summary).reset_index()
if "Status" in df.columns:
    status_map = df.sort_values("Timestamp").groupby("Case ID")["Status"].last().to_dict()
    cases["Status"] = cases["Case ID"].map(status_map)
else:
    cases["Status"] = "Unknown"

st.sidebar.subheader("Filters")
activities = sorted(df["Activity"].unique())
selected_activities = st.sidebar.multiselect("Activities to include in event table", activities, default=activities)
min_date, max_date = df["Timestamp"].min().date(), df["Timestamp"].max().date()
date_range = st.sidebar.date_input("Event date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
filtered = df[df["Activity"].isin(selected_activities)].copy()
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[(filtered["Timestamp"].dt.date >= start_date) & (filtered["Timestamp"].dt.date <= end_date)]

# Metrics use the full valid dataset so filtering the event table does not distort case KPIs.
total_cases = df["Case ID"].nunique()
avg_cycle = cases["Cycle Time Hours"].mean() if not cases.empty else 0
median_cycle = cases["Cycle Time Hours"].median() if not cases.empty else 0
completed = int((cases["Status"].astype(str).str.lower() == "completed").sum())
long_cases = int((cases["Cycle Time Hours"] > avg_cycle * 1.5).sum()) if avg_cycle > 0 else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Cases", f"{total_cases:,}")
c2.metric("Total Events", f"{len(df):,}")
c3.metric("Avg. Cycle Time", f"{avg_cycle:.1f} hrs")
c4.metric("Completed Cases", f"{completed:,}")
c5.metric("Potential Delayed Cases", f"{long_cases:,}")

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("Activity Frequency")
    freq = df["Activity"].value_counts().rename_axis("Activity").reset_index(name="Event Count")
    st.plotly_chart(px.bar(freq, x="Activity", y="Event Count", title="Number of events per activity"), use_container_width=True)
with right:
    st.subheader("Average Time Until Next Activity")
    durations = df.dropna(subset=["Duration Hours"])
    if not durations.empty:
        bottlenecks = durations.groupby("Activity", as_index=False)["Duration Hours"].mean().sort_values("Duration Hours", ascending=False)
        bottlenecks = bottlenecks.rename(columns={"Duration Hours": "Average Wait (hours)"})
        st.plotly_chart(px.bar(bottlenecks, x="Activity", y="Average Wait (hours)", title="Average time before the next event", color="Average Wait (hours)"), use_container_width=True)
    else:
        st.info("Each case needs at least two events to calculate activity durations.")

st.subheader("Most Common Process Paths")
path_counts = cases["Process Path"].value_counts().head(10).rename_axis("Process Path").reset_index(name="Cases")
st.dataframe(path_counts, use_container_width=True, hide_index=True)

st.subheader("Bottleneck Analysis")
if not durations.empty:
    bottlenecks = durations.groupby("Activity", as_index=False).agg(
        Events=("Activity", "size"),
        Average_Wait_Hours=("Duration Hours", "mean"),
        Median_Wait_Hours=("Duration Hours", "median"),
        Maximum_Wait_Hours=("Duration Hours", "max"),
    ).sort_values("Average_Wait_Hours", ascending=False)
    st.dataframe(bottlenecks.round(2), use_container_width=True, hide_index=True)
    top = bottlenecks.iloc[0]
    st.info(f"**Potential bottleneck:** `{top['Activity']}` has the highest average time before the next event ({top['Average_Wait_Hours']:.1f} hours). Check staffing, approvals, and hand-offs for this step. This is a data-based flag, not proof of the root cause.")

st.subheader("Case Cycle-Time Distribution")
st.plotly_chart(px.histogram(cases, x="Cycle Time Hours", nbins=20, title="How long cases take from first to last event"), use_container_width=True)

st.subheader("Event Log")
show_cols = [c for c in ["Case ID", "Activity", "Timestamp", "Duration Hours", "Resource", "Department", "Status"] if c in df.columns]
st.dataframe(filtered[show_cols].sort_values(["Case ID", "Timestamp"]), use_container_width=True, hide_index=True)

st.subheader("Download Analysis")
col1, col2 = st.columns(2)
with col1:
    st.download_button("Download cleaned event log", df.drop(columns=["Next Timestamp"], errors="ignore").to_csv(index=False).encode("utf-8"), "cleaned_event_log.csv", "text/csv")
with col2:
    st.download_button("Download case summary", cases.to_csv(index=False).encode("utf-8"), "case_summary.csv", "text/csv")

with st.expander("How to prepare your own CSV"):
    st.markdown("""Your CSV must include these columns:
- `Case ID`: unique transaction/order/process identifier
- `Activity`: event or step name
- `Timestamp`: date and time of the event (for example `2026-07-01 09:30:00`)

Optional columns: `Resource`, `Department`, `Status`. Use one row per event and multiple rows per case. Sort order is handled automatically.""")

st.caption("Academic portfolio project. Use authorized, anonymized business data only. The included dataset is synthetic and does not represent a real company.")
