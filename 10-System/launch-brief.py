#!/usr/bin/env python3
"""
Servetus Launch Brief

Prints the session brief to the terminal, then writes
~/.servetus_session.json so statusline.sh can show ACTIVE state.

Called by ~/bin/sc before handing off to Claude Code.
Usage: python3 launch-brief.py [vault_path]
"""

import json, os, pathlib, re, socket, subprocess, sys, time
from datetime import datetime, timedelta

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
MODEL       = "claude-sonnet-4-6"
MONTHS      = ["","Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]
now         = datetime.now()

# ── ANSI ──────────────────────────────────────────────────────────────────────
BOLD    = "\033[1m"
DIM     = "\033[2m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
RED     = "\033[31m"
RESET   = "\033[0m"
PURPLE  = "\033[38;5;135m"

# ── Box drawing ───────────────────────────────────────────────────────────────
def _plain(s):
    return re.sub(r'\033\[[0-9;]*m', '', s)

def top():  return f"{PURPLE}╔{'═'*(W-2)}╗{RESET}"
def div():  return f"{PURPLE}╠{'═'*(W-2)}╣{RESET}"
def bot():  return f"{PURPLE}╚{'═'*(W-2)}╝{RESET}"

def row(content):
    plain = _plain(content)
    if len(plain) > C:
        content = plain[:C-1] + "…"
    pad = C - len(_plain(content))
    return f"{PURPLE}║{RESET}  {content}{' ' * max(0, pad)}  {PURPLE}║{RESET}"

def lrow(label, value, lw=10):
    return row(f"{label:<{lw}}{value}")

def tbar(pct, width=18):
    filled = max(0, min(width, int(pct * width / 100)))
    return "█" * filled + "░" * (width - filled)

def fmtk(n):
    return f"{n // 1000}k" if n >= 1000 else str(n)

# ── Data collectors ───────────────────────────────────────────────────────────
def read_fm(path):
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

def active_arcs(limit=3):
    """Return (titles[:limit], total_count) sorted by file mtime — most recent first."""
    d = VAULT / "05-Arcs"
    if not d.exists(): return [], 0
    files = []
    for f in d.glob("*.md"):
        if f.name.startswith('_'): continue
        fm = read_fm(f)
        if fm.get('status', '').lower() == 'active':
            files.append((fm.get('title', f.stem), f.stat().st_mtime))
    files.sort(key=lambda x: x[1], reverse=True)
    titles = [t for t, _ in files]
    return titles[:limit], len(titles)

def projects(limit=4):
    d = VAULT / "04-Projects"
    if not d.exists(): return [], 0
    out = []
    for sub in d.iterdir():
        if not sub.is_dir() or sub.name.startswith(('_', '.')): continue
        mtime = sub.stat().st_mtime
        for f in sub.rglob("*"):
            try: mtime = max(mtime, f.stat().st_mtime)
            except: pass
        out.append((sub.name, mtime))
    out.sort(key=lambda x: x[1], reverse=True)
    return [p[0] for p in out[:limit]], len(out)

def git_status():
    try:
        r = subprocess.run(['git', 'status', '--porcelain'], cwd=str(VAULT),
                           capture_output=True, text=True, timeout=3)
        if r.returncode == 0:
            changed = len([l for l in r.stdout.splitlines() if l.strip()])
            return 'clean' if not changed else f"{changed} pending"
    except:
        pass
    return None

def version():
    try: return (VAULT / "10-System" / "VERSION").read_text().strip()
    except: return "0.x"

def session_registry():
    registry = HOME / ".servetus_sessions.json"
    if not registry.exists():
        return []
    try:
        return json.loads(registry.read_text())
    except:
        return []

def last_closed_session(sessions):
    closed = [s for s in sessions
              if s.get("status") == "closed"
              and s.get("vault") == str(VAULT)
              and s.get("closed")]
    if not closed:
        return None
    return max(closed, key=lambda s: s["closed"])

def elapsed(ts_str):
    if not ts_str:
        return "?"
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        diff = (datetime.now(dt.tzinfo) if dt.tzinfo else now) - dt
        secs = int(diff.total_seconds())
    except:
        return "?"
    if secs < 60:      return f"{secs}s ago"
    if secs < 3600:    return f"{secs // 60}m ago"
    if secs < 86400:   return f"{secs // 3600}h {(secs % 3600) // 60}m ago"
    days = secs // 86400
    return f"{days}d ago"

def fmt_closed_ts(ts_str):
    if not ts_str: return ""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        dt = dt.astimezone() if dt.tzinfo else dt
        if dt.date() == now.date():
            return dt.strftime("today %H:%M")
        if (now.date() - dt.date()).days == 1:
            return dt.strftime("yesterday %H:%M")
        return dt.strftime("%b %d %H:%M")
    except:
        return ts_str[:16]

# ── Write session file ────────────────────────────────────────────────────────
CURRENT_STARTED = now.isoformat(timespec="seconds")

def write_session():
    room = os.environ.get("SERVETUS_ROOM", "")
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
    registry = HOME / ".servetus_sessions.json"
    try:
        sessions = json.loads(registry.read_text()) if registry.exists() else []
    except:
        sessions = []

    # Dedup: skip if this started timestamp is already registered
    if any(s.get("started") == CURRENT_STARTED for s in sessions):
        return

    # Auto-expire open sessions older than 7 days (never properly closed)
    cutoff = (now - timedelta(days=7)).isoformat(timespec="seconds")
    for s in sessions:
        if s.get("status") == "open" and s.get("started", "9999") < cutoff:
            s["status"] = "expired"

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

# ── Print brief ───────────────────────────────────────────────────────────────
def main():
    write_session()

    sess       = session_stats()
    arc_top, arc_total   = active_arcs(limit=3)
    proj_top, proj_total = projects(limit=4)
    reg        = session_registry()
    last       = last_closed_session(reg)
    git        = git_status()
    ver        = version()
    room       = os.environ.get("SERVETUS_ROOM", "")

    out = []

    # ── Header ───────────────────────────────────────────────────────────────
    out.append(top())
    room_suffix = f"  ·  {YELLOW}{room}{RESET}" if room else ""
    out.append(row(f"{BOLD}SERVETUS{RESET}  ·  v{ver}  ·  "
                   f"{now.strftime('%Y-%m-%d  %H:%M')}{room_suffix}"))
    vault_short = str(VAULT).replace(str(HOME), "~")
    out.append(row(f"{DIM}{vault_short}  ·  {MODEL}{RESET}"))

    # ── SESSION (context usage) ───────────────────────────────────────────────
    out.append(div())
    if sess and sess['total'] > 0:
        pct = sess['pct']
        bc  = GREEN if pct < 60 else (YELLOW if pct < 80 else RED)
        out.append(lrow("SESSION",
            f"{bc}{tbar(pct)}{RESET}  {pct}%  ·  "
            f"{fmtk(sess['total'])} used  ·  ↑{sess['user']} ↓{sess['asst']}"))
        if pct >= 80:
            out.append(lrow("", f"{RED}context {pct}% full — start a new session{RESET}"))
        elif pct >= 60:
            out.append(lrow("", f"{YELLOW}context filling — consider a new session{RESET}"))
    else:
        out.append(lrow("SESSION", f"{GREEN}fresh{RESET}"))

    # ── LAST CLOSED SESSION ───────────────────────────────────────────────────
    out.append(div())
    if last:
        room_s = last.get("room", "") or "—"
        closed = last.get("closed", "")
        ago    = elapsed(closed)
        when   = fmt_closed_ts(closed)
        line   = f"{ago}  ·  {when}  ·  {YELLOW}{room_s}{RESET}"
        turns  = last.get("turns", "")
        dur    = last.get("duration", "")
        detail = "  ·  ".join(x for x in [
            f"{turns} turns" if turns else "",
            dur if dur else "",
        ] if x)
        out.append(lrow("LAST", line))
        if detail:
            out.append(lrow("", f"{DIM}{detail}{RESET}"))
    else:
        out.append(lrow("LAST", f"{DIM}no prior closed sessions{RESET}"))

    # ── ARCS ──────────────────────────────────────────────────────────────────
    out.append(div())
    if arc_top:
        arc_str = "  ·  ".join(arc_top)
        suffix  = f"  ·  {DIM}+{arc_total - len(arc_top)} more{RESET}" \
                  if arc_total > len(arc_top) else ""
        out.append(lrow("ARCS", f"{GREEN}{arc_str}{RESET}{suffix}"))
    else:
        out.append(lrow("ARCS", f"{DIM}none active{RESET}"))

    # ── PROJECTS ──────────────────────────────────────────────────────────────
    out.append(div())
    if proj_top:
        proj_str = "  ·  ".join(proj_top)
        suffix   = f"  ·  {DIM}+{proj_total - len(proj_top)} more{RESET}" \
                   if proj_total > len(proj_top) else ""
        out.append(lrow("PROJECTS", f"{proj_str}{suffix}"))
    else:
        out.append(lrow("PROJECTS", f"{DIM}none{RESET}"))

    # ── FOOTER (git status, compact) ─────────────────────────────────────────
    if git is not None:
        out.append(div())
        gc = GREEN if git == 'clean' else YELLOW
        out.append(lrow("GIT", f"{gc}{git}{RESET}"))

    out.append(bot())
    print("\n".join(out))
    print()

    # ── Context plug-in line ──────────────────────────────────────────────────
    print(f"  {DIM}↳ vault context loaded  ·  {vault_short}{RESET}")
    print()


if __name__ == "__main__":
    main()
