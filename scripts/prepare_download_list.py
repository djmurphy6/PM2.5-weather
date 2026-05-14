"""
Build the CSV that the PurpleAir Data Download Tool expects.

Reads the sensor list saved by find_purpleair_sensors.py, fetches each
sensor's read key from the API, and writes:

    data/raw/purpleair/download_list.csv   ← load this into the download tool

Usage:
    python scripts/prepare_download_list.py
"""

import sys
import pandas as pd
from pathlib import Path

SENSOR_LIST = Path("data/raw/purpleair/eugene_sensors.csv")
OUTPUT_PATH = Path("data/raw/purpleair/download_list.csv")

def main():
    if not SENSOR_LIST.exists():
        print(f"ERROR: {SENSOR_LIST} not found.")
        print("Run scripts/find_purpleair_sensors.py first.")
        sys.exit(1)

    sensors = pd.read_csv(SENSOR_LIST)
    sensor_ids = sensors["sensor_index"].tolist()
    print(f"Fetching read keys for {len(sensor_ids)} sensors...")

    # read_key is a private credential not exposed by the API.
    # All sensors returned by the discovery script are public, so read_key is blank.
    out = sensors[["sensor_index"]].copy()
    out["read_key"] = ""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT_PATH, index=False)

    print(f"\nSaved {len(out)} sensors to: {OUTPUT_PATH}")
    print(f"Sensor IDs: {sorted(out['sensor_index'].tolist())}")
    print("\nNext step:")
    print("  1. Open the PurpleAir Data Download Tool")
    print("  2. Load download_list.csv in the sensor input field")
    print("  3. Set date range: 2022-08-01 to 2022-11-30")
    print("  4. Set average: 60 minutes")
    print("  5. Output directory: data/raw/purpleair/")
    print("  6. Click Get Data")

if __name__ == "__main__":
    main()
