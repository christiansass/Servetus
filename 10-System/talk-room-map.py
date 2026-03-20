#!/usr/bin/env python3
"""
talk-room-map.py — Build and update config/talk-rooms.json from Nextcloud Talk API.

Fetches all Talk rooms, merges with any existing manual annotations (arc, role, notes),
and writes the full token → room map to config/talk-rooms.json.

Usage:
    python3 10-System/talk-room-map.py
    python3 10-System/talk-room-map.py --show   # print room list, don't write

config/nextcloud.env must contain:
    NEXTCLOUD_URL=https://your.server
    NEXTCLOUD_USER=your-username
    NEXTCLOUD_APP_PASSWORD=your-app-password
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent
ENV_FILE   = VAULT_ROOT / "config" / "nextcloud.env"
MAP_FILE   = VAULT_ROOT / "config" / "talk-rooms.json"

ROOM_TYPES = {1: "onetoone", 2: "group", 3: "public", 4: "changelog", 5: "notetoself", 6: "notetoself"}


def load_env(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def fetch_rooms(url, user, password):
    endpoint = f"{url.rstrip('/')}/ocs/v2.php/apps/spreed/api/v4/room?format=json"
    credentials = f"{user}:{password}"
    import base64
    b64 = base64.b64encode(credentials.encode()).decode()
    req = urllib.request.Request(
        endpoint,
        headers={
            "Authorization": f"Basic {b64}",
            "OCS-APIREQUEST": "true",
        }
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["ocs"]["data"]


def main():
    show_only = "--show" in sys.argv

    if not ENV_FILE.exists():
        print(f"[error] {ENV_FILE} not found — run Servetus onboarding first")
        sys.exit(1)

    env = load_env(ENV_FILE)
    url  = env.get("NEXTCLOUD_URL", "")
    user = env.get("NEXTCLOUD_USER", "")
    pw   = env.get("NEXTCLOUD_APP_PASSWORD", "")

    if not all([url, user, pw]):
        print("[error] NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_APP_PASSWORD must all be set in config/nextcloud.env")
        sys.exit(1)

    print(f"[talk-room-map] Connecting to {url} ...")
    try:
        rooms = fetch_rooms(url, user, pw)
    except urllib.error.HTTPError as e:
        print(f"[error] HTTP {e.code}: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"[error] {e}")
        sys.exit(1)

    print(f"[talk-room-map] {len(rooms)} rooms found")

    # Load existing map to preserve manual annotations (arc, role, notes)
    existing = {}
    if MAP_FILE.exists():
        with open(MAP_FILE) as f:
            existing = json.load(f)

    updated = {}
    for r in sorted(rooms, key=lambda x: x.get("lastActivity", 0), reverse=True):
        token = r["token"]
        prev  = existing.get(token, {})
        entry = {
            "name":         r.get("displayName", ""),
            "type":         ROOM_TYPES.get(r.get("type"), "unknown"),
            "last_activity": r.get("lastActivity", 0),
            # Preserve manual annotations
            "arc":          prev.get("arc", None),
            "participants": prev.get("participants", []),
            "role":         prev.get("role", None),
            "notes":        prev.get("notes", None),
        }
        # Strip nulls for cleanliness
        entry = {k: v for k, v in entry.items() if v is not None}
        updated[token] = entry

    if show_only:
        for token, r in updated.items():
            print(f"{token:20} {r['type']:12} {r['name']}")
        return

    with open(MAP_FILE, "w") as f:
        json.dump(updated, f, indent=2)

    print(f"[talk-room-map] Written to {MAP_FILE}")


if __name__ == "__main__":
    main()
