#!/usr/bin/env python3
"""
Block a date range as holiday/unavailable in availabilities.json.

Usage:
    python scripts/add_holiday.py 2026-05-20 2026-05-25
    python scripts/add_holiday.py 2026-12-24 2026-01-02
"""

import json
import os
import sys
from datetime import date, timedelta

AVAIL_PATH = os.path.join(os.path.dirname(__file__), "..", "availabilities.json")


def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/add_holiday.py START_DATE END_DATE")
        print("  Dates in YYYY-MM-DD format. END_DATE is inclusive.")
        print("  Example: python scripts/add_holiday.py 2026-05-20 2026-05-25")
        sys.exit(1)

    try:
        start = date.fromisoformat(sys.argv[1])
        end = date.fromisoformat(sys.argv[2])
    except ValueError:
        print("Error: dates must be in YYYY-MM-DD format")
        sys.exit(1)

    if end < start:
        print("Error: end date must be on or after start date")
        sys.exit(1)

    path = os.path.normpath(AVAIL_PATH)
    with open(path) as f:
        data = json.load(f)

    existing = {(s["date"], s["start"], s["end"]) for s in data["blockedSlots"]}
    added = 0
    current = start
    while current <= end:
        slot = {"date": current.isoformat(), "start": "00:00", "end": "23:59"}
        key = (slot["date"], slot["start"], slot["end"])
        if key not in existing:
            data["blockedSlots"].append(slot)
            added += 1
        current += timedelta(days=1)

    data["blockedSlots"].sort(key=lambda x: (x["date"], x["start"]))

    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    days = (end - start).days + 1
    print(f"Blocked {days} days ({start} to {end}), {added} new slots added.")
    print(f"Updated {path}")


if __name__ == "__main__":
    main()
