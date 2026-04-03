#!/usr/bin/env python3
"""
Servetus Launch Menu
--------------------
Interactive context picker shown at the start of every sc session.

Displays:
  - Open sessions     (with < resume if a matching JSONL is found)
  - Recent sessions   (last 4 closed, with < resume if session_id known)
  - Active arcs       (from 05-Arcs/ — status: active)
  - Recent projects   (from 04-Projects/ — sorted by mtime)

User picks a number, types N for a new label, or presses Enter to skip.

Side effects:
  - Writes selected room + resume_id into ~/.servetus_session.json
  - Appends a new "open" entry to ~/.servetus_sessions.json (session registry)

Output (stdout, two lines — for sc to capture):
  line 1: room label  (may be empty)
  line 2: resume_id   (may be empty)

Display and input go to /dev/tty directly so stdout capture in sc is clean.

Usage:
    python3 launch-menu.py [vault_path]
"""

import json, pathlib, re, socket, sys
from datetime import datetime

VAULT        = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 \
               else pathlib.Path(__file__).resolve().parent.parent
HOME         = pathlib.Path.home()
SESSION_F    = HOME / ".servetus_session.json"    # single current session
REGISTRY_F   = HOME / ".servetus_sessions.json"  # registry of all sessions
PROJECTS_DIR = HOME / ".claude" / "projects"

W = 72
C = W - 4

BOLD    = "\033[1m"
DIM     = "\033[2m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
CYAN    = "\033[36m"
RESET   = "\033[0m"
PURPLE  = "\033[38;5;135m"   # Obsidian purple  ≈ #7B4FDB
NC_BLUE = "\033[38;5;39m"    # Nextcloud blue   ≈ #0082C9

OB_GEM   = "◆"   # Obsidian — crystalline gem
NC_CLOUD = "☁"   # Nextcloud — cloud


# ── Box drawing ───────────────────────────────────────────────────────────────

def _plain(s):
    return re.sub(r'\033\[[0-9;]*m', '', s)

def top():   return f"{PURPLE}╔{'═' * (W - 2)}╗{RESET}"
def bot():   return f"{PURPLE}╚{'═' * (W - 2)}╝{RESET}"
def div():   return f"{PURPLE}╠{'═' * (W - 2)}╣{RESET}"
def blank(): return f"{PURPLE}║{' ' * (W - 2)}║{RESET}"

def row(content, indent=2):
    plain  = _plain(content)
    prefix = " " * indent
    avail  = C - len(prefix)
    if len(plain) > avail:
        content = plain[:avail - 1] + "…"
    pad = C - len(_plain(content)) - indent
    return f"{PURPLE}║{RESET}{prefix}{content}{' ' * max(0, pad)}  {PURPLE}║{RESET}"

def item_row(n, label, detail="", marker=""):
    num   = f"{CYAN}{n:>2}.{RESET} "
    short = label[:30]
    lbl   = f"{BOLD}{short}{RESET}{' ' * (30 - len(short))}"  # bold text only; pad outside bold
    det   = f"  {DIM}{detail}{RESET}" if detail else ""
    mrk   = f"  {marker}" if marker else ""
    return row(f"{num}{lbl}{det}{mrk}", indent=2)

def section(title):
    return [div(), row(f"{NC_BLUE}{BOLD}{title}{RESET}", indent=2)]


# ── Session registry ──────────────────────────────────────────────────────────

def load_registry():
    try:
        data = json.loads(REGISTRY_F.read_text()) if REGISTRY_F.exists() else []
        return [s for s in data if isinstance(s, dict)]
    except:
        return []

def save_registry(sessions):
    try:
        REGISTRY_F.write_text(json.dumps(sessions, indent=2))
    except:
        pass

def register_open(room, resume_id):
    sessions = load_registry()
    now_str  = datetime.now().isoformat(timespec="seconds")
    machine  = socket.gethostname()
    # Deduplicate: if an open entry for this vault+room+machine already exists
    # within the last 60 seconds, don't create another one
    for s in sessions:
        if (s.get("status") == "open"
                and s.get("vault") == str(VAULT)
                and s.get("machine") == machine
                and s.get("room") == room):
            try:
                age = abs((datetime.now() - datetime.fromisoformat(s["started"])).total_seconds())
                if age < 60:
                    return  # duplicate within same launch window — skip
            except Exception:
                pass
    sessions.append({
        "room":       room,
        "started":    now_str,
        "machine":    machine,
        "vault":      str(VAULT),
        "status":     "open",
        "session_id": resume_id,
        "closed":     None,
    })
    save_registry(sessions)


# ── Time formatting ───────────────────────────────────────────────────────────

def calendar_time(iso_str):
    """Return a short calendar stamp: 'Mar 17 15:04' — useful when relative time is ambiguous."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str).astimezone()
        return dt.strftime("%b %-d %H:%M")
    except:
        return ""

def relative_time(iso_str):
    if not iso_str:
        return ""
    try:
        dt   = datetime.fromisoformat(iso_str).astimezone()
        diff = int((datetime.now().astimezone() - dt).total_seconds())
        if diff < 60:     return "just now"
        if diff < 3600:   return f"{diff // 60}m ago"
        if diff < 86400:  return f"{diff // 3600}h {(diff % 3600) // 60}m ago"
        if diff < 172800: return "yesterday"
        return f"{diff // 86400}d ago"
    except:
        return ""


# ── JSONL / resume detection ──────────────────────────────────────────────────

def find_project_dir():
    if not PROJECTS_DIR.exists():
        return None
    slug = str(VAULT).replace("/", "-").replace("\\", "-")
    d    = PROJECTS_DIR / slug
    if d.exists():
        return d
    parts = [p for p in VAULT.parts if p not in ("", "/")]
    for d in PROJECTS_DIR.iterdir():
        if d.is_dir() and all(p in d.name for p in parts[-2:]):
            return d
    return None

def find_jsonl_for_session(started_iso, project_dir):
    """Return the JSONL stem closest in time to started_iso, or None."""
    if not project_dir or not project_dir.exists() or not started_iso:
        return None
    try:
        started = datetime.fromisoformat(started_iso).astimezone()
    except:
        return None
    best, best_diff = None, float("inf")
    for jf in project_dir.glob("*.jsonl"):
        if "subagent" in jf.name:
            continue
        try:
            mtime = datetime.fromtimestamp(jf.stat().st_mtime).astimezone()
            diff  = abs((mtime - started).total_seconds())
            if diff < best_diff and diff < 86400:
                best_diff, best = diff, jf
        except:
            pass
    return best.stem if best else None


# ── Vault data ────────────────────────────────────────────────────────────────

def get_active_arcs():
    d = VAULT / "05-Arcs"
    if not d.exists():
        return []
    out = []
    for f in sorted(d.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.name.startswith("_"):
            continue
        try:
            text = f.read_text(errors="replace")
            if not text.startswith("---"):
                continue
            end = text.find("\n---", 3)
            fm  = text[3:end] if end != -1 else text[3:]
            sm  = re.search(r'^\s*status:\s*(.+)$', fm, re.M)
            if not sm or sm.group(1).strip().strip("'\"").lower() not in \
                    ("active", "open", "in-progress", "ongoing"):
                continue
            tm    = re.search(r'^\s*title:\s*["\']?(.+?)["\']?\s*$', fm, re.M)
            title = tm.group(1).strip().strip("'\"") if tm else f.stem
            # short_name: used as the room label when set — keeps statusline tight
            sn    = re.search(r'^\s*short_name:\s*["\']?(.+?)["\']?\s*$', fm, re.M)
            label = sn.group(1).strip().strip("'\"") if sn else title
            out.append({
                "title": title,
                "label": label,   # what becomes SERVETUS_ROOM
                "mtime": datetime.fromtimestamp(f.stat().st_mtime),
            })
        except:
            pass
    return out[:6]

def get_recent_projects():
    d = VAULT / "04-Projects"
    if not d.exists():
        return []
    out = []
    for sub in d.iterdir():
        if not sub.is_dir() or sub.name.startswith(("_", ".")):
            continue
        mtime = sub.stat().st_mtime
        for f in sub.rglob("*"):
            try:
                mtime = max(mtime, f.stat().st_mtime)
            except:
                pass
        out.append({"name": sub.name, "mtime": datetime.fromtimestamp(mtime)})
    return sorted(out, key=lambda x: x["mtime"], reverse=True)[:5]


# ── Interactive menu ──────────────────────────────────────────────────────────

def show_menu():
    registry    = load_registry()
    open_sess   = [s for s in registry if s.get("status") == "open"
                   and s.get("vault", "") == str(VAULT)]
    closed_sess = sorted(
        [s for s in registry if s.get("status") == "closed"],
        key=lambda s: s.get("closed") or "",
        reverse=True,
    )[:4]
    arcs        = get_active_arcs()
    projects    = get_recent_projects()
    project_dir = find_project_dir()

    now   = datetime.now().astimezone()
    lines = []
    items = []  # list of (room_label, resume_id_or_None)

    # Header
    lines.append(top())
    lines.append(row(
        f"{PURPLE}{BOLD}SERVETUS{RESET}"
        f"  {DIM}·{RESET}  "
        f"{PURPLE}{OB_GEM} Obsidian{RESET}  "
        f"{NC_BLUE}{NC_CLOUD} Nextcloud{RESET}  "
        f"{DIM}{now.strftime('%Y-%m-%d  %H:%M')}  ·  {socket.gethostname()}{RESET}",
        indent=2,
    ))
    lines.append(row(
        f"{DIM}What's the context for this window?{RESET}",
        indent=2,
    ))

    # Open sessions
    if open_sess:
        lines.extend(section("OPEN SESSIONS"))
        for s in open_sess:
            n      = len(items) + 1
            sid    = s.get("session_id") or ""
            resume = sid or find_jsonl_for_session(s.get("started"), project_dir)
            items.append((s.get("room", ""), resume))
            age    = relative_time(s.get("started", ""))
            # Show short ID if available; otherwise fall back to started timestamp
            id_tag = f"[{sid[:8]}]" if sid else calendar_time(s.get("started", ""))
            detail = f"{age}  ·  {id_tag}"
            marker = f"{GREEN}< resume{RESET}" if resume else ""
            lines.append(item_row(n, s.get("room") or "(no label)", detail, marker))

    # Recent closed sessions
    if closed_sess:
        lines.extend(section("RECENT SESSIONS"))
        for s in closed_sess:
            n      = len(items) + 1
            resume = s.get("session_id") or \
                     find_jsonl_for_session(s.get("started"), project_dir)
            items.append((s.get("room", ""), resume))
            age    = relative_time(s.get("closed") or s.get("started", ""))
            marker = f"{DIM}< resume{RESET}" if resume else ""
            lines.append(item_row(n, s.get("room") or "(no label)", age, marker))

    # Active arcs
    if arcs:
        lines.extend(section("ACTIVE ARCS"))
        for a in arcs:
            n = len(items) + 1
            # label = short_name if defined, else title — this becomes SERVETUS_ROOM
            items.append((a["label"], None))
            # show full title in menu, label (short_name) in parens if different
            display = a["title"]
            if a["label"] != a["title"]:
                display = f"{a['title']}  {DIM}[{a['label']}]{RESET}"
            lines.append(item_row(n, display, relative_time(a["mtime"].isoformat())))

    # Recent projects
    if projects:
        lines.extend(section("PROJECTS"))
        for p in projects:
            n = len(items) + 1
            items.append((p["name"], None))
            lines.append(item_row(n, p["name"], relative_time(p["mtime"].isoformat())))

    if not items:
        lines.append(blank())
        lines.append(row(f"{DIM}No sessions, arcs, or projects found yet.{RESET}", indent=4))

    # Footer
    n_hint = f"1–{len(items)}" if items else "—"
    lines.append(div())
    lines.append(row(
        f"  {PURPLE}[{n_hint}]{RESET} continue   "
        f"  {PURPLE}[N]{RESET} new label   "
        f"  {PURPLE}[Enter]{RESET} today's SOC",
        indent=2,
    ))
    lines.append(bot())
    lines.append("")

    # Write display to /dev/tty so stdout capture in sc stays clean
    try:
        tty = open("/dev/tty", "w")
        tty.write("\n".join(lines) + "\n")
        tty.write("  Context: ")
        tty.flush()
        tty_in = open("/dev/tty", "r")
        raw    = _plain(tty_in.readline()).strip()
        tty.write("\n")
        tty.flush()
    except (OSError, IOError):
        # Fallback if /dev/tty unavailable (e.g. non-interactive)
        return "", None

    room, resume_id = "", None

    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(items):
            room, resume_id = items[idx]
        # else treat as invalid → no context
    elif raw.upper() == "N":
        try:
            tty.write("  Label: ")
            tty.flush()
            room = _plain(tty_in.readline()).strip()
            tty.write("\n")
            tty.flush()
        except:
            room = ""
    elif raw:
        # Typed a name directly instead of a number
        room = raw
    else:
        # Enter with no input → default to today's SOC
        today = datetime.now().strftime("%Y-%m-%d")
        room = f"{today}_SOC"
        # Find the most recent JSONL from today to resume
        # BUT skip sessions that are marked "closed" in the registry
        closed_ids = {
            s.get("session_id") for s in registry
            if s.get("status") == "closed" and s.get("session_id")
        }
        if project_dir and project_dir.exists():
            today_jsonls = []
            for jf in project_dir.glob("*.jsonl"):
                if "subagent" in jf.name:
                    continue
                if jf.stem in closed_ids:
                    continue  # Skip closed sessions
                try:
                    mtime = datetime.fromtimestamp(jf.stat().st_mtime)
                    if mtime.strftime("%Y-%m-%d") == today:
                        today_jsonls.append((mtime, jf.stem))
                except Exception:
                    pass
            if today_jsonls:
                today_jsonls.sort(reverse=True)
                resume_id = today_jsonls[0][1]

    try:
        tty.close()
        tty_in.close()
    except:
        pass

    return room, resume_id


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    room, resume_id = show_menu()

    # Write into ~/.servetus_session.json so launch-brief.py reads the room
    # and sc can read resume_id before brief runs
    try:
        existing = {}
        if SESSION_F.exists():
            try:
                existing = json.loads(SESSION_F.read_text())
            except:
                pass
        existing["room"]      = room
        existing["resume_id"] = resume_id or ""
        SESSION_F.write_text(json.dumps(existing, indent=2))
    except:
        pass

    # Register this session as open
    register_open(room, resume_id)

    # Output for sc: room on line 1, resume_id on line 2
    print(room)
    print(resume_id or "")


if __name__ == "__main__":
    main()
