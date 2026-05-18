"""
Build the CSV that the PurpleAir Data Download Tool expects.

Reads the sensor list saved by find_purpleair_sensors.py and writes a
download_list CSV containing only sensors that existed before the target
event window.

Usage:
    # 2022 Cedar Creek Fire (default)
    python scripts/prepare_download_list.py

    # 2020 Holiday Farm Fire
    python scripts/prepare_download_list.py --year 2020
"""

import sys
import argparse
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

SENSOR_LIST = Path("data/raw/purpleair/eugene_sensors.csv")

# Per-year configuration: window_end is the last day to download (inclusive).
# Only sensors created before window_end are included.
YEAR_CONFIG = {
    2022: {
        "window_start":  "2022-08-01",
        "window_end":    "2022-09-30",
        "smoke_peak":    "2022-08-15",   # Cedar Creek onset
        "output":        Path("data/raw/purpleair/download_list.csv"),
        "download_dir":  "data/raw/purpleair/PurpleAir Download 2022/",
    },
    2020: {
        "window_start":  "2020-08-01",
        "window_end":    "2020-10-15",
        "smoke_peak":    "2020-09-07",   # Holiday Farm fire explosion
        "output":        Path("data/raw/purpleair/download_list_2020.csv"),
        "download_dir":  "data/raw/purpleair/PurpleAir Download 2020/",
    },
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2022, choices=list(YEAR_CONFIG))
    args = parser.parse_args()
    cfg = YEAR_CONFIG[args.year]

    if not SENSOR_LIST.exists():
        print(f"ERROR: {SENSOR_LIST} not found.")
        print("Run scripts/find_purpleair_sensors.py first.")
        sys.exit(1)

    sensors = pd.read_csv(SENSOR_LIST)
    sensors["date_created_dt"] = pd.to_datetime(sensors["date_created_dt"], utc=True)

    window_end_dt = datetime.fromisoformat(cfg["window_end"]).replace(tzinfo=timezone.utc)
    smoke_peak_dt = datetime.fromisoformat(cfg["smoke_peak"]).replace(tzinfo=timezone.utc)
    window_start_dt = datetime.fromisoformat(cfg["window_start"]).replace(tzinfo=timezone.utc)

    # Keep any sensor created before the end of the download window
    subset = sensors[sensors["date_created_dt"] < window_end_dt].copy()

    def coverage(created):
        if created < window_start_dt:
            return "full"
        elif created < smoke_peak_dt:
            return "partial_pre_peak"
        else:
            return "partial_post_onset"

    subset["coverage"] = subset["date_created_dt"].apply(coverage)

    out = subset[["sensor_index"]].copy()
    out["read_key"] = ""

    cfg["output"].parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(cfg["output"], index=False)

    print(f"\nYear {args.year} — window {cfg['window_start']} → {cfg['window_end']}")
    print(f"Saved {len(out)} sensors to: {cfg['output']}")
    print(f"\nCoverage breakdown:")
    print(subset["coverage"].value_counts().to_string())
    print(f"\nSensor IDs ({len(out)}): {sorted(out['sensor_index'].tolist())}")
    print(f"\nNext step:")
    print(f"  1. Open the PurpleAir Data Download Tool")
    print(f"  2. Load {cfg['output']} in the sensor input field")
    print(f"  3. Set date range: {cfg['window_start']} to {cfg['window_end']}")
    print(f"  4. Set average: 60 minutes")
    print(f"  5. Output directory: {cfg['download_dir']}")
    print(f"  6. Click Get Data")


if __name__ == "__main__":
    main()
