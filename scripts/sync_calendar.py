#!/usr/bin/env python3
"""
Fetches events from Google Calendar and Apple iCloud Calendar,
then writes blocked time slots to availabilities.json.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

import urllib.request

import caldav
import vobject
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- Configuration ---
TIMEZONE = "America/Toronto"
DAYS_AHEAD = 30
MEETING_DURATION = 30
CONTACT_EMAIL = "alireza.toghiani@icloud.com"
WEEKLY_AVAILABILITY = {
    "monday":    [{"start": "10:00", "end": "17:00"}],
    "tuesday":   [{"start": "10:00", "end": "17:00"}],
    "wednesday": [{"start": "10:00", "end": "17:00"}],
    "thursday":  [{"start": "10:00", "end": "17:00"}],
    "friday":    [{"start": "10:00", "end": "17:00"}],
    "saturday":  [],
    "sunday":    [],
}

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "availabilities.json")


def get_date_range():
    """Return (start, end) as ISO strings for the next DAYS_AHEAD days."""
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from backports.zoneinfo import ZoneInfo

    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=DAYS_AHEAD)
    return start, end


def fetch_google_events(start, end):
    """Fetch events from Google Calendar using OAuth2 refresh token."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("Google Calendar secrets not set, skipping.")
        return []

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
    )

    service = build("calendar", "v3", credentials=creds)
    events_result = service.events().list(
        calendarId="primary",
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = []
    for ev in events_result.get("items", []):
        s = ev.get("start", {})
        e = ev.get("end", {})
        # Skip all-day events (they use "date" not "dateTime")
        if "dateTime" in s and "dateTime" in e:
            events.append({
                "start": s["dateTime"],
                "end": e["dateTime"],
            })
        elif "date" in s and "date" in e:
            # All-day event — block entire day
            events.append({
                "start_date": s["date"],
                "end_date": e["date"],
                "all_day": True,
            })
    return events


def fetch_apple_events(start, end):
    """Fetch events from Apple iCloud Calendar via CalDAV."""
    apple_id = os.environ.get("APPLE_ID")
    apple_app_password = os.environ.get("APPLE_APP_PASSWORD")

    if not all([apple_id, apple_app_password]):
        print("Apple Calendar secrets not set, skipping.")
        return []

    client = caldav.DAVClient(
        url="https://caldav.icloud.com",
        username=apple_id,
        password=apple_app_password,
    )

    events = []
    try:
        principal = client.principal()
        calendars = principal.calendars()

        for cal in calendars:
            try:
                results = cal.search(
                    start=start,
                    end=end,
                    event=True,
                    expand=True,
                )
            except Exception as e:
                print(f"  Warning: could not search calendar '{cal.name}': {e}")
                continue

            for event in results:
                try:
                    vevent = event.vobject_instance.vevent
                    dtstart = vevent.dtstart.value
                    dtend = vevent.dtend.value if hasattr(vevent, "dtend") else None

                    # All-day events have date, not datetime
                    if not hasattr(dtstart, "hour"):
                        if dtend and not hasattr(dtend, "hour"):
                            events.append({
                                "start_date": dtstart.isoformat(),
                                "end_date": dtend.isoformat(),
                                "all_day": True,
                            })
                    else:
                        if dtend:
                            events.append({
                                "start": dtstart.isoformat(),
                                "end": dtend.isoformat(),
                            })
                except Exception as e:
                    print(f"  Warning: could not parse event: {e}")
                    continue

    except Exception as e:
        print(f"Apple Calendar error: {e}")

    return events


def fetch_ics_events(start, end):
    """Fetch events from ICS URLs (e.g. work calendar shared link)."""
    ics_urls = os.environ.get("ICS_CALENDAR_URLS", "")
    if not ics_urls.strip():
        print("ICS calendar URLs not set, skipping.")
        return []

    events = []
    for url in ics_urls.split(","):
        url = url.strip()
        if not url:
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CalendarSync/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read().decode("utf-8")

            cal = vobject.readOne(data)
            for component in cal.components():
                if component.name != "VEVENT":
                    continue
                try:
                    dtstart = component.dtstart.value
                    dtend = component.dtend.value if hasattr(component, "dtend") else None

                    if not hasattr(dtstart, "hour"):
                        # All-day event
                        if dtend and not hasattr(dtend, "hour"):
                            ev_start = dtstart if hasattr(dtstart, "isoformat") else dtstart
                            ev_end = dtend if hasattr(dtend, "isoformat") else dtend
                            if ev_end > start.date() and ev_start < end.date():
                                events.append({
                                    "start_date": ev_start.isoformat(),
                                    "end_date": ev_end.isoformat(),
                                    "all_day": True,
                                })
                    else:
                        if dtend:
                            # Make timezone-aware for comparison
                            if hasattr(dtstart, "tzinfo") and dtstart.tzinfo:
                                if dtend > start and dtstart < end:
                                    events.append({
                                        "start": dtstart.isoformat(),
                                        "end": dtend.isoformat(),
                                    })
                            else:
                                events.append({
                                    "start": dtstart.isoformat(),
                                    "end": dtend.isoformat(),
                                })
                except Exception as e:
                    print(f"  Warning: could not parse ICS event: {e}")
                    continue

            print(f"  ICS ({url[:50]}...): {len(events)} events so far")
        except Exception as e:
            print(f"  ICS fetch error for {url[:50]}...: {e}")

    return events


def events_to_blocked_slots(events):
    """Convert raw events into blocked slot entries for the JSON."""
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from backports.zoneinfo import ZoneInfo

    tz = ZoneInfo(TIMEZONE)
    slots = []

    for ev in events:
        if ev.get("all_day"):
            # Block full availability window for each day
            d_start = datetime.fromisoformat(ev["start_date"]).date() if "start_date" in ev else None
            d_end = datetime.fromisoformat(ev["end_date"]).date() if "end_date" in ev else None
            if d_start and d_end:
                current = d_start
                while current < d_end:
                    slots.append({
                        "date": current.isoformat(),
                        "start": "00:00",
                        "end": "23:59",
                    })
                    current += timedelta(days=1)
        else:
            start_dt = datetime.fromisoformat(ev["start"])
            end_dt = datetime.fromisoformat(ev["end"])

            # Convert to local timezone
            if start_dt.tzinfo is not None:
                start_dt = start_dt.astimezone(tz)
                end_dt = end_dt.astimezone(tz)

            # If event spans multiple days, split into per-day slots
            current_date = start_dt.date()
            final_date = end_dt.date()

            while current_date <= final_date:
                day_start = start_dt.strftime("%H:%M") if current_date == start_dt.date() else "00:00"
                day_end = end_dt.strftime("%H:%M") if current_date == end_dt.date() else "23:59"

                if day_start != day_end:
                    slots.append({
                        "date": current_date.isoformat(),
                        "start": day_start,
                        "end": day_end,
                    })
                current_date += timedelta(days=1)

    # Deduplicate and sort
    seen = set()
    unique = []
    for s in slots:
        key = (s["date"], s["start"], s["end"])
        if key not in seen:
            seen.add(key)
            unique.append(s)
    unique.sort(key=lambda x: (x["date"], x["start"]))
    return unique


def main():
    start, end = get_date_range()
    print(f"Fetching events from {start.date()} to {end.date()}...")

    all_events = []

    google_events = fetch_google_events(start, end)
    print(f"  Google Calendar: {len(google_events)} events")
    all_events.extend(google_events)

    apple_events = fetch_apple_events(start, end)
    print(f"  Apple Calendar: {len(apple_events)} events")
    all_events.extend(apple_events)

    ics_events = fetch_ics_events(start, end)
    print(f"  ICS Calendars: {len(ics_events)} events")
    all_events.extend(ics_events)

    blocked_slots = events_to_blocked_slots(all_events)
    print(f"  Total blocked slots: {len(blocked_slots)}")

    output = {
        "timezone": TIMEZONE,
        "meetingDurationMinutes": MEETING_DURATION,
        "weeklyAvailability": WEEKLY_AVAILABILITY,
        "blockedSlots": blocked_slots,
        "maxBookingDaysAhead": DAYS_AHEAD,
        "contactEmail": CONTACT_EMAIL,
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
    }

    output_path = os.path.normpath(OUTPUT_PATH)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
        f.write("\n")

    print(f"Written to {output_path}")


if __name__ == "__main__":
    main()
