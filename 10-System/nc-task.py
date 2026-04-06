#!/usr/bin/env python3
"""
nc-task.py — Create tasks in Nextcloud Tasks via CalDAV.

Pure Python, no external dependencies. Creates VTODO entries on Nextcloud
CalDAV task lists shared with or owned by the Servetus user.

Usage:
  python3 10-System/nc-task.py "Watch Stanley Kubrick: A Life in Pictures with Alison"
  python3 10-System/nc-task.py "Fix deploy script" --list binary-ranch
  python3 10-System/nc-task.py "Call dentist" --list personal --due 2026-04-10
  python3 10-System/nc-task.py --lists                    # show available lists

Config: config/nextcloud.env (NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_APP_PASSWORD)
"""

import argparse
import base64
import json
import sys
import urllib.request
import urllib.error
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, date
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent / "config" / "nextcloud.env"


def load_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def make_headers(user: str, password: str) -> dict:
    cred = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {cred}"}


def list_calendars(env: dict) -> list[dict]:
    """Fetch CalDAV calendars that support VTODO."""
    user = env["NEXTCLOUD_USER"]
    url = f"{env['NEXTCLOUD_URL']}/remote.php/dav/calendars/{user}/"
    body = """<?xml version="1.0"?>
<d:propfind xmlns:d="DAV:" xmlns:cs="http://calendarserver.org/ns/"
            xmlns:c="urn:ietf:params:xml:ns:caldav">
  <d:prop>
    <d:displayname/>
    <c:supported-calendar-component-set/>
  </d:prop>
</d:propfind>"""
    req = urllib.request.Request(
        url, data=body.encode(), method="PROPFIND",
        headers={
            **make_headers(user, env["NEXTCLOUD_APP_PASSWORD"]),
            "Content-Type": "application/xml",
            "Depth": "1",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = r.read()

    ns = {
        "d": "DAV:",
        "cs": "http://calendarserver.org/ns/",
        "c": "urn:ietf:params:xml:ns:caldav",
    }
    root = ET.fromstring(data)
    results = []
    for resp in root.findall(".//d:response", ns):
        href = resp.find("d:href", ns)
        name = resp.find(".//d:displayname", ns)
        comps = [c.get("name", "") for c in resp.findall(".//c:comp", ns)]
        if href is not None and name is not None and "VTODO" in comps:
            # Extract short ID from href
            parts = href.text.rstrip("/").split("/")
            short_id = parts[-1] if parts else href.text
            results.append({
                "href": href.text,
                "name": name.text,
                "short_id": short_id,
            })
    return results


def find_list(calendars: list[dict], query: str) -> dict | None:
    """Find a task list by name or short_id (case-insensitive partial match)."""
    q = query.lower()
    for cal in calendars:
        if q in cal["name"].lower() or q in cal["short_id"].lower():
            return cal
    return None


def create_task(env: dict, calendar_href: str, summary: str,
                description: str = "", due_date: str = "",
                priority: int = 0) -> str:
    """Create a VTODO on the given calendar. Returns the UID."""
    user = env["NEXTCLOUD_USER"]
    password = env["NEXTCLOUD_APP_PASSWORD"]
    base = env["NEXTCLOUD_URL"]

    uid = str(uuid.uuid4())
    now = datetime.now(tz=__import__('datetime').timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    vtodo_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Servetus//Tasks//EN",
        "BEGIN:VTODO",
        f"UID:{uid}",
        f"DTSTAMP:{now}",
        f"CREATED:{now}",
        f"LAST-MODIFIED:{now}",
        f"SUMMARY:{summary}",
        "STATUS:NEEDS-ACTION",
    ]
    if description:
        # Escape newlines for iCalendar
        desc_escaped = description.replace("\n", "\\n")
        vtodo_lines.append(f"DESCRIPTION:{desc_escaped}")
    if due_date:
        # Accept YYYY-MM-DD, convert to iCal DATE format
        try:
            dt = date.fromisoformat(due_date)
            vtodo_lines.append(f"DUE;VALUE=DATE:{dt.strftime('%Y%m%d')}")
        except ValueError:
            pass
    if priority:
        vtodo_lines.append(f"PRIORITY:{priority}")

    vtodo_lines.extend([
        "END:VTODO",
        "END:VCALENDAR",
    ])
    ical_body = "\r\n".join(vtodo_lines)

    url = f"{base}{calendar_href}{uid}.ics"
    req = urllib.request.Request(
        url, data=ical_body.encode(), method="PUT",
        headers={
            **make_headers(user, password),
            "Content-Type": "text/calendar",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        status = r.status

    if status not in (200, 201):
        raise RuntimeError(f"Failed to create task: HTTP {status}")

    return uid


def main():
    parser = argparse.ArgumentParser(description="Create Nextcloud Tasks")
    parser.add_argument("summary", nargs="?", help="Task title")
    parser.add_argument("--list", "-l", default="", help="Task list name (partial match)")
    parser.add_argument("--due", "-d", default="", help="Due date (YYYY-MM-DD)")
    parser.add_argument("--description", default="", help="Task description")
    parser.add_argument("--priority", type=int, default=0, help="Priority (1=high, 5=medium, 9=low)")
    parser.add_argument("--lists", action="store_true", help="List available task lists")
    args = parser.parse_args()

    env = load_env()
    calendars = list_calendars(env)

    if args.lists:
        print("Available task lists:")
        for cal in calendars:
            print(f"  {cal['name']}  ({cal['short_id']})")
        return

    if not args.summary:
        parser.error("Task summary is required (or use --lists)")

    # Default to first available list if none specified
    if args.list:
        cal = find_list(calendars, args.list)
        if not cal:
            print(f"No task list matching '{args.list}'. Available:")
            for c in calendars:
                print(f"  {c['name']}  ({c['short_id']})")
            sys.exit(1)
    else:
        # Default list preference: personal tasks on a shared list
        cal = find_list(calendars, "binary-ranch") or calendars[0] if calendars else None
        if not cal:
            print("No VTODO-capable task lists found.")
            sys.exit(1)

    uid = create_task(env, cal["href"], args.summary,
                      description=args.description,
                      due_date=args.due,
                      priority=args.priority)
    print(f"Created task on [{cal['name']}]: {args.summary}")
    if args.due:
        print(f"  Due: {args.due}")
    print(f"  UID: {uid}")


if __name__ == "__main__":
    main()
