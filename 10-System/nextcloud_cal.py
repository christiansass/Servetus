#!/usr/bin/env python3
"""
nextcloud_cal.py — CalDAV library for Servetus.

Pure Python, no LLM dependency. Importable by any Servetus component:
    from nextcloud_cal import list_calendars, get_today, create_event

Auth via nextcloud.env (same file talk-listener uses).

Usage:
    python3 10-System/nextcloud_cal.py              # quick connectivity test
    python3 10-System/nextcloud_cal.py --today       # print today's events
"""

import os
from datetime import datetime, timedelta, date
from pathlib import Path
from zoneinfo import ZoneInfo

import caldav
from icalendar import Calendar as iCal

# ── Config ───────────────────────────────────────────────────────────────────

VAULT_ROOT = Path(__file__).parent.parent
ENV_FILE   = VAULT_ROOT / "config" / "nextcloud.env"
TZ         = ZoneInfo("America/Chicago")


def _load_env():
    """Load env vars from nextcloud.env if present."""
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_load_env()


def _client():
    return caldav.DAVClient(
        url=f"{os.environ['NEXTCLOUD_URL']}/remote.php/dav",
        username=os.environ["NEXTCLOUD_USER"],
        password=os.environ["NEXTCLOUD_APP_PASSWORD"],
    )


# ── Helpers ──────────────────────────────────────────────────────────────────

def _format_event(vevent) -> dict:
    """Extract readable fields from a VEVENT component."""
    def _dt(val):
        if val is None:
            return None
        dt = val.dt if hasattr(val, "dt") else val
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TZ)
            return dt.astimezone(TZ).strftime("%Y-%m-%d %H:%M")
        if isinstance(dt, date):
            return dt.strftime("%Y-%m-%d")
        return str(dt)

    return {
        "summary":     str(vevent.get("SUMMARY", "")),
        "start":       _dt(vevent.get("DTSTART")),
        "end":         _dt(vevent.get("DTEND")),
        "location":    str(vevent.get("LOCATION", "")),
        "description": str(vevent.get("DESCRIPTION", "")),
        "uid":         str(vevent.get("UID", "")),
        "status":      str(vevent.get("STATUS", "")),
    }


def _parse_events(cal_data) -> list[dict]:
    """Parse iCalendar data into a list of event dicts."""
    cal = iCal.from_ical(cal_data)
    events = []
    for component in cal.walk():
        if component.name == "VEVENT":
            events.append(_format_event(component))
    return events


# ── Public API ───────────────────────────────────────────────────────────────

def list_calendars() -> list[dict]:
    """List all calendars available to the Nextcloud user."""
    client = _client()
    principal = client.principal()
    calendars = principal.calendars()
    result = []
    for cal in calendars:
        try:
            name = cal.get_display_name()
        except Exception:
            name = str(cal.url).rstrip("/").split("/")[-1]
        result.append({
            "name": name,
            "url": str(cal.url),
            "id": str(cal.url).rstrip("/").split("/")[-1],
        })
    return result


def get_events(
    calendar_id: str = "personal",
    start_date: str = "",
    end_date: str = "",
    days: int = 7,
) -> list[dict]:
    """
    Get events from a calendar within a date range.

    Args:
        calendar_id: Calendar slug (e.g. 'personal', 'personal_shared_by_csass',
                     'seven-talents_shared_by_csass'). Default: personal.
        start_date:  Start date as YYYY-MM-DD. Default: today.
        end_date:    End date as YYYY-MM-DD. Default: start_date + days.
        days:        Number of days from start_date if end_date not given. Default: 7.
    """
    client = _client()
    caldav_url = f"{os.environ['NEXTCLOUD_URL']}/remote.php/dav"
    cal_url = f"{caldav_url}/calendars/{os.environ['NEXTCLOUD_USER']}/{calendar_id}/"
    cal = caldav.Calendar(client=client, url=cal_url)

    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=TZ)
    else:
        start = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)

    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, tzinfo=TZ
        )
    else:
        end = start + timedelta(days=days)

    results = cal.search(start=start, end=end, event=True, expand=True)

    events = []
    for event in results:
        parsed = _parse_events(event.data)
        events.extend(parsed)

    events.sort(key=lambda e: e.get("start") or "")
    return events


def get_today(calendar_id: str = "") -> list[dict]:
    """
    Get today's events across all calendars, or from a specific one.

    Args:
        calendar_id: Optional calendar slug. If empty, searches all calendars.
    """
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    if calendar_id:
        return get_events(calendar_id=calendar_id, start_date=today, days=1)

    all_events = []
    for cal in list_calendars():
        cal_id = cal["id"]
        try:
            events = get_events(calendar_id=cal_id, start_date=today, days=1)
            for e in events:
                e["calendar"] = cal["name"]
            all_events.extend(events)
        except Exception:
            continue

    all_events.sort(key=lambda e: e.get("start") or "")
    return all_events


def create_event(
    summary: str,
    start: str,
    end: str = "",
    calendar_id: str = "personal",
    location: str = "",
    description: str = "",
    all_day: bool = False,
) -> dict:
    """
    Create a new calendar event.

    Args:
        summary:     Event title.
        start:       Start time as 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD' for all-day.
        end:         End time (same format). Default: start + 1 hour, or next day for all-day.
        calendar_id: Calendar slug. Default: personal.
        location:    Optional location string.
        description: Optional description.
        all_day:     If True, creates an all-day event.
    """
    client = _client()
    caldav_url = f"{os.environ['NEXTCLOUD_URL']}/remote.php/dav"
    cal_url = f"{caldav_url}/calendars/{os.environ['NEXTCLOUD_USER']}/{calendar_id}/"
    cal = caldav.Calendar(client=client, url=cal_url)

    if all_day or len(start) == 10:
        dtstart = datetime.strptime(start[:10], "%Y-%m-%d").date()
        if end:
            dtend = datetime.strptime(end[:10], "%Y-%m-%d").date()
        else:
            dtend = dtstart + timedelta(days=1)
        dt_fmt = ";VALUE=DATE"
    else:
        dtstart = datetime.strptime(start, "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        if end:
            dtend = datetime.strptime(end, "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        else:
            dtend = dtstart + timedelta(hours=1)
        dt_fmt = ""

    vcal = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Servetus Nextcloud Cal//EN
BEGIN:VEVENT
SUMMARY:{summary}
DTSTART{dt_fmt}:{dtstart.strftime('%Y%m%dT%H%M%S') if isinstance(dtstart, datetime) else dtstart.strftime('%Y%m%d')}
DTEND{dt_fmt}:{dtend.strftime('%Y%m%dT%H%M%S') if isinstance(dtend, datetime) else dtend.strftime('%Y%m%d')}
{f'LOCATION:{location}' if location else ''}
{f'DESCRIPTION:{description}' if description else ''}
END:VEVENT
END:VCALENDAR"""

    vcal = "\n".join(line for line in vcal.splitlines() if line.strip())
    event = cal.save_event(vcal)
    return {"status": "created", "uid": str(event.url)}


def search_events(query: str, calendar_id: str = "", days_ahead: int = 30) -> list[dict]:
    """
    Search for events by text across calendars.

    Args:
        query:       Text to search for in event summaries and descriptions.
        calendar_id: Optional calendar slug. If empty, searches all calendars.
        days_ahead:  How many days ahead to search. Default: 30.
    """
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    query_lower = query.lower()

    if calendar_id:
        cal_ids = [calendar_id]
    else:
        cal_ids = [c["id"] for c in list_calendars()]

    matches = []
    for cid in cal_ids:
        try:
            events = get_events(calendar_id=cid, start_date=today, days=days_ahead)
            for e in events:
                text = f"{e.get('summary', '')} {e.get('description', '')} {e.get('location', '')}".lower()
                if query_lower in text:
                    e["calendar_id"] = cid
                    matches.append(e)
        except Exception:
            continue

    matches.sort(key=lambda e: e.get("start") or "")
    return matches


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if "--today" in sys.argv:
        events = get_today()
        if events:
            for e in events:
                cal_name = e.get("calendar", "")
                print(f"  {e['start']} | {e['summary']}" + (f" [{cal_name}]" if cal_name else ""))
        else:
            print("  (no events today)")
        sys.exit(0)

    print("Testing CalDAV connection...")
    cals = list_calendars()
    print(f"Found {len(cals)} calendars:")
    for c in cals:
        print(f"  - {c['name']} ({c['id']})")
    print("\nToday's events:")
    events = get_today()
    if events:
        for e in events:
            cal_name = e.get("calendar", "")
            print(f"  {e['start']} | {e['summary']}" + (f" [{cal_name}]" if cal_name else ""))
    else:
        print("  (none)")
    print("\nCalDAV connection OK.")
