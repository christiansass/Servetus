#!/usr/bin/env python3
"""
Servetus Session Status
-----------------------
Inbox-zero check for open/orphaned sessions.

Usage:
    python3 session-status.py          # count + summaries
    python3 session-status.py close    # archive all orphans, mark registry clean

Alias:
    svs          → python3 .../session-status.py
    svs close    → python3 .../session-status.py close
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR   = Path(__file__).resolve().parent
VAULT        = SCRIPT_DIR.parent
HOME         = Path.home()
REGISTRY     = HOME / ".servetus_sessions.json"
CLOSE_SCRIPT = SCRIPT_DIR / "session-close.py"
PROJECTS     = HOME / ".claude" / "projects"

# Sibling vault layout: Obsidian/Inbox/Claude/
CLAUDE_DIR = VAULT.parent / "Inbox" / "Claude"

BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
RESET  = "\033[0m"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def load_registry() -> list:
    if not REGISTRY.exists():
        return []
    try:
        return json.loads(REGISTRY.read_text())
    except Exception:
        return []


def open_registry_sessions(reg: list) -> list:
    return [s for s in reg if s.get("status") == "open"
            and s.get("vault") == str(VAULT)]


def mark_registry_closed(started_values) -> int:
    """Mark the given started timestamps as closed in the registry. Returns count updated."""
    if not started_values:
        return 0
    try:
        reg = json.loads(REGISTRY.read_text()) if REGISTRY.exists() else []
    except Exception:
        return 0
    now_str = datetime.now().astimezone().isoformat(timespec="seconds")
    count = 0
    for s in reg:
        if s.get("status") == "open" and s.get("started") in started_values:
            s["status"]    = "closed"
            s["closed"]    = now_str
            s["closed_by"] = "session-status close"
            count += 1
    try:
        REGISTRY.write_text(json.dumps(reg, indent=2))
    except Exception:
        pass
    return count


# ---------------------------------------------------------------------------
# JSONL scanning (live — does not rely on stale orphan-sessions.json)
# ---------------------------------------------------------------------------

def servetus_project_dir():
    slug = str(VAULT).replace("/", "-").replace("\\", "-")
    candidate = PROJECTS / slug
    if candidate.exists():
        return candidate
    # Fallback: partial match
    vault_parts = [p for p in VAULT.parts if p not in ("", "/")]
    for d in (PROJECTS.iterdir() if PROJECTS.exists() else []):
        if d.is_dir() and all(p in d.name for p in vault_parts[-2:]):
            return d
    return None


def is_real_session(path: Path) -> bool:
    """True if the JSONL contains at least one non-empty assistant text response."""
    try:
        for line in path.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("type") != "assistant":
                continue
            for block in obj.get("message", {}).get("content", []):
                if isinstance(block, dict) and block.get("type") == "text":
                    if block.get("text", "").strip():
                        return True
    except Exception:
        pass
    return False


def artifact_exists(path: Path) -> bool:
    short_id = path.stem[:8]
    if not CLAUDE_DIR.exists():
        return False
    for item in CLAUDE_DIR.iterdir():
        if short_id in item.name:
            return True
    return False


def find_orphan_jsonls():
    """Live scan: real sessions with no artifact, excluding subagents."""
    project_dir = servetus_project_dir()
    if not project_dir:
        return []
    orphans = []
    for jsonl in sorted(project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime):
        if "subagent" in jsonl.name:
            continue
        if artifact_exists(jsonl):
            continue
        if not is_real_session(jsonl):
            continue
        orphans.append(jsonl)
    return orphans


# ---------------------------------------------------------------------------
# Summary extraction (no LLM — mechanical only)
# ---------------------------------------------------------------------------

_SYSTEM_NOISE = re.compile(
    r"^(<[a-z]|---|#\s|You have access|Your task|IMPORTANT|The following|"
    r"As you answer|When working|This is the|gitStatus)",
    re.I,
)


def extract_summary(jsonl_path: Path) -> dict:
    """Pull first real topic, files touched, turn count, and timestamps from a JSONL."""
    user_msgs   = []
    files       = []
    turn_count  = 0
    first_ts    = last_ts = None

    try:
        for line in jsonl_path.read_text(errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue

            ts = obj.get("timestamp")
            if ts:
                if not first_ts:
                    first_ts = ts
                last_ts = ts

            t = obj.get("type", "")

            if t == "user":
                msg     = obj.get("message", {})
                content = msg.get("content", "") if isinstance(msg, dict) else msg
                text    = ""
                if isinstance(content, str):
                    text = content.strip()
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text += block.get("text", "")
                text = text.strip()
                # Keep only short, human-looking messages
                if text and 10 < len(text) < 1500 and not _SYSTEM_NOISE.match(text):
                    user_msgs.append(text)
                turn_count += 1

            elif t == "assistant":
                msg = obj.get("message", {})
                if not isinstance(msg, dict):
                    continue
                for block in msg.get("content", []):
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        name = block.get("name", "")
                        inp  = block.get("input", {})
                        if name in ("Edit", "Write", "NotebookEdit"):
                            fp = inp.get("file_path", inp.get("notebook_path", ""))
                            if fp:
                                files.append(Path(fp).name)

    except Exception:
        pass

    # First non-trivial user message = topic signal
    topic = ""
    for m in user_msgs[:4]:
        if len(m) > 25:
            topic = m[:200].replace("\n", " ")
            break
    if not topic and user_msgs:
        topic = user_msgs[0][:200].replace("\n", " ")

    # Dedup files, keep up to 5
    seen = set()
    deduped = []
    for f in files:
        if f not in seen:
            seen.add(f)
            deduped.append(f)
        if len(deduped) == 5:
            break

    return {
        "topic":    topic,
        "files":    deduped,
        "turns":    turn_count,
        "first_ts": first_ts,
        "last_ts":  last_ts,
    }


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def fmt_ts(ts_str: str) -> str:
    if not ts_str:
        return "?"
    try:
        dt  = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).astimezone()
        now = datetime.now().astimezone()
        if dt.date() == now.date():
            return dt.strftime("today %H:%M")
        if (now.date() - dt.date()).days == 1:
            return dt.strftime("yesterday %H:%M")
        return dt.strftime("%b %d %H:%M")
    except Exception:
        return ts_str[:16]


def fmt_elapsed(ts_str: str) -> str:
    if not ts_str:
        return ""
    try:
        dt   = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now  = datetime.now(dt.tzinfo)
        diff = int((now - dt).total_seconds())
    except Exception:
        return ""
    if diff < 3600:
        return f"{diff // 60}m ago"
    if diff < 86400:
        return f"{diff // 3600}h ago"
    return f"{diff // 86400}d ago"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Natural-language routing: if any argument contains a close/exit intent word,
    # run in close mode. Word order doesn't matter. Covers:
    #   sessions close / close sessions / sessions exit / exit all / sessions done / etc.
    _CLOSE_WORDS = {"close", "exit", "shut", "done", "finish", "end", "all", "clear", "zero"}
    args_lower   = " ".join(sys.argv[1:]).lower().split()
    close_mode   = any(w in _CLOSE_WORDS for w in args_lower)

    reg          = load_registry()
    open_reg     = open_registry_sessions(reg)
    orphan_paths = find_orphan_jsonls()

    total = max(len(open_reg), len(orphan_paths))  # overlap likely; show the larger signal

    # ── All clear ────────────────────────────────────────────────────────────
    if not open_reg and not orphan_paths:
        print(f"{GREEN}{BOLD}Sessions: all clear ✓{RESET}")
        return

    # ── Header count ────────────────────────────────────────────────────────
    parts = []
    if orphan_paths:
        parts.append(f"{len(orphan_paths)} unarchived")
    if open_reg:
        parts.append(f"{len(open_reg)} open in registry")
    print(f"{BOLD}Sessions:{RESET}  {YELLOW}{',  '.join(parts)}{RESET}\n")

    # ── Per-session summaries (from live JSONL scan) ─────────────────────────
    if orphan_paths:
        for path in orphan_paths:
            try:
                mtime    = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
                date_str = mtime.strftime("%Y-%m-%d")
                elapsed  = fmt_elapsed(mtime.isoformat())
            except Exception:
                date_str = "?"
                elapsed  = ""

            s = extract_summary(path)

            header = f"  {YELLOW}●{RESET}  {BOLD}{date_str}{RESET}"
            if elapsed:
                header += f"  {DIM}({elapsed}){RESET}"
            print(header)

            if s["topic"]:
                topic = s["topic"]
                if len(topic) > 130:
                    topic = topic[:127] + "..."
                print(f'      {DIM}"{topic}"{RESET}')

            if s["files"]:
                print(f"      Files: {', '.join(s['files'])}")

            ts_range = ""
            if s["first_ts"] and s["last_ts"]:
                ts_range = f"  ·  {fmt_ts(s['first_ts'])} → {fmt_ts(s['last_ts'])}"
            if s["turns"]:
                print(f"      {s['turns']} turns{ts_range}")

            print()

    # ── Registry-only opens (no JSONL found — likely launch-only ghosts) ─────
    orphan_stems = {p.stem[:8] for p in orphan_paths}
    ghost_reg = [s for s in open_reg
                 if not any(s.get("started", "") in str(p) for p in orphan_paths)]
    if ghost_reg:
        print(f"  {DIM}Registry ghosts (launched but no real JSONL content):{RESET}")
        for s in ghost_reg:
            room    = s.get("room") or "—"
            started = fmt_ts(s.get("started", ""))
            elapsed = fmt_elapsed(s.get("started", ""))
            print(f"    {DIM}○  [{room}]  started {started}  ({elapsed}){RESET}")
        print()

    # ── Close all ────────────────────────────────────────────────────────────
    if close_mode:
        print(f"{BOLD}Archiving...{RESET}\n")
        archived = 0
        skipped  = 0

        for path in orphan_paths:
            result = subprocess.run(
                [sys.executable, str(CLOSE_SCRIPT), str(path)],
                capture_output=True, text=True,
            )
            name = path.name
            if result.returncode == 0:
                # Check if session-close actually wrote something or skipped
                if "Skipping" in result.stdout or "empty" in result.stdout.lower():
                    print(f"  {DIM}○  {name}  (launch-only, skipped){RESET}")
                    skipped += 1
                else:
                    print(f"  {GREEN}✓{RESET}  {name}")
                    archived += 1
            else:
                print(f"  {RED}✗{RESET}  {name}")
                if result.stderr.strip():
                    print(f"      {DIM}{result.stderr.strip()[:120]}{RESET}")

        # Mark remaining open registry entries closed
        started_vals = [s.get("started", "") for s in open_reg]
        n_closed = mark_registry_closed(started_vals)

        print()
        note = f"{archived} archived"
        if skipped:
            note += f"  ·  {skipped} skipped (launch-only)"
        if n_closed:
            note += f"  ·  {n_closed} registry entries closed"
        print(f"{GREEN}{BOLD}Done.{RESET}  {note}")
        print(f"\n{GREEN}{BOLD}Sessions: all clear ✓{RESET}")

    else:
        print(f"  Run {BOLD}svs close{RESET} to archive all and return to zero.")


if __name__ == "__main__":
    main()
