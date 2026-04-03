#!/usr/bin/env python3
"""
secretary.py — Deterministic context assembly layer for Servetus.

Reads all known registers, outputs a structured context object.
No LLM involvement. Pure data collection and filtering.

This is the foundation everything else stands on:
  50–75% of daily ops are deterministic lookups.
  The secretary handles all of them before any LLM is invoked.

Output: JSON context object printed to stdout (or returned as dict).
        Passed to the packaging layer, then to the LLM endpoint.

Usage:
  python3 10-System/secretary.py                    # full context, JSON stdout
  python3 10-System/secretary.py --pretty           # pretty-printed JSON
  python3 10-System/secretary.py --section hopper   # single section only
  python3 10-System/secretary.py --room tnft3avs    # context scoped to a room

Spec: 10-System/dev-backlog/secretary-script.md
      10-System/dev-backlog/context-packaging-spec.md
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────

VAULT        = Path(__file__).parent.parent
CONFIG       = VAULT / "config"
SYSTEM       = VAULT / "10-System"
WITNESSES    = VAULT / "08-Witnesses"
RADAR        = VAULT / "06-Radar"
ARTIFACTS    = VAULT / "00-Artifacts"
MEMORIES     = VAULT / "02-Memories"

HOPPER_LOG   = SYSTEM / "hopper-events.log"
HOPPER_CURSOR= SYSTEM / "hopper-cursor.txt"
ROOMS_FILE   = CONFIG / "talk-rooms.json"
LAST_BRIEF   = SYSTEM / "last-session-brief.md"
DEV_BACKLOG  = SYSTEM / "dev-backlog"


# ── Hopper ────────────────────────────────────────────────────────────────────

def read_hopper(limit: int = 20) -> dict:
    """
    Return new hopper events since last cursor position.
    Cursor is a line count — lines after cursor are new.
    """
    result = {"new_items": [], "cursor_was": 0, "cursor_now": 0, "total_lines": 0}

    if not HOPPER_LOG.exists():
        return result

    lines = HOPPER_LOG.read_text(errors="replace").splitlines()
    result["total_lines"] = len(lines)

    cursor = 0
    if HOPPER_CURSOR.exists():
        try:
            cursor = int(HOPPER_CURSOR.read_text().strip())
        except ValueError:
            cursor = 0

    result["cursor_was"] = cursor
    new_lines = lines[cursor:]
    result["cursor_now"] = len(lines)

    # Parse event lines: timestamp | type | detail
    for line in new_lines[-limit:]:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3:
            result["new_items"].append({
                "timestamp": parts[0],
                "type":      parts[1],
                "detail":    parts[2],
                "raw":       line,
            })
        else:
            result["new_items"].append({"raw": line})

    return result


def advance_hopper_cursor():
    """Move cursor to current end of log (mark as seen)."""
    if HOPPER_LOG.exists():
        count = len(HOPPER_LOG.read_text(errors="replace").splitlines())
        HOPPER_CURSOR.write_text(str(count))


# ── Radar ─────────────────────────────────────────────────────────────────────

def read_radar() -> dict:
    """Read active radar items and open loops from 06-Radar/."""
    result = {"open_loops": [], "radar_items": [], "overdue": []}

    if not RADAR.exists():
        return result

    open_loops_file = RADAR / "open-loops.md"
    if open_loops_file.exists():
        text = open_loops_file.read_text(errors="replace")
        # Extract checkbox items
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("- [ ]"):
                result["open_loops"].append(line[5:].strip())
            elif line.startswith("- [x]") or line.startswith("- [X]"):
                pass  # Done items — skip

    # Scan other .md files in Radar for overdue markers
    today = datetime.now().strftime("%Y-%m-%d")
    for f in sorted(RADAR.glob("*.md")):
        if f.name == "open-loops.md":
            continue
        try:
            text = f.read_text(errors="replace")
            # Look for due dates in frontmatter or body
            due_matches = re.findall(r"due[_\s]*(?:date)?[:\s]+(\d{4}-\d{2}-\d{2})", text, re.I)
            for due in due_matches:
                if due < today:
                    result["overdue"].append({"file": f.name, "due": due})
            # Collect title
            title_match = re.search(r"^#\s+(.+)$", text, re.M)
            title = title_match.group(1).strip() if title_match else f.stem
            result["radar_items"].append({"file": f.name, "title": title})
        except Exception:
            continue

    return result


# ── Last session brief ────────────────────────────────────────────────────────

def read_last_brief() -> dict:
    """Read the last session brief if it exists."""
    if not LAST_BRIEF.exists():
        return {"exists": False, "content": None}

    text = LAST_BRIEF.read_text(errors="replace")
    # Extract modified date from frontmatter or file mtime
    mtime = datetime.fromtimestamp(LAST_BRIEF.stat().st_mtime).isoformat()
    return {
        "exists": True,
        "modified": mtime,
        "preview": text[:800].strip(),
    }


# ── Talk rooms ────────────────────────────────────────────────────────────────

def read_rooms(room_filter: Optional[str] = None) -> dict:
    """Load room registry. Optionally filter to a single room token."""
    if not ROOMS_FILE.exists():
        return {}
    rooms = json.loads(ROOMS_FILE.read_text())
    if room_filter:
        return {k: v for k, v in rooms.items() if k == room_filter}
    return rooms


# ── Witnesses ─────────────────────────────────────────────────────────────────

def list_witnesses() -> list:
    """Return list of known witness IDs."""
    if not WITNESSES.exists():
        return []
    return [f.stem.replace("_witness", "") for f in WITNESSES.glob("*_witness.md")]


def read_witness(actor_id: str) -> Optional[dict]:
    """Read a single witness file and return key fields."""
    witness_path = WITNESSES / f"{actor_id}_witness.md"
    if not witness_path.exists():
        return None

    text = witness_path.read_text(errors="replace")
    result = {"actor_id": actor_id, "raw_preview": text[:500]}

    # Extract display name
    name_match = re.search(r"display_name[:\s]+[\"']?([^\"'\n]+)[\"']?", text, re.I)
    if name_match:
        result["display_name"] = name_match.group(1).strip()

    # Extract circle
    circle_match = re.search(r"circle[:\s]+[\"']?(\w+)[\"']?", text, re.I)
    if circle_match:
        result["circle"] = circle_match.group(1).strip()

    return result


# ── Dev backlog ───────────────────────────────────────────────────────────────

def read_dev_backlog() -> list:
    """Summarize open dev backlog items."""
    items = []
    if not DEV_BACKLOG.exists():
        return items

    for f in sorted(DEV_BACKLOG.glob("*.md")):
        try:
            text = f.read_text(errors="replace")
            status_match = re.search(r"^status[:\s]+(\S+)", text, re.M | re.I)
            title_match  = re.search(r"^title[:\s]+[\"']?(.+)[\"']?$", text, re.M | re.I)
            priority_match = re.search(r"^priority[:\s]+(\S+)", text, re.M | re.I)

            status   = status_match.group(1).strip('"\'') if status_match else "unknown"
            title    = title_match.group(1).strip('"\'') if title_match else f.stem
            priority = priority_match.group(1).strip('"\'') if priority_match else "normal"

            if status not in ("done", "closed", "archived"):
                items.append({
                    "file":     f.name,
                    "title":    title,
                    "status":   status,
                    "priority": priority,
                })
        except Exception:
            continue

    return items


# ── Recent artifacts ──────────────────────────────────────────────────────────

def recent_artifacts(days: int = 3, limit: int = 10) -> list:
    """List most recently modified artifact .md files."""
    if not ARTIFACTS.exists():
        return []

    cutoff = datetime.now().timestamp() - (days * 86400)
    found  = []

    for f in ARTIFACTS.rglob("*.md"):
        try:
            mtime = f.stat().st_mtime
            if mtime >= cutoff:
                found.append((mtime, f))
        except Exception:
            continue

    found.sort(reverse=True)
    return [
        {
            "path":     str(f.relative_to(VAULT)),
            "modified": datetime.fromtimestamp(t).isoformat(),
        }
        for t, f in found[:limit]
    ]


# ── Transcription queue state ─────────────────────────────────────────────────

def read_transcription_state() -> dict:
    """Read the transcription queue state file."""
    state_file = SYSTEM / ".transcription-queue-state.json"
    if not state_file.exists():
        return {"processed": {}}
    try:
        state = json.loads(state_file.read_text())
        processed = state.get("processed", {})
        ok    = sum(1 for v in processed.values() if v.get("status") == "ok")
        error = sum(1 for v in processed.values() if v.get("status") == "error")
        # Most recent completion
        recent = sorted(
            [(v.get("processed_at", ""), k) for k, v in processed.items()
             if v.get("status") == "ok"],
            reverse=True
        )
        return {
            "total_processed": ok,
            "total_errors":    error,
            "most_recent":     recent[0] if recent else None,
        }
    except Exception as e:
        return {"error": str(e)}


# ── System service status ─────────────────────────────────────────────────────

def read_service_status() -> dict:
    """Check which Servetus daemons are running (Linux only)."""
    services = [
        "servetus-talk-listener",
        "servetus-transcription-queue",
        "ollama",
    ]
    result = {}
    for svc in services:
        try:
            import subprocess
            r = subprocess.run(
                ["systemctl", "--user", "is-active", svc],
                capture_output=True, text=True, timeout=3
            )
            result[svc] = r.stdout.strip()
        except Exception:
            result[svc] = "unknown"
    return result


# ── Assembly ──────────────────────────────────────────────────────────────────

def assemble(room_filter: Optional[str] = None,
             section_filter: Optional[str] = None) -> dict:
    """
    Assemble the full context object from all registers.
    No LLM involvement — pure deterministic data collection.
    """
    now = datetime.now()
    ctx = {
        "generated_at": now.isoformat(),
        "vault": str(VAULT),
        "machine": os.uname().nodename if hasattr(os, "uname") else "unknown",
    }

    sections = {
        "hopper":         read_hopper,
        "radar":          read_radar,
        "last_brief":     read_last_brief,
        "witnesses":      lambda: {"known": list_witnesses()},
        "rooms":          lambda: read_rooms(room_filter),
        "dev_backlog":    read_dev_backlog,
        "recent_artifacts": recent_artifacts,
        "transcription":  read_transcription_state,
    }

    # Add service status only on Linux
    if sys.platform.startswith("linux"):
        sections["services"] = read_service_status

    if section_filter:
        if section_filter in sections:
            ctx[section_filter] = sections[section_filter]()
        else:
            ctx["error"] = f"Unknown section: {section_filter}. Available: {list(sections)}"
    else:
        for name, fn in sections.items():
            try:
                ctx[name] = fn()
            except Exception as e:
                ctx[name] = {"error": str(e)}

    return ctx


# ── CLI ───────────────────────────────────────────────────────────────────────

DAEMON_INTERVAL = 300  # seconds between daemon context refreshes (5 min)


def run_daemon():
    """
    Daemon mode: continuously refresh context and write a summary to
    10-System/last-session-brief.md every DAEMON_INTERVAL seconds.

    This is the mode used by the secretary container in docker-compose.
    It keeps last-session-brief.md current so the talk-listener always
    has a fresh context snapshot to inject into Claude's system prompt.
    """
    import time as _time

    print(f"[secretary] Daemon started — refreshing every {DAEMON_INTERVAL}s", file=sys.stderr)

    while True:
        try:
            ctx = assemble()
            brief_path = SYSTEM / "last-session-brief.md"

            # Build a concise markdown brief from the context
            lines = [
                f"# Secretary Brief — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                "",
            ]

            # Hopper
            hopper = ctx.get("hopper", {})
            new_items = hopper.get("new_items", [])
            if new_items:
                lines.append("## Hopper (new since last session)")
                for item in new_items[-10:]:
                    lines.append(f"- {item.get('raw', '')}")
                lines.append("")

            # Radar
            radar = ctx.get("radar", {})
            open_loops = radar.get("open_loops", [])
            if open_loops:
                lines.append("## Open Loops")
                for loop in open_loops[:5]:
                    lines.append(f"- {loop}")
                lines.append("")

            # Transcription queue
            tq = ctx.get("transcription", {})
            ok_count = tq.get("ok_count", 0)
            total    = tq.get("total_files", 0)
            inprog   = tq.get("in_progress", [])
            lines.append("## Transcription Queue")
            lines.append(f"- Completed: {ok_count}/{total}")
            if inprog:
                lines.append(f"- Processing: {', '.join(inprog)}")
            lines.append("")

            # Services
            svcs = ctx.get("services", {})
            if svcs:
                up = [k for k, v in svcs.items() if v.get("active")]
                down = [k for k, v in svcs.items() if not v.get("active")]
                lines.append("## Services")
                if up:
                    lines.append(f"- Up: {', '.join(up)}")
                if down:
                    lines.append(f"- Down: {', '.join(down)}")
                lines.append("")

            brief_path.write_text("\n".join(lines))
            print(f"[secretary] Brief updated: {len(lines)} lines", file=sys.stderr)

        except Exception as e:
            print(f"[secretary] Daemon error: {e}", file=sys.stderr)

        _time.sleep(DAEMON_INTERVAL)


def main():
    parser = argparse.ArgumentParser(
        description="Servetus secretary — deterministic context assembly"
    )
    parser.add_argument("--pretty",   action="store_true", help="Pretty-print JSON")
    parser.add_argument("--section",  metavar="NAME",      help="Output one section only")
    parser.add_argument("--room",     metavar="TOKEN",     help="Scope to a Talk room token")
    parser.add_argument("--advance",  action="store_true", help="Advance hopper cursor after read")
    parser.add_argument("--witness",  metavar="ACTOR_ID",  help="Look up a single witness")
    parser.add_argument("--daemon",   action="store_true",
                        help="Run continuously, refreshing last-session-brief.md every 5 min")
    args = parser.parse_args()

    if args.daemon:
        run_daemon()
        return  # run_daemon() loops forever

    if args.witness:
        result = read_witness(args.witness)
        if result is None:
            print(json.dumps({"error": f"No witness file for: {args.witness}"}))
        else:
            print(json.dumps(result, indent=2 if args.pretty else None))
        return

    ctx = assemble(room_filter=args.room, section_filter=args.section)

    indent = 2 if args.pretty else None
    print(json.dumps(ctx, indent=indent, default=str))

    if args.advance:
        advance_hopper_cursor()
        print("\n[secretary] Hopper cursor advanced.", file=sys.stderr)


if __name__ == "__main__":
    main()
