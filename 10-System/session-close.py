#!/usr/bin/env python3
"""
Servetus Session Close
----------------------
Converts the most recent Claude Code session (.jsonl) for the Servetus vault
into a full-fidelity artifact package and drops it into the Hopper (Inbox/Claude/).

One folder per session — everything co-located:
  Inbox/Claude/<date>-claude-session-<id>/
      <date>-claude-session-<id>.md   (human-readable artifact)
      <id>-img-001.png                (pasted images, if any)
      <session-id>.jsonl              (raw tape / ground truth witness)

Hopper is a transit zone. Empty = healthy. Once memories are extracted the
whole folder moves to 00-Artifacts/YYYY/ — the move is the completion signal.

Only captures sessions from the Servetus project directory in ~/.claude/projects/.

Usage:
    python3 session-close.py                      # auto-detects most recent Servetus session
    python3 session-close.py <path/to/file.jsonl> # explicit file
"""

import os
import sys
import json
import uuid
import shutil
import socket
import platform
from datetime import datetime, timezone
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = VAULT_ROOT / "config"


def local_timezone_name() -> str:
    """Return the system's IANA timezone name (e.g. America/Chicago)."""
    try:
        import os as _os
        lt = _os.readlink("/etc/localtime")
        if "zoneinfo/" in lt:
            return lt.split("zoneinfo/", 1)[1]
    except Exception:
        pass
    try:
        import subprocess
        result = subprocess.check_output(
            ["timedatectl", "show", "--property=Timezone", "--value"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        if result:
            return result
    except Exception:
        pass
    dt = datetime.now().astimezone()
    return dt.strftime("UTC%z")


LOCAL_TZ = local_timezone_name()

# Session artifacts land in the sibling Inbox vault (multi-vault Obsidian layout):
#   Obsidian/
#   ├── Servetus/   ← this vault
#   └── Inbox/
#       └── Claude/ ← artifacts land here
_sibling_claude = VAULT_ROOT.parent / "Inbox" / "Claude"

if _sibling_claude.parent.exists():
    CLAUDE_DIR = _sibling_claude
else:
    print(
        f"[session-close] Error: sibling Inbox vault not found at "
        f"{_sibling_claude.parent}\n"
        f"Expected layout: Obsidian/Inbox/Claude/ alongside Obsidian/Servetus/\n"
        f"Create the folder or run the installer to set it up."
    )
    sys.exit(1)



# ---------------------------------------------------------------------------
# Origin fingerprint
# ---------------------------------------------------------------------------

def get_os() -> str:
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
    machine = socket.gethostname()
    overrides = CONFIG_DIR / "overrides.md"
    if overrides.exists():
        for line in overrides.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("machine_name:"):
                val = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                if val:
                    machine = val
                break

    mac_int = uuid.getnode()
    mac = ":".join(["{:02x}".format((mac_int >> (8 * i)) & 0xff)
                    for i in reversed(range(6))])

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "unknown"

    return {"machine": machine, "mac": mac, "ip": ip, "os": get_os()}


# ---------------------------------------------------------------------------
# Find most recent .jsonl session
# ---------------------------------------------------------------------------

def find_servetus_project_dir() -> Path:
    home = Path.home()
    projects = home / ".claude" / "projects"
    if not projects.exists():
        raise FileNotFoundError(f"Claude Code projects directory not found: {projects}")

    slug = str(VAULT_ROOT).replace("/", "-").replace("\\", "-")
    project_dir = projects / slug

    if project_dir.exists():
        return project_dir

    vault_parts = [p for p in VAULT_ROOT.parts if p not in ("", "/")]
    for d in projects.iterdir():
        if d.is_dir() and all(p in d.name for p in vault_parts[-2:]):
            return d

    raise FileNotFoundError(
        f"Could not find Claude Code project directory for vault: {VAULT_ROOT}\n"
        f"Expected: {project_dir}\n"
        f"Launch Claude Code from within the vault using 'sc'."
    )


def find_most_recent_jsonl() -> Path:
    import getpass
    home = Path.home()
    projects = home / ".claude" / "projects"

    candidate_dirs = []

    try:
        candidate_dirs.append(find_servetus_project_dir())
    except FileNotFoundError:
        pass

    default_dir = projects / f"-Users-{getpass.getuser()}"
    if default_dir.exists() and default_dir not in candidate_dirs:
        candidate_dirs.append(default_dir)

    candidates = [
        p for d in candidate_dirs
        for p in d.glob("*.jsonl")
        if p.stat().st_size > 10_000
    ]

    if not candidates:
        raise FileNotFoundError(
            f"No session files found in: {[str(d) for d in candidate_dirs]}\n"
            f"Launch Claude Code from the Servetus vault using 'sc'."
        )

    return max(candidates, key=lambda p: p.stat().st_mtime)


# ---------------------------------------------------------------------------
# Parse .jsonl
# ---------------------------------------------------------------------------

def parse_jsonl(path: Path) -> list:
    turns = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                turns.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return turns


# ---------------------------------------------------------------------------
# Timestamp formatting
# ---------------------------------------------------------------------------

def parse_ts(ts_str: str):
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).astimezone()
    except Exception:
        return None


def format_ts(ts_str: str) -> str:
    dt = parse_ts(ts_str)
    if not dt:
        return ts_str or ""
    ms = dt.strftime("%f")[:3]
    return dt.strftime(f"%Y-%m-%d %H:%M:%S.{ms} %Z")


def fmt_ms(ms: int) -> str:
    """Format milliseconds as human-readable duration."""
    if ms < 1000:
        return f"{ms}ms"
    s = ms / 1000
    if s < 60:
        return f"{s:.1f}s"
    m, s = divmod(int(s), 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"


# ---------------------------------------------------------------------------
# Full context extraction
# ---------------------------------------------------------------------------

def summarize_tool_input(name: str, inp: dict) -> str:
    """Return a one-line summary of a tool call's input."""
    if not inp:
        return ""
    if name in ("Read", "Edit", "Write", "NotebookEdit"):
        return inp.get("file_path", inp.get("notebook_path", ""))
    if name == "Bash":
        cmd = inp.get("command", "")
        return cmd[:120] + ("…" if len(cmd) > 120 else "")
    if name == "Glob":
        return f"{inp.get('pattern', '')} in {inp.get('path', '.')}"
    if name == "Grep":
        return f"`{inp.get('pattern', '')}` in {inp.get('path', '.')}"
    if name in ("WebFetch", "WebSearch"):
        return inp.get("url", inp.get("query", ""))
    if name == "Agent":
        return inp.get("description", inp.get("prompt", "")[:80])
    # Generic: first string value
    for v in inp.values():
        if isinstance(v, str):
            return v[:120]
    return json.dumps(inp)[:120]


def extract_full_context(turns: list) -> dict:
    """Extract all structured context from the raw JSONL turns."""
    session_meta = {}
    cwd_timeline  = []   # {timestamp, cwd, branch}
    tool_log      = []   # {timestamp, name, input_summary, uuid}
    turn_durations = []  # {timestamp, duration_ms}
    token_totals  = {"input": 0, "output": 0, "cache_read": 0, "cache_created": 0}
    image_count   = 0
    images        = []   # {index, media_type, data, source_type, url}
    messages      = []   # structured conversation turns

    last_cwd    = None
    last_branch = None

    for turn in turns:
        t_type  = turn.get("type", "")
        ts      = turn.get("timestamp", "")
        cwd     = turn.get("cwd", "")
        branch  = turn.get("gitBranch", "")

        # Harvest session-level metadata from any turn that carries it
        for key in ("sessionId", "slug", "version"):
            if turn.get(key):
                session_meta[key] = turn[key]

        # CWD / branch change tracking
        if cwd and (cwd != last_cwd or branch != last_branch):
            cwd_timeline.append({"timestamp": ts, "cwd": cwd, "branch": branch})
            last_cwd    = cwd
            last_branch = branch

        # --- system: turn duration ---
        if t_type == "system" and turn.get("subtype") == "turn_duration":
            turn_durations.append({
                "timestamp": ts,
                "duration_ms": turn.get("durationMs", 0),
            })

        # --- user turn ---
        elif t_type in ("user", "human"):
            msg     = turn.get("message", {})
            content = msg.get("content", "") if isinstance(msg, dict) else msg
            perm    = turn.get("permissionMode", "")
            if perm:
                session_meta["permissionMode"] = perm

            text_parts   = []
            tool_results = []

            if isinstance(content, str):
                text_parts.append(content)
            elif isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type", "")
                    if btype == "text":
                        text_parts.append(block.get("text", ""))
                    elif btype == "image":
                        image_count += 1
                        src = block.get("source", {})
                        images.append({
                            "index":       image_count,
                            "media_type":  src.get("media_type", "image/png"),
                            "data":        src.get("data", ""),
                            "url":         src.get("url", ""),
                            "source_type": src.get("type", "base64"),
                        })
                        text_parts.append(f"__IMAGE_{image_count}__")
                    elif btype == "tool_result":
                        res_content = block.get("content", "")
                        if isinstance(res_content, list):
                            res_text = "\n".join(
                                b.get("text", "") for b in res_content
                                if isinstance(b, dict) and b.get("type") == "text"
                            )
                        else:
                            res_text = str(res_content) if res_content else ""
                        tool_results.append({
                            "tool_use_id": block.get("tool_use_id", ""),
                            "result_preview": res_text[:300] + ("…" if len(res_text) > 300 else ""),
                        })

            text = "\n".join(text_parts).strip()
            if text or tool_results:
                messages.append({
                    "role":         "user",
                    "timestamp":    ts,
                    "uuid":         turn.get("uuid", ""),
                    "cwd":          cwd,
                    "branch":       branch,
                    "content":      text,
                    "tool_results": tool_results,
                    "perm":         perm,
                })

        # --- assistant turn ---
        elif t_type == "assistant":
            msg     = turn.get("message", {}) if isinstance(turn.get("message"), dict) else {}
            content = msg.get("content", [])
            usage   = msg.get("usage", {})
            model   = msg.get("model", "")
            if model:
                session_meta["model"] = model

            # Accumulate token usage
            token_totals["input"]         += usage.get("input_tokens", 0)
            token_totals["output"]        += usage.get("output_tokens", 0)
            token_totals["cache_read"]    += usage.get("cache_read_input_tokens", 0)
            token_totals["cache_created"] += usage.get("cache_creation_input_tokens", 0)

            text_parts = []
            tool_calls = []

            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type", "")
                    if btype == "text":
                        text_parts.append(block.get("text", ""))
                    elif btype == "tool_use":
                        name = block.get("name", "")
                        inp  = block.get("input", {})
                        entry = {
                            "id":            block.get("id", ""),
                            "name":          name,
                            "input":         inp,
                            "input_summary": summarize_tool_input(name, inp),
                        }
                        tool_calls.append(entry)
                        tool_log.append({
                            "timestamp":     ts,
                            "name":          name,
                            "input_summary": entry["input_summary"],
                            "id":            entry["id"],
                        })

            text = "\n".join(text_parts).strip()
            if text or tool_calls:
                messages.append({
                    "role":       "assistant",
                    "timestamp":  ts,
                    "uuid":       turn.get("uuid", ""),
                    "cwd":        cwd,
                    "branch":     branch,
                    "content":    text,
                    "tool_calls": tool_calls,
                    "usage":      usage,
                })

    return {
        "session_meta":  session_meta,
        "cwd_timeline":  cwd_timeline,
        "tool_log":      tool_log,
        "turn_durations": turn_durations,
        "token_totals":  token_totals,
        "image_count":   image_count,
        "images":        images,
        "messages":      messages,
    }


# ---------------------------------------------------------------------------
# Build artifact markdown
# ---------------------------------------------------------------------------

_MEDIA_EXT = {
    "image/png":  ".png",
    "image/jpeg": ".jpg",
    "image/jpg":  ".jpg",
    "image/gif":  ".gif",
    "image/webp": ".webp",
}


def image_filename(short_id: str, img: dict) -> str:
    """Stable, session-scoped filename for a pasted image.

    Pattern: {short_id}-img-{n:03d}{ext}
    The session short_id is embedded so the image traces back to its artifact
    even if the file is ever separated from its folder.
    """
    ext = _MEDIA_EXT.get(img["media_type"], ".png")
    return f"{short_id}-img-{img['index']:03d}{ext}"


def build_artifact(jsonl_path: Path, ctx: dict, origin: dict, witness_path: Path) -> tuple:
    """Returns (filename, markdown_content, image_files).

    image_files is a list of (relative_path_str, bytes) — caller writes them
    into a subfolder named after the session slug.
    """
    meta     = ctx["session_meta"]
    messages = ctx["messages"]

    # Session timing: prefer first/last message timestamps
    all_ts = [m["timestamp"] for m in messages if m.get("timestamp")]
    if all_ts:
        created  = parse_ts(all_ts[0])
        modified = parse_ts(all_ts[-1])
    else:
        stat     = jsonl_path.stat()
        created  = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).astimezone()
        modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).astimezone()

    date_str     = created.strftime("%Y-%m-%d")
    datetime_str = created.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + created.strftime("%z")
    closed_str   = modified.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + modified.strftime("%z")
    short_id     = jsonl_path.stem[:8]
    file_slug    = f"{date_str}-claude-session-{short_id}"
    room         = os.environ.get("SERVETUS_ROOM", "")
    title        = f"Claude Code Session — {created.strftime('%B %d, %Y')}"

    duration_secs = int((modified - created).total_seconds())
    duration_str  = fmt_ms(duration_secs * 1000)

    user_turns      = sum(1 for m in messages if m["role"] == "user")
    assistant_turns = sum(1 for m in messages if m["role"] == "assistant")
    total_tools     = len(ctx["tool_log"])
    tok             = ctx["token_totals"]

    # Build tool call index: id -> name+summary (for pairing with tool_results)
    tool_index = {t["id"]: t for t in ctx["tool_log"]}

    # ---- Frontmatter ----
    frontmatter = f"""---
type: artifact
title: "{title}"
slug: "{file_slug}"
session-name: "{meta.get('slug', '')}"
session-id: "{meta.get('sessionId', jsonl_path.stem)}"
session-room: "{room}"

date: {datetime_str}
closed: {closed_str}
duration: "{duration_str}"
timezone: "{LOCAL_TZ}"

model: "{meta.get('model', '')}"
claude-version: "{meta.get('version', '')}"
permission-mode: "{meta.get('permissionMode', '')}"

origin:
  machine: "{origin['machine']}"
  mac: "{origin['mac']}"
  ip: "{origin['ip']}"
  os: "{origin['os']}"

source:
  jsonl: "{jsonl_path.name}"
  jsonl-path: "{jsonl_path}"
  witness: "{witness_path}"

stats:
  turns-user: {user_turns}
  turns-assistant: {assistant_turns}
  tool-calls: {total_tools}
  images: {ctx['image_count']}
  tokens-input: {tok['input']}
  tokens-output: {tok['output']}
  tokens-cache-read: {tok['cache_read']}
  tokens-cache-created: {tok['cache_created']}

circles: []
published: false
tags: [artifact, session, claude-code]
---"""

    lines = [f"# {title}\n"]

    # ---- Session Header ----
    lines.append("## Session Info\n")
    lines.append(f"| | |")
    lines.append(f"|---|---|")
    lines.append(f"| **Name** | `{meta.get('slug', '—')}` |")
    lines.append(f"| **Session ID** | `{meta.get('sessionId', jsonl_path.stem)}` |")
    lines.append(f"| **Model** | {meta.get('model', '—')} |")
    lines.append(f"| **Claude Code** | v{meta.get('version', '—')} |")
    lines.append(f"| **Permission mode** | {meta.get('permissionMode', '—')} |")
    lines.append(f"| **Opened** | `{format_ts(all_ts[0]) if all_ts else '—'}` |")
    lines.append(f"| **Closed** | `{format_ts(all_ts[-1]) if all_ts else '—'}` |")
    lines.append(f"| **Duration** | {duration_str} |")
    lines.append(f"| **Turns** | {user_turns} user / {assistant_turns} assistant |")
    lines.append(f"| **Tool calls** | {total_tools} |")
    lines.append(f"| **Images** | {ctx['image_count']} |")
    lines.append(f"| **Machine** | {origin['machine']} / {origin['os']} |")
    lines.append(f"| **Witness** | `{witness_path.name}` |\n")

    # ---- Token Usage ----
    lines.append("## Token Usage\n")
    lines.append(f"| | Tokens |")
    lines.append(f"|---|---|")
    lines.append(f"| Input | {tok['input']:,} |")
    lines.append(f"| Output | {tok['output']:,} |")
    lines.append(f"| Cache read | {tok['cache_read']:,} |")
    lines.append(f"| Cache created | {tok['cache_created']:,} |")
    lines.append(f"| **Total** | **{sum(tok.values()):,}** |\n")

    # ---- CWD / Branch Timeline ----
    if ctx["cwd_timeline"]:
        lines.append("## Working Directory Timeline\n")
        lines.append("| Time | CWD | Branch |")
        lines.append("|---|---|---|")
        for entry in ctx["cwd_timeline"]:
            lines.append(
                f"| `{format_ts(entry['timestamp'])}` "
                f"| `{entry['cwd']}` "
                f"| `{entry['branch']}` |"
            )
        lines.append("")

    # ---- Tool Activity Log ----
    if ctx["tool_log"]:
        lines.append("## Tool Activity\n")
        lines.append("| Time | Tool | Input |")
        lines.append("|---|---|---|")
        for entry in ctx["tool_log"]:
            summary = entry["input_summary"].replace("|", "\\|")
            lines.append(
                f"| `{format_ts(entry['timestamp'])}` "
                f"| **{entry['name']}** "
                f"| `{summary}` |"
            )
        lines.append("")

    # ---- Turn Durations ----
    if ctx["turn_durations"]:
        lines.append("## Turn Durations\n")
        lines.append("| Time | Duration |")
        lines.append("|---|---|")
        for entry in ctx["turn_durations"]:
            lines.append(
                f"| `{format_ts(entry['timestamp'])}` "
                f"| {fmt_ms(entry['duration_ms'])} |"
            )
        lines.append("")

    # ---- Transcript ----
    lines.append("---\n")
    lines.append("## Transcript\n")

    for msg in messages:
        role_label = "**User**" if msg["role"] == "user" else "**Servetus**"
        ts         = format_ts(msg.get("timestamp", ""))
        ts_suffix  = f" `{ts}`" if ts else ""
        meta_parts = []
        if msg.get("cwd"):
            meta_parts.append(f"`{msg['cwd']}`")
        if msg.get("branch"):
            meta_parts.append(f"branch: `{msg['branch']}`")
        meta_line  = " · ".join(meta_parts)

        lines.append(f"### {role_label}{ts_suffix}")
        if meta_line:
            lines.append(f"*{meta_line}*\n")

        # Tool calls (assistant)
        for tc in msg.get("tool_calls", []):
            summary = tc["input_summary"].replace("`", "'")
            lines.append(f"> **{tc['name']}** → `{summary}`")
        if msg.get("tool_calls"):
            lines.append("")

        # Tool results (user — paired back to tool calls)
        for tr in msg.get("tool_results", []):
            tool_name = tool_index.get(tr["tool_use_id"], {}).get("name", "tool")
            preview   = tr["result_preview"].replace("\n", " ").strip()
            lines.append(f"> ↩ **{tool_name}** result: {preview}")
        if msg.get("tool_results"):
            lines.append("")

        if msg["content"]:
            lines.append(msg["content"])

        lines.append("\n---\n")

    # ---- Resolve image placeholders in transcript ----
    # Replace __IMAGE_N__ with markdown image refs pointing to the session subfolder.
    # The session short_id is embedded in every filename so images trace back to
    # this artifact even if separated from their folder.
    import base64 as _b64
    image_files = []  # (relative_filename, raw_bytes)
    body = "\n".join(lines)

    for img in ctx.get("images", []):
        fname = image_filename(short_id, img)
        md_ref = f"![{fname}]({fname})"
        body = body.replace(f"__IMAGE_{img['index']}__", md_ref)

        # Images are in the same folder as the .md — just fname, no subfolder prefix
        if img["source_type"] == "base64" and img["data"]:
            try:
                raw = _b64.b64decode(img["data"])
                image_files.append((fname, raw))
            except Exception:
                pass
        # URL-sourced images: reference only, no local copy

    content = frontmatter + "\n\n" + body
    return f"{file_slug}.md", content, image_files


# ---------------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------------

def write_session_package(filename: str, content: str, jsonl_path: Path,
                          image_files: list) -> Path:
    """Write all session artifacts into one folder in the Hopper (Inbox/Claude/).

    Everything lands together:
        Inbox/Claude/<file_slug>/
            <file_slug>.md
            <session-id>.jsonl   ← raw tape / witness
            <short_id>-img-NNN.* ← pasted images
    """
    stem = filename.rsplit(".", 1)[0]   # file_slug
    session_dir = CLAUDE_DIR / stem
    session_dir.mkdir(parents=True, exist_ok=True)

    # Markdown
    md_path = session_dir / filename
    if md_path.exists():
        print(f"[session-close] Already exists: {md_path}")
    else:
        md_path.write_text(content, encoding="utf-8")

    # JSONL witness — raw tape, co-located with artifact
    jsonl_dest = session_dir / jsonl_path.name
    if not jsonl_dest.exists():
        shutil.copy2(jsonl_path, jsonl_dest)
        print(f"[session-close] Witness:  {jsonl_dest}")
    else:
        print(f"[session-close] Witness already exists: {jsonl_dest}")

    # Images
    for img_fname, img_bytes in image_files:
        img_path = session_dir / img_fname
        if not img_path.exists():
            img_path.write_bytes(img_bytes)
            print(f"[session-close] Image:    {img_path}")
        else:
            print(f"[session-close] Image already exists: {img_path}")

    return md_path


# ---------------------------------------------------------------------------
# Orphan scanner — find JSONLs with real content but no artifact
# ---------------------------------------------------------------------------

ORPHAN_FILE = VAULT_ROOT / "10-System" / "orphan-sessions.json"


def is_real_session(jsonl_path: Path) -> bool:
    """Return True if the JSONL contains at least one assistant text response.
    An empty session is: file-history-snapshot + caveat + /exit + goodbye = 4 lines.
    Anything with an actual assistant reply is real and deserves an artifact."""
    try:
        for line in jsonl_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("type") != "assistant":
                continue
            msg = obj.get("message", {})
            if not isinstance(msg, dict):
                continue
            for block in msg.get("content", []):
                if isinstance(block, dict) and block.get("type") == "text":
                    if block.get("text", "").strip():
                        return True
    except Exception:
        pass
    return False


def artifact_exists(jsonl_path: Path) -> bool:
    """Return True if an artifact folder already exists for this session."""
    short_id = jsonl_path.stem[:8]
    for item in CLAUDE_DIR.iterdir() if CLAUDE_DIR.exists() else []:
        if short_id in item.name:
            return True
    return False


def scan_orphans(current_jsonl: Path) -> list:
    """Scan project dir for real sessions without artifacts. Exclude current session."""
    try:
        project_dir = find_servetus_project_dir()
    except FileNotFoundError:
        return []

    orphans = []
    for jsonl in sorted(project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime):
        if jsonl == current_jsonl:
            continue
        if "subagent" in jsonl.name:
            continue
        if artifact_exists(jsonl):
            continue
        if not is_real_session(jsonl):
            continue
        try:
            mtime = datetime.fromtimestamp(jsonl.stat().st_mtime).astimezone()
            orphans.append({
                "jsonl": str(jsonl),
                "short_id": jsonl.stem[:8],
                "mtime": mtime.isoformat(timespec="seconds"),
                "date": mtime.strftime("%Y-%m-%d"),
            })
        except Exception:
            pass
    return orphans


def write_orphan_report(orphans: list):
    """Write orphan list to 10-System/orphan-sessions.json for launch-brief to surface."""
    try:
        ORPHAN_FILE.write_text(json.dumps(orphans, indent=2))
        if orphans:
            print(f"[session-close] Orphans:  {len(orphans)} unarchived session(s) flagged → {ORPHAN_FILE.name}")
    except Exception as e:
        print(f"[session-close] Orphan scan: could not write report ({e})")


# ---------------------------------------------------------------------------
# Session registry — mark session closed
# ---------------------------------------------------------------------------

def close_session_in_registry(vault: str, started_ts: str, session_id: str, room: str,
                              summary: dict = None):
    """Find the most recent open entry for this vault and mark it closed."""
    registry_path = Path.home() / ".servetus_sessions.json"
    try:
        sessions = json.loads(registry_path.read_text()) if registry_path.exists() else []
    except Exception:
        return

    now_str = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    # Find the most recent open entry for this vault (match by vault path)
    target_idx = None
    for i in range(len(sessions) - 1, -1, -1):
        s = sessions[i]
        if s.get("status") == "open" and s.get("vault", "") == vault:
            target_idx = i
            break

    if target_idx is not None:
        sessions[target_idx]["status"]     = "closed"
        sessions[target_idx]["closed"]     = now_str
        sessions[target_idx]["session_id"] = session_id
        if room and not sessions[target_idx].get("room"):
            sessions[target_idx]["room"] = room
        if summary:
            sessions[target_idx].update(summary)
    else:
        # No open entry found — append a closed record so history is preserved
        entry = {
            "room":       room,
            "started":    started_ts,
            "machine":    socket.gethostname(),
            "vault":      vault,
            "status":     "closed",
            "session_id": session_id,
            "closed":     now_str,
        }
        if summary:
            entry.update(summary)
        sessions.append(entry)

    try:
        registry_path.write_text(json.dumps(sessions, indent=2))
        print(f"[session-close] Registry: session marked closed")
    except Exception as e:
        print(f"[session-close] Registry: could not update ({e})")


# ---------------------------------------------------------------------------
# Session Brief (LLM context injection at next open)
# ---------------------------------------------------------------------------

def write_session_brief(ctx: dict, duration_secs: float, room: str,
                        files_touched: list, brief_path: Path) -> None:
    """Write 10-System/last-session-brief.md for LLM context at next session open.

    Structural extraction only — no LLM API call. Pulls closing exchange verbatim
    plus mechanical metadata. Overwritten each session; always reflects most recent close.
    """
    now = datetime.now().astimezone()
    closed_str = now.strftime("%Y-%m-%dT%H:%M:%S%z")
    closed_human = now.strftime("%Y-%m-%d %H:%M")

    session_id = ctx["session_meta"].get("sessionId", "")[:8]
    turns = sum(1 for m in ctx["messages"] if m["role"] == "user")
    dur = fmt_ms(duration_secs * 1000)

    # Pull last 3 user turns + last assistant response
    user_turns = [m for m in ctx["messages"] if m["role"] == "user"]
    asst_turns = [m for m in ctx["messages"] if m["role"] == "assistant"]
    last_user_msgs = user_turns[-3:] if len(user_turns) >= 3 else user_turns
    last_asst = asst_turns[-1] if asst_turns else None

    # Closing exchange
    exchange_lines = []
    for msg in last_user_msgs:
        text = msg.get("content", "")
        if isinstance(text, list):
            text = " ".join(b.get("text", "") for b in text if b.get("type") == "text")
        exchange_lines.append(f"**You:** {text.strip()[:400]}")
    if last_asst:
        content = last_asst.get("content", "")
        if isinstance(content, list):
            content = " ".join(b.get("text", "") for b in content if b.get("type") == "text")
        exchange_lines.append(f"\n**Servetus:** {content.strip()[:600]}")

    # Tool summary
    tool_log = ctx.get("tool_log", [])
    tool_counts: dict = {}
    for t in tool_log:
        name = t.get("name", "unknown")
        tool_counts[name] = tool_counts.get(name, 0) + 1
    tool_summary = "  ".join(
        f"{v}× {k}" for k, v in sorted(tool_counts.items(), key=lambda x: -x[1])
    )

    files_section = "\n".join(f"- {f}" for f in files_touched) if files_touched else "- (none recorded)"

    fm_lines = [
        "---",
        f"session_id: {session_id}",
        f'closed_at: "{closed_str}"',
        f'room: "{room or "unset"}"',
        f'duration: "{dur}"',
        f"turns: {turns}",
        "---",
    ]
    body_lines = [
        "",
        "# Last Session Brief",
        "",
        f"**Room:** {room or 'unset'}  ",
        f"**Closed:** {closed_human}  ·  {dur}  ·  {turns} turns",
        "",
        "## Closing Exchange",
        "",
        "\n\n".join(exchange_lines),
        "",
        "## Files Touched",
        "",
        files_section,
        "",
        "## Tool Activity",
        "",
        tool_summary or "(none)",
        "",
    ]

    brief_path.write_text("\n".join(fm_lines + body_lines), encoding="utf-8")
    print(f"[session-close] Brief:    {brief_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) > 1:
        jsonl_path = Path(sys.argv[1])
        if not jsonl_path.exists():
            print(f"Error: file not found: {jsonl_path}")
            sys.exit(1)
    else:
        try:
            jsonl_path = find_most_recent_jsonl()
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)

    print(f"[session-close] Source:   {jsonl_path}")

    turns  = parse_jsonl(jsonl_path)
    ctx    = extract_full_context(turns)

    if not ctx["messages"]:
        print("[session-close] No messages found in session file. Nothing to write.")
        sys.exit(0)

    # A real session requires the human to have typed something AND me to have replied.
    # Claude Code auto-injects initialization context as a user turn, so user_turns > 0
    # is not sufficient — it's always true even when you open and immediately exit.
    # The definitive signal: did I (the assistant) actually produce text in response?
    assistant_text_turns = sum(
        1 for m in ctx["messages"]
        if m["role"] == "assistant" and m.get("content", "").strip()
    )
    if assistant_text_turns == 0:
        print("[session-close] No assistant responses — session was empty (head in the door). Skipping.")
        sys.exit(0)

    # A launch-only session (open → pick room → close) passes the above check because
    # the room picker generates an assistant text response. Guard against it:
    # Every session has at least 2 user typed turns (system init + room selection).
    # A real session has 3+ typed turns OR at least one work tool was invoked.
    user_typed_turns = sum(
        1 for m in ctx["messages"]
        if m["role"] == "user" and m.get("content", "").strip()
    )
    work_tools_used = sum(
        1 for t in ctx["tool_log"]
        if t["name"] in {"Edit", "Write", "Bash", "Read", "Glob", "Grep", "Agent"}
    )
    if user_typed_turns < 3 and work_tools_used == 0:
        print(f"[session-close] Launch/room-selection only "
              f"(typed turns: {user_typed_turns}, work tools: {work_tools_used}). Skipping.")
        sys.exit(0)

    origin = get_origin()

    all_ts  = [m["timestamp"] for m in ctx["messages"] if m.get("timestamp")]
    created = parse_ts(all_ts[0]) if all_ts else \
              datetime.fromtimestamp(jsonl_path.stat().st_ctime, tz=timezone.utc).astimezone()

    # Compute session folder path so frontmatter can reference the witness location
    short_id     = jsonl_path.stem[:8]
    date_str     = created.strftime("%Y-%m-%d")
    file_slug    = f"{date_str}-claude-session-{short_id}"
    witness_path = CLAUDE_DIR / file_slug / jsonl_path.name

    filename, content, image_files = build_artifact(jsonl_path, ctx, origin, witness_path)
    out_path = write_session_package(filename, content, jsonl_path, image_files)

    tok = ctx["token_totals"]
    print(f"[session-close] Artifact: {out_path}")
    print(f"[session-close] Turns:    {sum(1 for m in ctx['messages'] if m['role'] == 'user')} user / "
          f"{sum(1 for m in ctx['messages'] if m['role'] == 'assistant')} assistant")
    print(f"[session-close] Tools:    {len(ctx['tool_log'])}")
    print(f"[session-close] Tokens:   {tok['input']:,} in / {tok['output']:,} out "
          f"({tok['cache_read']:,} cache read)")

    # Build compact summary for the registry (surfaced in next launch brief)
    all_ts   = [m["timestamp"] for m in ctx["messages"] if m.get("timestamp")]
    modified = parse_ts(all_ts[-1]) if all_ts else \
               datetime.fromtimestamp(jsonl_path.stat().st_mtime, tz=timezone.utc).astimezone()
    duration_secs = int((modified - created).total_seconds())
    files_touched = sorted(set(
        t["input_summary"] for t in ctx["tool_log"]
        if t["name"] in ("Edit", "Write", "NotebookEdit") and t["input_summary"]
    ))
    # Keep just basenames so the registry stays readable
    files_touched = [os.path.basename(f) for f in files_touched]

    summary = {
        "turns":         sum(1 for m in ctx["messages"] if m["role"] == "user"),
        "tool_calls":    len(ctx["tool_log"]),
        "duration":      fmt_ms(duration_secs * 1000),
        "files_touched": files_touched,
    }

    # Mark this session closed in the registry (~/.servetus_sessions.json)
    close_session_in_registry(
        vault      = str(VAULT_ROOT),
        started_ts = created.isoformat(),
        session_id = ctx["session_meta"].get("sessionId", jsonl_path.stem),
        room       = os.environ.get("SERVETUS_ROOM", ""),
        summary    = summary,
    )

    # Scan for orphaned sessions (real content, no artifact) and report for next launch
    orphans = scan_orphans(jsonl_path)
    write_orphan_report(orphans)

    # Write brief for LLM context injection at next session open
    brief_path = VAULT_ROOT / "10-System" / "last-session-brief.md"
    write_session_brief(ctx, duration_secs, os.environ.get("SERVETUS_ROOM", ""),
                        files_touched, brief_path)


if __name__ == "__main__":
    main()
