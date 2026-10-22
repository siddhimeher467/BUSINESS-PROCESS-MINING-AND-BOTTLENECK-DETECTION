# Business Process Mining & Bottleneck Detection System

A ready-to-run academic portfolio project inspired by a Process Mining Virtual Internship. It analyzes a CSV event log and provides process KPIs, common process paths, activity wait-time estimates, potential bottleneck flags, cycle-time charts, and downloadable summaries.

## Requirements
- Python 3.10 or newer
- Internet connection for installing packages (first run only)

## Run locally
1. Extract the ZIP file.
2. Open a terminal in the `process_mining_project` folder.
3. Create and activate a virtual environment (recommended):
   - Windows: `py -m venv .venv` then `.venv\\Scripts\\activate`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Start the app: `streamlit run app.py`
6. Open the local address shown in the terminal (usually `http://localhost:8501`).

## Input CSV format
Required columns:
- `Case ID`: unique order/process instance ID
- `Activity`: event name
- `Timestamp`: event date and time

Optional columns: `Resource`, `Department`, `Status`.
Use one row per event. A case normally has multiple rows. Example data is in `data/sample_event_log.csv`.

## Main features
- KPI cards: cases, events, average cycle time, completed cases, potential delayed cases
- Activity frequency chart
- Average time until the next activity (used as a basic bottleneck indicator)
- Most common process paths
- Case cycle-time distribution
- Event-log table and CSV downloads
- Upload support for a user's own event log

## Important methodology note
The time from an activity to the next recorded event is a **time-between-events estimate**, not necessarily the actual working time spent on that activity. It may include queues, nights, weekends, and hand-offs. The app flags potential bottlenecks for investigation; it does not prove the root cause. Use anonymized, authorized data only.

## Suggested project report sections
1. Abstract
2. Introduction to Process Mining
3. Problem Statement
4. Objectives
5. System Architecture
6. Dataset and Event Log Structure
7. Methodology
8. Implementation and Screenshots
9. Results and Discussion
10. Limitations
11. Future Scope
12. Conclusion

Dataset is synthetic and for demonstration only; it does not represent any real organization.
