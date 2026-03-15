#!/usr/bin/env python3
"""
Servetus Session Close
----------------------
Converts the most recent Claude Code session (.jsonl) for the Servetus vault
into a full-fidelity artifact markdown file and preserves the raw JSONL as a witness.

Two outputs per session:
  1. Raw JSONL → 00-Artifacts/claude-sessions/YYYY/<session-id>.jsonl  (witness / ground truth)
  2. Markdown  → Inbox/Claude/<date>-claude-session-<id>.md             (human-readable artifact)

Only captures sessions from the Servetus project directory in ~/.claude/projects/.

Usage:
    python3 session-close.py                      # auto-detects most recent Servetus session
    python3 session-close.py <path/to/file.jsonl> # explicit file
"""

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

# Session artifacts land in the sibling Inbox vault (multi-vault Obsidian layout):
#   Obsidian/
#   ├── Servetus/   ← this vault
#   └── Inbox/
#       └── Claude/ ← artifacts land here
_sibling_claude = VAULT_ROOT.parent / "Inbox" / "Claude"
_fallback_claude = VAULT_ROOT / "00-inbox" / "claude"

if _sibling_claude.parent.exists():
    CLAUDE_DIR = _sibling_claude
else:
    CLAUDE_DIR = _fallback_claude
    print(
        f"[session-close] Warning: sibling Inbox vault not found at "
        f"{_sibling_claude.parent} — falling back to {_fallback_claude}"
    )

# Raw JSONL witnesses land in 00-Artifacts (sovereign, ground truth, never edited)
WITNESS_DIR = VAULT_ROOT / "00-Artifacts" / "claude-sessions"


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
        "messages":      messages,
    }


# ---------------------------------------------------------------------------
# Build artifact markdown
# ---------------------------------------------------------------------------

def build_artifact(jsonl_path: Path, ctx: dict, origin: dict, witness_path: Path) -> tuple:
    """Returns (filename, markdown_content)."""
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

date: {datetime_str}
closed: {closed_str}
duration: "{duration_str}"
timezone: "America/Chicago"

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

    body    = "\n".join(lines)
    content = frontmatter + "\n\n" + body
    return f"{file_slug}.md", content


# ---------------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------------

def copy_witness(jsonl_path: Path, created: datetime) -> Path:
    """Copy raw JSONL to 00-Artifacts/claude-sessions/YYYY/ as the ground-truth witness."""
    year_dir = WITNESS_DIR / created.strftime("%Y")
    year_dir.mkdir(parents=True, exist_ok=True)
    dest = year_dir / jsonl_path.name
    if not dest.exists():
        shutil.copy2(jsonl_path, dest)
        print(f"[session-close] Witness:  {dest}")
    else:
        print(f"[session-close] Witness already exists: {dest}")
    return dest


def write_artifact(filename: str, content: str) -> Path:
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CLAUDE_DIR / filename
    if out_path.exists():
        print(f"[session-close] Already exists: {out_path}")
        return out_path
    out_path.write_text(content, encoding="utf-8")
    return out_path


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

    origin = get_origin()

    # Determine session start for witness folder
    all_ts  = [m["timestamp"] for m in ctx["messages"] if m.get("timestamp")]
    created = parse_ts(all_ts[0]) if all_ts else \
              datetime.fromtimestamp(jsonl_path.stat().st_ctime, tz=timezone.utc).astimezone()

    witness_path          = copy_witness(jsonl_path, created)
    filename, content     = build_artifact(jsonl_path, ctx, origin, witness_path)
    out_path              = write_artifact(filename, content)

    tok = ctx["token_totals"]
    print(f"[session-close] Artifact: {out_path}")
    print(f"[session-close] Turns:    {sum(1 for m in ctx['messages'] if m['role'] == 'user')} user / "
          f"{sum(1 for m in ctx['messages'] if m['role'] == 'assistant')} assistant")
    print(f"[session-close] Tools:    {len(ctx['tool_log'])}")
    print(f"[session-close] Tokens:   {tok['input']:,} in / {tok['output']:,} out "
          f"({tok['cache_read']:,} cache read)")


if __name__ == "__main__":
    main()
