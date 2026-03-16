from fastapi import FastAPI, HTTPException
import requests

# Create the FastAPI application object used by Uvicorn.
app = FastAPI()


@app.get("/")
def read_root():
    # Basic health-check style route so you can confirm the server is running.
    return {"Hello": "World"}

# Local source of truth for section start/end times.
# Key = section id, Value = (start_time, end_time)
# TODO: Update recitation hours for the current semester.
RECITATION_HOURS = {
    "a": ("09:00", "09:50"),
    "b": ("10:00", "10:50"),
    "c": ("11:00", "11:50"),
    "d": ("12:00", "12:50"),
}
# Upstream service that provides TA names for each section.
MICROSERVICE_LINK = "http://17313-teachers.s3d.cmu.edu:8080/section_info/"


@app.get("/section_info/{section_id}")
def get_section_info(section_id: str):
    # Normalize to lowercase so /A and /a are treated the same.
    section_id = section_id.lower()

    # Reject unknown sections early.
    if section_id not in RECITATION_HOURS:
        raise HTTPException(status_code=404, detail="Invalid section id")

    # Fetch local schedule data.
    start_time, end_time = RECITATION_HOURS[section_id]

    try:
        # Fetch TA data from the external microservice.
        response = requests.get(MICROSERVICE_LINK + section_id, timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:
        # Convert upstream/network failures into a clear API error for clients.
        raise HTTPException(
            status_code=502,
            detail="Section info service unavailable",
        ) from exc

    # Expected shape from microservice includes a `ta` list.
    data = response.json()

    # Return combined data from both sources in the required format.
    return {
        "section": section_id,
        "start_time": start_time,
        "end_time": end_time,
        "ta": data["ta"],
    }
