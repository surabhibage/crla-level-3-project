from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
from datetime import datetime
import pandas as pd
import os
import uuid
import json
import gspread

# ── Google Sheets Setup ───────────────────────────────────────────────
# SHEET_NAME = "Peer Connections Candidate Observations"

# def get_sheet():
#     try:
#         gc = gspread.service_account(filename="credentials.json")
#         return gc.open(SHEET_NAME).sheet1
#     except Exception as e:
#         print("Google Sheets connection error:", e)
#         return None
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

def get_sheet():
    try:
        credentials_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])

        credentials = Credentials.from_service_account_info(credentials_info, scopes=["https://www.googleapis.com/auth/spreadsheets"])

        gc = gspread.authorize(credentials)

        sheet = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"]).sheet1

        return sheet

    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        raise

# ── App Setup ───────────────────────────────────────────────
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Load candidate list from names.csv
def load_candidates():
    csv_path = "names.csv"
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            names = (df["First Name"].astype(str).str.strip() + " " + df["Last Name"].astype(str).str.strip()).tolist()
            return sorted(names)
        except Exception as e:
            print("Error loading CSV:", e)
    return ["Candidate 1", "Candidate 2", "Candidate 3"]

# Divide candidates evenly into 3 rotating room groups across 3 rounds
def get_round_room_assignments():
    candidates = load_candidates()
    n = len(candidates)
    # Split into 3 balanced groups
    s1 = (n + 2) // 3
    s2 = s1 + (n - s1 + 1) // 2

    g1 = candidates[0:s1]
    g2 = candidates[s1:s2]
    g3 = candidates[s2:]

    return {
        "Round 1": {
            "Tinker Toys": sorted(g1),
            "Mini Lessons": sorted(g2),
            "Scenarios": sorted(g3)
        },
        "Round 2": {
            "Tinker Toys": sorted(g3),
            "Mini Lessons": sorted(g1),
            "Scenarios": sorted(g2)
        },
        "Round 3": {
            "Tinker Toys": sorted(g2),
            "Mini Lessons": sorted(g3),
            "Scenarios": sorted(g1)
        }
    }

def format_score(val: float):
    return int(val) if val.is_integer() else val

# In-memory storage for draft observations
observations = []

def get_observations_by_round():
    rounds = ["Round 1", "Round 2", "Round 3"]
    return {
        r: [obs for obs in reversed(observations) if obs.get("round") == r]
        for r in rounds
    }

def count_pending():
    return sum(1 for obs in observations if not obs.get("submitted_to_sheets"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    assignments = get_round_room_assignments()
    observed_names = [obs["candidate"] for obs in observations]
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "assignments_json": json.dumps(assignments),
            "observations": observations,
            "observations_by_round": get_observations_by_round(),
            "observed_names": observed_names,
            "pending_count": count_pending(),
            "success_msg": None,
            "error_msg": None,
            "last_observer": "",
            "last_room": "Tinker Toys",
            "last_round": "Round 1"
        }
    )

@app.post("/submit", response_class=HTMLResponse)
async def handle_form(
    request: Request,
    edit_id: Optional[str] = Form(None),
    observer_name: str = Form(...),
    room: str = Form(...),
    round_num: str = Form(..., alias="round"),
    candidate: str = Form(...),
    teamwork: float = Form(...),
    initiative: float = Form(...),
    personal_rep: float = Form(...),
    work_with: Optional[str] = Form("Yes"),
    comments: Optional[str] = Form("")
):
    entry_data = {
        "observer_name": observer_name.strip(),
        "room": room,
        "round": round_num,
        "candidate": candidate,
        "teamwork": format_score(teamwork),
        "initiative": format_score(initiative),
        "personal_rep": format_score(personal_rep),
        "work_with": work_with,
        "comments": comments.strip() if comments else "",
        "submitted_to_sheets": False
    }

    if edit_id:
        # Update existing observation
        updated = False
        for obs in observations:
            if obs.get("id") == edit_id:
                obs.update(entry_data)
                obs["submitted_to_sheets"] = False
                updated = True
                break
        msg = f"Updated draft observation for {candidate}!" if updated else f"Draft for {candidate} saved!"
    else:
        # Create new observation with unique id
        entry_data["id"] = uuid.uuid4().hex[:8]
        observations.append(entry_data)
        msg = f"Draft observation for {candidate} ({round_num}, {room}) saved!"

    assignments = get_round_room_assignments()
    observed_names = [obs["candidate"] for obs in observations]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "assignments_json": json.dumps(assignments),
            "observations": observations,
            "observations_by_round": get_observations_by_round(),
            "observed_names": observed_names,
            "pending_count": count_pending(),
            "success_msg": msg,
            "error_msg": None,
            "last_observer": observer_name.strip(),
            "last_room": room,
            "last_round": round_num
        }
    )

@app.post("/delete/{obs_id}", response_class=HTMLResponse)
async def delete_observation(request: Request, obs_id: str):
    global observations
    deleted_candidate = ""
    for obs in observations:
        if obs.get("id") == obs_id:
            deleted_candidate = obs.get("candidate", "")
            break
    observations = [obs for obs in observations if obs.get("id") != obs_id]

    assignments = get_round_room_assignments()
    observed_names = [obs["candidate"] for obs in observations]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "assignments_json": json.dumps(assignments),
            "observations": observations,
            "observations_by_round": get_observations_by_round(),
            "observed_names": observed_names,
            "pending_count": count_pending(),
            "success_msg": f"Deleted observation for {deleted_candidate}.",
            "error_msg": None,
            "last_observer": "",
            "last_room": "Tinker Toys",
            "last_round": "Round 1"
        }
    )

@app.post("/final-submit", response_class=HTMLResponse)
async def final_submit(request: Request):
    pending = [obs for obs in observations if not obs.get("submitted_to_sheets")]

    if not pending:
        msg = None
        err = "No pending observations to submit to Google Sheets."
    else:
        sheet = get_sheet()
        if not sheet:
            msg = None
            err = "Could not connect to Google Sheets. Please check credentials.json."
        else:
            try:
                rows_to_insert = []
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for obs in pending:
                    rows_to_insert.append([
                        now_str,
                        obs["candidate"],
                        obs["round"],
                        obs["room"],
                        obs["observer_name"],
                        obs["teamwork"],
                        obs["initiative"],
                        obs["personal_rep"],
                        obs["work_with"],
                        obs["comments"]
                    ])

                sheet.append_rows(rows_to_insert)
                for obs in pending:
                    obs["submitted_to_sheets"] = True

                msg = f"🎉 Success! All {len(rows_to_insert)} observation(s) have been permanently submitted to Google Sheets!"
                err = None
            except Exception as e:
                print("Failed to push batch to Google Sheets:", e)
                msg = None
                err = f"Failed to submit to Google Sheets: {str(e)}"

    assignments = get_round_room_assignments()
    observed_names = [obs["candidate"] for obs in observations]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "assignments_json": json.dumps(assignments),
            "observations": observations,
            "observations_by_round": get_observations_by_round(),
            "observed_names": observed_names,
            "pending_count": count_pending(),
            "success_msg": msg,
            "error_msg": err,
            "last_observer": "",
            "last_room": "Tinker Toys",
            "last_round": "Round 1"
        }
    )
