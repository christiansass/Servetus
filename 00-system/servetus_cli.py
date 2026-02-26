#!/usr/bin/env python3
"""
Servetus CLI

Usage:
    python servetus_cli.py log "optional text here"
If no text is passed, you'll be dropped into a prompt to type/paste,
finish with Ctrl-D (Linux/macOS) or Ctrl-Z + Enter (Windows).

This writes a dated daily-log markdown file into `02-daily-logs/`.
"""

import sys
import socket
import uuid
import platform
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR    = VAULT_ROOT / "02-daily-logs"


# ---------------------------------------------------------------------------
# Origin fingerprint
# ---------------------------------------------------------------------------

def get_os() -> str:
    """Returns a human-readable OS string. Reads /etc/os-release on Linux for distro name."""
    system = platform.system()
    if system == "Linux":
        try:
            for line in open("/etc/os-release"):
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
        except Exception:
            pass
        return f"Linux {platform.release()}"
    elif system == "Darwin":
        return f"macOS {platform.mac_ver()[0]}"
    elif system == "Windows":
        return f"Windows {platform.version()}"
    return system


def get_origin() -> dict:
    """
    Returns machine fingerprint: human name, MAC, outbound IP, OS.

    machine — from config/overrides.md machine_name, falls back to hostname
    mac     — primary network interface hardware address (stable across OS on dual-boot)
    ip      — outbound IP at session time (reveals network/location)
    os      — human-readable OS name (disambiguates dual-boot sessions)
    """
    # Machine name
    machine = socket.gethostname()
    overrides = VAULT_ROOT / "config" / "overrides.md"
    if overrides.exists():
        for line in overrides.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("machine_name:"):
                val = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                if val:
                    machine = val
                break

    # MAC address
    mac_int = uuid.getnode()
    mac = ":".join(["{:02x}".format((mac_int >> (8 * i)) & 0xff)
                    for i in reversed(range(6))])

    # Outbound IP — UDP connect trick (no data sent)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "unknown"

    return {"machine": machine, "mac": mac, "ip": ip, "os": get_os()}


# ---------------------------------------------------------------------------
# Log builder
# ---------------------------------------------------------------------------

def build_daily_log(content: str) -> str:
    today    = datetime.now()
    date_iso = today.strftime("%Y-%m-%d")
    pretty   = today.strftime("%B %d, %Y")
    origin   = get_origin()

    return f"""---
servitus:
  schema_version: 1
  record_type: daily_log
  pipeline_stage: inbox
  status: draft
  intent: capture

identity:
  title: "Daily Log — {pretty}"
  slug: "daily-log-{date_iso}"
  record_id: "SV-{today.strftime('%Y%m%d-%H%M%S')}-CST-LOG"

time:
  created_at: "{date_iso}"
  timezone: "America/Chicago"
  source_range: "today"

origin:
  machine: "{origin['machine']}"
  mac: "{origin['mac']}"
  ip: "{origin['ip']}"
  os: "{origin['os']}"

tags:
  - servitus
  - daily-log
---

# Daily Log — {pretty}

## 1) Raw Input
{content.strip()}

## 2) Summary
<add summary or let Servetus/LLM fill this later>

## 3) Key Points
-

## 4) Events Detected
-

## 5) Next Actions
- [ ]
""".rstrip() + "\n"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_log(args):
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if args:
        raw = " ".join(args)
    else:
        print("Enter your log content. Press Ctrl-D (or Ctrl-Z on Windows) when done:")
        raw = sys.stdin.read().strip()

    if not raw:
        print("No content provided, aborting.")
        return

    today    = datetime.now()
    filename = today.strftime("%Y-%m-%d-servetus-log.md")
    path     = LOG_DIR / filename

    if path.exists():
        origin = get_origin()
        entry  = (
            f"\n\n---\n"
            f"# Additional Entry\n"
            f"<!-- origin: {origin['machine']} | {origin['mac']} | {origin['ip']} | {origin['os']} -->\n\n"
            f"{raw}\n"
        )
        with open(path, "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"Appended to existing log: {path}")
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(build_daily_log(raw))
        print(f"Created new daily log: {path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python servetus_cli.py log [text...]")
        sys.exit(1)

    command = sys.argv[1]
    args    = sys.argv[2:]

    if command == "log":
        cmd_log(args)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
