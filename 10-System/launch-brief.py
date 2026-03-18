#!/usr/bin/env python3
"""
Servetus Launch Brief

Prints the 8-gauge cluster to the terminal, then writes
~/.servetus_session.json so statusline.sh can show ACTIVE state.

Called by ~/bin/sc before handing off to Claude Code.
Usage: python3 launch-brief.py [vault_path]
"""

import json, os, pathlib, re, socket, subprocess, sys, time
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = pathlib.Path(__file__).resolve().parent
VAULT       = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 \
              else SCRIPT_DIR.parent
HOME        = pathlib.Path.home()
PROJECTS    = HOME / ".claude" / "projects"
SESSION_F   = HOME / ".servetus_session.json"
CONTEXT_LIM = 200_000
W           = 72    # total box width
C           = W - 6 # inner content width (2 borders + 2-space padding each side)
PIPE_L      = 2     # left pipe column  (╦ breaks box bottom here)
PIPE_R      = 5     # right pipe column (╦ breaks box bottom here)
BRAIN_W     = 38    # brain box outer width (left-justified, ≤ Claude Code footer)
MODEL       = "claude-sonnet-4-6"
MONTHS      = ["","Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]
now         = datetime.now()

# ── ANSI ──────────────────────────────────────────────────────────────────────
BOLD  = "\033[1m"
DIM   = "\033[2m"
GREEN = "\033[32m"
YELLOW= "\033[33m"
RED   = "\033[31m"
RESET = "\033[0m"

# ── Box drawing ───────────────────────────────────────────────────────────────
def _plain(s):
    return re.sub(r'\033\[[0-9;]*m', '', s)

def top():  return "╔" + "═"*(W-2) + "╗"
def div():  return "╠" + "═"*(W-2) + "╣"
def bot():
    # Bottom border with ╦ openings at PIPE_L and PIPE_R — pipes exit downward here
    return (
        "╚"
        + "═" * (PIPE_L - 1)
        + "╦"
        + "═" * (PIPE_R - PIPE_L - 1)
        + "╦"
        + "═" * (W - PIPE_R - 2)
        + "╝"
    )

def row(content):
    plain = _plain(content)
    if len(plain) > C:
        content = plain[:C-1] + "…"
    pad = C - len(_plain(content))
    return f"║  {content}{' ' * max(0, pad)}  ║"

def lrow(label, value, lw=10):
    """Fixed-width label + value row."""
    return row(f"{label:<{lw}}{value}")

def tbar(pct, width=18):
    filled = max(0, min(width, int(pct * width / 100)))
    return "█" * filled + "░" * (width - filled)

def fmtk(n):
    return f"{n // 1000}k" if n >= 1000 else str(n)

# ── Data collectors ───────────────────────────────────────────────────────────
def read_fm(path):
    """Parse minimal frontmatter: status, title, tags."""
    try:
        text = path.read_text(errors='replace')
        if not text.startswith('---'):
            return {}
        end = text.find('\n---', 3)
        fm = text[3:end] if end != -1 else text[3:]
        result = {}
        m = re.search(r'^\s+status:\s*(.+)$', fm, re.M)
        if m: result['status'] = m.group(1).strip().strip('"\'')
        m = re.search(r'title:\s*["\']?(.+?)["\']?\s*$', fm, re.M)
        if m: result['title'] = m.group(1).strip().strip('"\'')
        result['tags'] = re.findall(r'^\s+-\s+(\S+)', fm, re.M)
        return result
    except:
        return {}

def session_stats():
    if not PROJECTS.exists():
        return None
    candidates = sorted(
        [p for p in PROJECTS.rglob("*.jsonl") if "subagents" not in str(p)],
        key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not candidates:
        return None
    in_tok = cache_r = cache_c = 0
    user_n = asst_n = 0
    timestamps = []
    try:
        for raw in candidates[0].read_text(errors='replace').splitlines():
            if not raw.strip(): continue
            try: obj = json.loads(raw)
            except: continue
            t = obj.get('type', '')
            ts = obj.get('timestamp')
            if ts: timestamps.append(ts)
            if t == 'user':
                user_n += 1
            elif t == 'assistant':
                asst_n += 1
                u = obj.get('message', {}).get('usage', {})
                if u:
                    in_tok  = u.get('input_tokens', in_tok)
                    cache_r = u.get('cache_read_input_tokens', cache_r)
                    cache_c = u.get('cache_creation_input_tokens', cache_c)
    except:
        pass
    total = in_tok + cache_r + cache_c
    pct   = min(100, total * 100 // CONTEXT_LIM)
    first_ts = last_ts = None
    if timestamps:
        try:
            first_ts = datetime.fromisoformat(timestamps[0].replace('Z','+00:00')).astimezone()
            last_ts  = datetime.fromisoformat(timestamps[-1].replace('Z','+00:00')).astimezone()
        except: pass
    return dict(total=total, pct=pct, user=user_n, asst=asst_n,
                first_ts=first_ts, last_ts=last_ts)

def memory_stats():
    cm    = VAULT / "CLAUDE.md"
    size  = cm.stat().st_size if cm.exists() else 0
    tkit  = VAULT / "Toolkit"
    specs = sorted([f for f in tkit.glob("*.md") if not f.name.startswith('_')]) \
            if tkit.exists() else []
    return dict(claude_kb=size / 1024, specs=specs)

def active_arcs():
    d = VAULT / "05-Arcs"
    if not d.exists(): return []
    out = []
    for f in sorted(d.glob("*.md")):
        if f.name.startswith('_'): continue
        fm = read_fm(f)
        if fm.get('status', '').lower() == 'active':
            out.append(fm.get('title', f.stem))
    return out

def projects():
    d = VAULT / "04-Projects"
    if not d.exists(): return []
    out = []
    for sub in d.iterdir():
        if not sub.is_dir() or sub.name.startswith(('_', '.')): continue
        mtime = sub.stat().st_mtime
        for f in sub.rglob("*"):
            try: mtime = max(mtime, f.stat().st_mtime)
            except: pass
        out.append((sub.name, mtime))
    return sorted(out, key=lambda x: x[1], reverse=True)

def radar_items():
    d = VAULT / "06-Radar"
    if not d.exists(): return []
    out = []
    for f in sorted(d.glob("*.md")):
        if f.name.startswith('_') or 'spec' in f.name or 'template' in f.name:
            continue
        fm = read_fm(f)
        out.append(dict(title=fm.get('title', f.stem), tags=fm.get('tags', [])))
    return out

def last_artifact():
    base = VAULT / "00-Artifacts"
    if not base.exists(): return None
    latest = None
    for yr in sorted(base.iterdir()):
        if not yr.is_dir(): continue
        for mo in sorted(yr.iterdir()):
            if not mo.is_dir(): continue
            for dy in sorted(mo.iterdir()):
                if dy.is_dir(): latest = dy.name
    return latest

def write_path():
    m = now.month
    return (f"00-Artifacts/{now.year}/{m:02d}-{MONTHS[m]}/"
            f"{now.year}-{m:02d}-{now.day:02d}/claude/")

def system_checks():
    checks = {}
    checks['session-close'] = (VAULT / "10-System" / "session-close.py").exists()
    checks['statusline']    = (HOME / ".claude" / "statusline.sh").exists()
    try:
        r = subprocess.run(['git', 'status', '--porcelain'], cwd=str(VAULT),
                           capture_output=True, text=True, timeout=3)
        if r.returncode == 0:
            changed = len([l for l in r.stdout.splitlines() if l.strip()])
            checks['git'] = 'clean' if not changed else f"{changed} pending"
        else:
            checks['git'] = None
    except:
        checks['git'] = None
    return checks

def version():
    try: return (VAULT / "10-System" / "VERSION").read_text().strip()
    except: return "0.x"

def session_registry():
    """Load ~/.servetus_sessions.json, return [] on any failure."""
    registry = HOME / ".servetus_sessions.json"
    if not registry.exists():
        return []
    try:
        return json.loads(registry.read_text())
    except:
        return []

def last_closed_session(sessions):
    """Most recent closed session for this vault."""
    closed = [s for s in sessions
              if s.get("status") == "closed"
              and s.get("vault") == str(VAULT)
              and s.get("closed")]
    if not closed:
        return None
    return max(closed, key=lambda s: s["closed"])

def other_open_sessions(sessions):
    """Open sessions for this vault other than the one we just started."""
    return [s for s in sessions
            if s.get("status") == "open"
            and s.get("vault") == str(VAULT)
            and s.get("started") != CURRENT_STARTED]

def elapsed(ts_str):
    """Human-readable time since an ISO timestamp string."""
    if not ts_str:
        return "?"
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo:
            diff = datetime.now(dt.tzinfo) - dt
        else:
            diff = now - dt
        secs = int(diff.total_seconds())
    except:
        return "?"
    if secs < 60:      return f"{secs}s ago"
    if secs < 3600:    return f"{secs // 60}m ago"
    if secs < 86400:   return f"{secs // 3600}h {(secs % 3600) // 60}m ago"
    days = secs // 86400
    return f"{days}d ago"

def fmt_closed_ts(ts_str):
    """Format a close timestamp for display: 'Mon 05:13' or 'Mar 15 22:41'."""
    if not ts_str:
        return ""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo:
            dt = dt.astimezone()
        else:
            dt = dt
        if dt.date() == now.date():
            return dt.strftime("today %H:%M")
        if (now.date() - dt.date()).days == 1:
            return dt.strftime("yesterday %H:%M")
        return dt.strftime("%b %d %H:%M")
    except:
        return ts_str[:16]

# ── Write session file ────────────────────────────────────────────────────────
CURRENT_STARTED = now.isoformat(timespec="seconds")  # stable key for this run

def write_session():
    room = os.environ.get("SERVETUS_ROOM", "")
    # ~/.servetus_session.json — current session state (statusline reads this)
    try:
        SESSION_F.write_text(json.dumps({
            "started": CURRENT_STARTED,
            "llm":     MODEL,
            "vault":   str(VAULT),
            "machine": socket.gethostname(),
            "room":    room,
        }, indent=2))
    except:
        pass
    # ~/.servetus_sessions.json — registry (append open entry)
    registry = HOME / ".servetus_sessions.json"
    try:
        sessions = json.loads(registry.read_text()) if registry.exists() else []
    except:
        sessions = []
    sessions.append({
        "room":       room,
        "started":    CURRENT_STARTED,
        "machine":    socket.gethostname(),
        "vault":      str(VAULT),
        "status":     "open",
        "session_id": None,
        "closed":     None,
    })
    try:
        registry.write_text(json.dumps(sessions, indent=2))
    except:
        pass

# ── Funnel animation ──────────────────────────────────────────────────────────
def funnel_animation():
    """
    Pipes exit through ╦ openings in the box bottom border, drop 3 rows,
    then spread right into the brain box — left-justified, like a plug.

    Phase 1: pipe rows print dim, one at a time.
    Phase 2: brain box materializes in green.
    """
    BRAIN_I   = BRAIN_W - 2  # inner content width = 36
    PIPE_ROWS = 3

    # Two pipes dropping from the ╦ openings in the box bottom
    pipe_row = " " * PIPE_L + "║" + " " * (PIPE_R - PIPE_L - 1) + "║"

    # Spread row: pipes expand right into brain box top
    #   ╔═╝  ╚══...══╗
    spread = (
        "╔" + "═" * (PIPE_L - 1) + "╝"
        + " " * (PIPE_R - PIPE_L - 1)
        + "╚" + "═" * (BRAIN_W - PIPE_R - 2) + "╗"
    )

    def brow(content):
        return "║" + content[:BRAIN_I].ljust(BRAIN_I) + "║"

    # Brain art — mascot pending (task #1). Placeholder until art arrives.
    brain = [
        brow(""),
        brow("  [ mascot art — task #1 ]"),
        brow(""),
        "╚" + "═" * BRAIN_I + "╝",
    ]

    # Phase 1: pipes drop, dim
    for _ in range(PIPE_ROWS):
        sys.stdout.write(f"{DIM}{pipe_row}{RESET}\n")
        sys.stdout.flush()
        time.sleep(0.060)
    sys.stdout.write(f"{DIM}{spread}{RESET}\n")
    sys.stdout.flush()

    # Phase 2: brain materializes, green
    time.sleep(0.060)
    for line in brain:
        sys.stdout.write(f"{GREEN}{line}{RESET}\n")
        sys.stdout.flush()
        time.sleep(0.045)

    sys.stdout.write("\n")
    sys.stdout.flush()


# ── Print brief ───────────────────────────────────────────────────────────────
def main():
    write_session()

    sess  = session_stats()
    mem   = memory_stats()
    arcs  = active_arcs()
    projs = projects()
    radar = radar_items()
    art   = last_artifact()
    wpath = write_path()
    sys_  = system_checks()
    ver   = version()
    reg   = session_registry()
    last  = last_closed_session(reg)
    other = other_open_sessions(reg)
    vault_sessions = [s for s in reg if s.get("vault") == str(VAULT)]
    is_first = len(vault_sessions) <= 1  # only the current open one

    out = []

    # Title
    out.append(top())
    room  = os.environ.get("SERVETUS_ROOM", "")
    room_suffix = f"  ·  {YELLOW}{room}{RESET}" if room else ""
    title = f"{BOLD}SERVETUS{RESET}  ●  Memory Architecture Layer{room_suffix}"
    right = f"v{ver}  {now.strftime('%Y-%m-%d %H:%M')}"
    gap   = C - len(_plain(title)) - len(right)
    out.append(row(title + " " * max(1, gap) + right))

    # SESSION
    out.append(div())
    if sess:
        pct = sess['pct']
        rem = CONTEXT_LIM - sess['total']
        bc  = GREEN if pct < 60 else (YELLOW if pct < 80 else RED)
        out.append(lrow("SESSION",
            f"{bc}{tbar(pct)}{RESET}  {pct}%  |  "
            f"{fmtk(sess['total'])} used  |  ↑{sess['user']} ↓{sess['asst']}"))
        detail = f"{fmtk(rem)} remaining"
        if sess['last_ts']:
            detail += f"  ·  last active {sess['last_ts'].strftime('%Y-%m-%d %H:%M')}"
        out.append(lrow("", detail))
        if pct >= 80:
            out.append(lrow("", f"{RED}context {pct}% full — recommend a new session{RESET}"))
        elif pct >= 60:
            out.append(lrow("", f"{YELLOW}context filling — consider new session for unrelated work{RESET}"))
    else:
        out.append(lrow("SESSION", f"{GREEN}fresh — no prior session found{RESET}"))

    # LAST SESSION
    out.append(div())
    if is_first:
        out.append(lrow("LAST", f"{GREEN}first session — no prior history{RESET}"))
    elif last:
        room_s  = last.get("room", "") or "—"
        closed  = last.get("closed", "")
        when    = fmt_closed_ts(closed)
        ago     = elapsed(closed)
        # Summary fields written by session-close (if present)
        turns   = last.get("turns", "")
        files   = last.get("files_touched", [])
        dur     = last.get("duration", "")
        line1 = f"{ago}  ·  {when}  ·  {YELLOW}{room_s}{RESET}"
        out.append(lrow("LAST", line1))
        detail_parts = []
        if turns:    detail_parts.append(f"{turns} turns")
        if dur:      detail_parts.append(dur)
        if files:    detail_parts.append("  ".join(files[:4]) + (f"  +{len(files)-4}" if len(files) > 4 else ""))
        if detail_parts:
            out.append(lrow("", f"{DIM}{'  ·  '.join(detail_parts)}{RESET}"))
    else:
        out.append(lrow("LAST", f"{DIM}no prior closed sessions found{RESET}"))

    # OTHER OPEN SESSIONS
    if other:
        out.append(div())
        for s in other[:3]:
            s_room    = s.get("room", "—") or "—"
            s_started = fmt_closed_ts(s.get("started", ""))
            out.append(lrow("OPEN", f"{YELLOW}{s_room}{RESET}  ·  started {s_started}"))

    # MEMORY
    out.append(div())
    # Build spec name list that fits within inner width (label=10, so budget=C-10)
    budget = C - 10
    spec_parts = []
    for f in mem['specs']:
        candidate = "  ".join(spec_parts + [f.stem])
        if len(candidate) > budget - 5:  # leave room for "+N"
            remaining = len(mem['specs']) - len(spec_parts)
            spec_parts.append(f"+{remaining}")
            break
        spec_parts.append(f.stem)
    spec_names = "  ".join(spec_parts)
    out.append(lrow("MEMORY",
        f"CLAUDE.md {mem['claude_kb']:.1f}kb  +  {len(mem['specs'])} Toolkit specs"))
    if spec_names:
        out.append(lrow("", f"{DIM}{spec_names}{RESET}"))

    # RADAR
    out.append(div())
    if radar:
        tags    = [t for item in radar for t in item['tags']]
        tag_str = "  ".join(f"#{t}" for t in tags[:6])
        out.append(lrow("RADAR",
            f"{len(radar)} items" + (f"  |  {tag_str}" if tag_str else "")))
        titles = "  ·  ".join(item['title'] for item in radar[:3])
        out.append(lrow("", f"{DIM}{titles}{RESET}"))
    else:
        out.append(lrow("RADAR", f"{DIM}no items filed{RESET}"))

    # ARC
    out.append(div())
    if arcs:
        budget = C - 10
        arc_parts = []
        for a in arcs:
            candidate = "  ·  ".join(arc_parts + [a])
            if len(candidate) > budget - 6:
                arc_parts.append(f"+{len(arcs) - len(arc_parts)}")
                break
            arc_parts.append(a)
        arc_str = "  ·  ".join(arc_parts)
        out.append(lrow("ARC", f"{GREEN}{arc_str}{RESET}"))
    else:
        out.append(lrow("ARC", f"{DIM}no active arcs{RESET}"))

    # PROJECTS
    out.append(div())
    if projs:
        budget = C - 10
        proj_parts = []
        for p in projs:
            candidate = "  ·  ".join(proj_parts + [p[0]])
            if len(candidate) > budget - 6:
                proj_parts.append(f"+{len(projs) - len(proj_parts)}")
                break
            proj_parts.append(p[0])
        names  = "  ·  ".join(proj_parts)
        top_dt = datetime.fromtimestamp(projs[0][1])
        out.append(lrow("PROJECTS", names))
        out.append(lrow("",
            f"{DIM}most recent: {projs[0][0]}  —  {top_dt.strftime('%Y-%m-%d')}{RESET}"))
    else:
        out.append(lrow("PROJECTS", f"{DIM}none{RESET}"))

    # TEMPORAL
    out.append(div())
    today_ym = now.strftime("%Y-%m")
    if art:
        art_ym = art[:7]
        if art_ym >= today_ym:
            period = f"{GREEN}present{RESET} ({today_ym})"
        else:
            period = f"{YELLOW}historical{RESET} ({art_ym})"
        out.append(lrow("TEMPORAL", f"{period}  ·  last artifact: {art}"))
    else:
        out.append(lrow("TEMPORAL", f"{DIM}no artifacts yet{RESET}"))

    # WRITE
    out.append(div())
    out.append(lrow("WRITE", f"→ {wpath}"))

    # SYSTEM
    out.append(div())
    parts = []
    for key, val in sys_.items():
        if val is True or val == 'clean':
            parts.append(f"{GREEN}{key} ✓{RESET}")
        elif val is False or val is None:
            parts.append(f"{RED}{key} ✗{RESET}")
        else:
            parts.append(f"{YELLOW}{key}: {val}{RESET}")
    out.append(lrow("SYSTEM", "   ".join(parts)))

    # ORPHANS — unarchived sessions flagged by last session-close
    orphan_file = VAULT / "10-System" / "orphan-sessions.json"
    if orphan_file.exists():
        try:
            orphans = json.loads(orphan_file.read_text())
            if orphans:
                out.append(div())
                dates = ", ".join(o.get("date", o.get("short_id", "?")) for o in orphans)
                out.append(lrow(
                    f"{YELLOW}ORPHANS{RESET}",
                    f"{YELLOW}{len(orphans)} unarchived session(s): {dates} — run session-close <path> to recover{RESET}"
                ))
        except Exception:
            pass

    out.append(bot())
    print("\n".join(out))
    print()
    funnel_animation()

if __name__ == "__main__":
    main()
