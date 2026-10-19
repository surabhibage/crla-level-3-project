# CRLA Level 3 Project

Run locally with `uvicorn app:app --reload`.
On Render, build with `pip install -r requirements.txt` and start with
`uvicorn app:app --host 0.0.0.0 --port $PORT`.

Configure these variables in local `.env` or Render Environment settings:

- `GOOGLE_CREDENTIALS`: service account JSON.
- `GOOGLE_SHEET_ID`: spreadsheet ID shared by both tabs.
- `GOOGLE_OBSERVATIONS_SHEET_NAME`: exact observations tab name (for example `sheet1`).
- `GOOGLE_INTERVIEWEES_SHEET_NAME`: exact candidate tab name (for example `Interviewees`).

Tab names are case sensitive and must be different. See `.env.example`.
Enable the Google Sheets API and share the spreadsheet with the service account as an Editor.
Observations append to columns A–J of the explicitly selected observations tab;
place observation headers in row 1 and keep this table contiguous.

The interviewees tab must have `Interviewee First Name` and `Interviewee Last Name`
headers in row 1. Names are trimmed, combined, deduplicated, and sorted; empty
rows are skipped. Names refresh on page loads at most once per 60 seconds per
server process. Connection or header failures show a warning and retain the last
successfully loaded list in that process. An empty valid tab clears the list.
Restarting clears the cache. No CSV or sample-name fallback is used.
Remove any old Render `names.csv` secret file or `NAMES_CSV_PATH` setting if desired;
they are no longer used.

Run checks with `.venv/bin/python -m unittest discover -s tests`.
