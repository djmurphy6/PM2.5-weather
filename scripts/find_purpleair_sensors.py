"""

Usage:
    python scripts/find_purpleair_sensors.py

Requires PURPLEAIR_API_KEY in a .env file at the project root.
Saves results to data/raw/purpleair/eugene_sensors.csv
"""

import os
import sys
import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────

# Bounding box around Eugene / Springfield, OR
BBOX = {
    "nwlat":  44.20,
    "nwlng": -123.30,
    "selat":  43.90,
    "selng": -122.85,
}

# Only include sensors created before this date (must have 2020 data)
CUTOFF_DATE = datetime(2022, 8, 1, tzinfo=timezone.utc)
CUTOFF_TS   = int(CUTOFF_DATE.timestamp())

PURPLEAIR_API = "https://api.purpleair.com/v1/sensors"

FIELDS = [
    "sensor_index",
    "name",
    "latitude",
    "longitude",
    "location_type",   # 0 = outside, 1 = inside
    "date_created",    # Unix timestamp
    "last_seen",       # Unix timestamp
    "channel_state",
    "channel_flags",
    "confidence",
]

OUTPUT_PATH = Path("data/raw/purpleair/eugene_sensors.csv")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    load_dotenv()
    api_key = os.getenv("PURPLEAIR_API_KEY")

    if not api_key:
        print("ERROR: PURPLEAIR_API_KEY not found.")
        print("Create a .env file in the project root with:")
        print("    PURPLEAIR_API_KEY=your_key_here")
        print("Get a free key at https://develop.purpleair.com")
        sys.exit(1)

    print(f"Querying PurpleAir API for sensors in Eugene bounding box...")
    print(f"  NW corner: {BBOX['nwlat']}°N, {BBOX['nwlng']}°W")
    print(f"  SE corner: {BBOX['selat']}°N, {BBOX['selng']}°W")
    print(f"  Cutoff:    sensors created before {CUTOFF_DATE.date()}\n")

    params = {
        "fields":        ",".join(FIELDS),
        "location_type": 0,          # outdoor only
        **BBOX,
    }
    headers = {"X-API-Key": api_key}

    response = requests.get(PURPLEAIR_API, params=params, headers=headers, timeout=30)

    if response.status_code == 403:
        print("ERROR: API key rejected (403). Check your key.")
        sys.exit(1)
    elif response.status_code != 200:
        print(f"ERROR: API returned {response.status_code}")
        print(response.text)
        sys.exit(1)

    data = response.json()
    field_names = data["fields"]
    rows        = data["data"]

    df = pd.DataFrame(rows, columns=field_names)
    total_found = len(df)
    print(f"Found {total_found} outdoor sensors in bounding box.")

    # Filter: must have been created before the cutoff
    df = df[df["date_created"] <= CUTOFF_TS].copy()
    print(f"Sensors with data before {CUTOFF_DATE.date()}: {len(df)}")

    # Convert Unix timestamps to readable dates
    df["date_created_dt"] = pd.to_datetime(df["date_created"], unit="s", utc=True)
    df["last_seen_dt"]    = pd.to_datetime(df["last_seen"],    unit="s", utc=True)

    # Flag sensors that are still reporting (seen in last 7 days)
    now = datetime.now(tz=timezone.utc)
    df["still_active"] = (now - df["last_seen_dt"]).dt.days <= 7

    # Sort by date created (oldest first — most likely to have full 2020 coverage)
    df = df.sort_values("date_created_dt")

    # Save
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved sensor list to: {OUTPUT_PATH}")

    # Summary
    print("\n── Summary ───────────────────────────────────────────────")
    print(f"  Total outdoor sensors in bounding box:  {total_found}")
    print(f"  Sensors with pre-Aug-2022 data:         {len(df)}")
    print(f"  Still actively reporting:               {df['still_active'].sum()}")
    print(f"  Sensor IDs: {sorted(df['sensor_index'].tolist())}")
    print("\n── Sensor List ───────────────────────────────────────────")
    display_cols = ["sensor_index", "name", "date_created_dt", "last_seen_dt", "still_active", "latitude", "longitude"]
    print(df[display_cols].to_string(index=False))
    print("\nNext step: run scripts/download_purpleair_history.py with these sensor IDs.")


if __name__ == "__main__":
    main()
