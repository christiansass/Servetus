#!/usr/bin/env python3
"""
Servetus Session Close
----------------------
Converts the most recent Claude Code session (.jsonl) for the Servetus vault
into a raw artifact markdown file and writes it to 00-inbox/YYYY/MM-MonthName/YYYY-MM-DD/.

Only captures sessions from the Servetus project directory in ~/.claude/projects/.
This ensures non-Servetus Claude Code sessions are never captured.

Inbox is the entry point — all raw captures land here for review before filing.

Usage:
    python3 session-close.py                      # auto-detects most recent Servetus session
    python3 session-close.py <path/to/file.jsonl> # explicit file

The artifact file is named:
    YYYY-MM-DD-claude-session-<short-id>.md

Run this at the end of every Servetus Claude Code session (or use 'sc' which runs it automatically).
"""

import sys
import json
import uuid
import socket
import platform
from datetime import datetime, timezone
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
INBOX_DIR  = VAULT_ROOT / "00-inbox"
CONFIG_DIR = VAULT_ROOT / "config"

MONTH_NAMES = {
    1: "01-January", 2: "02-February", 3: "03-March", 4: "04-April",
    5: "05-May", 6: "06-June", 7: "07-July", 8: "08-August",
    9: "09-September", 10: "10-October", 11: "11-November", 12: "12-December",
}


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
    """
    Find the Claude Code project directory that corresponds to this Servetus vault.
    Claude Code slugifies the vault path as the project directory name.
    e.g. /Users/foo/Nextcloud/Obsidian/Servetus → -Users-foo-Nextcloud-Obsidian-Servetus
    """
    home = Path.home()
    projects = home / ".claude" / "projects"
    if not projects.exists():
        raise FileNotFoundError(f"Claude Code projects directory not found: {projects}")

    # Slugify the vault root path the same way Claude Code does
    slug = str(VAULT_ROOT).replace("/", "-").replace("\\", "-")
    if slug.startswith("-"):
        pass  # already has leading dash from absolute path
    project_dir = projects / slug

    if project_dir.exists():
        return project_dir

    # Fallback: search for a project dir whose slug contains key vault path components
    vault_parts = [p for p in VAULT_ROOT.parts if p not in ("", "/")]
    for d in projects.iterdir():
        if d.is_dir() and all(p in d.name for p in vault_parts[-2:]):
            return d

    raise FileNotFoundError(
        f"Could not find Claude Code project directory for vault: {VAULT_ROOT}\n"
        f"Expected: {project_dir}\n"
        f"Launch Claude Code from within the vault using 'sc' to ensure sessions are scoped correctly."
    )


def find_most_recent_jsonl() -> Path:
    """Find the most recently modified .jsonl in the Servetus project directory only."""
    project_dir = find_servetus_project_dir()
    candidates = list(project_dir.glob("*.jsonl"))
    if not candidates:
        raise FileNotFoundError(
            f"No .jsonl session files found in {project_dir}\n"
            f"Make sure you launched this session using 'sc' from the Servetus vault."
        )
    return max(candidates, key=lambda p: p.stat().st_mtime)


# ---------------------------------------------------------------------------
# Parse .jsonl into structured turns
# ---------------------------------------------------------------------------

def parse_jsonl(path: Path) -> list:
    """Parse Claude Code .jsonl into a list of message dicts."""
    turns = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                turns.append(obj)
            except json.JSONDecodeError:
                continue
    return turns


def extract_messages(turns: list) -> list:
    """Extract human/assistant message pairs from raw turns."""
    messages = []
    for turn in turns:
        # Claude Code jsonl format varies — handle common shapes
        msg_type = turn.get("type", "")

        if msg_type == "human" or turn.get("role") == "user":
            content = turn.get("message", turn.get("content", ""))
            if isinstance(content, list):
                # multi-part content blocks
                text = "\n".join(
                    block.get("text", "") for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                )
            else:
                text = str(content)
            if text.strip():
                messages.append({"role": "user", "content": text.strip()})

        elif msg_type == "assistant" or turn.get("role") == "assistant":
            content = turn.get("message", turn.get("content", ""))
            if isinstance(content, list):
                text = "\n".join(
                    block.get("text", "") for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                )
            else:
                text = str(content)
            if text.strip():
                messages.append({"role": "assistant", "content": text.strip()})

    return messages


# ---------------------------------------------------------------------------
# Build artifact markdown
# ---------------------------------------------------------------------------

def build_artifact(jsonl_path: Path, messages: list, origin: dict) -> tuple:
    """Returns (filename, markdown_content)."""
    stat = jsonl_path.stat()
    created  = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).astimezone()
    modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).astimezone()

    date_str     = created.strftime("%Y-%m-%d")
    datetime_str = created.strftime("%Y-%m-%dT%H:%M:%S%z")
    short_id     = jsonl_path.stem[:8]
    slug         = f"{date_str}-claude-session-{short_id}"
    title        = f"Claude Code Session — {created.strftime('%B %d, %Y')}"

    # Count turns
    user_turns      = sum(1 for m in messages if m["role"] == "user")
    assistant_turns = sum(1 for m in messages if m["role"] == "assistant")

    frontmatter = f"""---
type: artifact
title: "{title}"
slug: "{slug}"

date: {datetime_str}
closed: {modified.strftime("%Y-%m-%dT%H:%M:%S%z")}
timezone: "America/Chicago"

origin:
  machine: "{origin['machine']}"
  mac: "{origin['mac']}"
  ip: "{origin['ip']}"
  os: "{origin['os']}"

source:
  file: "{jsonl_path.name}"
  path: "{jsonl_path}"
  turns: {user_turns}

circles: []
published: false
tags: [artifact, session, claude-code]
---"""

    # Build transcript body
    lines = [f"# {title}\n"]
    lines.append(f"**Session file:** `{jsonl_path.name}`  ")
    lines.append(f"**Turns:** {user_turns} user / {assistant_turns} assistant  ")
    lines.append(f"**Machine:** {origin['machine']} | {origin['os']}\n")
    lines.append("---\n")
    lines.append("## Transcript\n")

    for i, msg in enumerate(messages, 1):
        role_label = "**User**" if msg["role"] == "user" else "**Servetus**"
        lines.append(f"### {role_label}\n")
        lines.append(msg["content"])
        lines.append("\n---\n")

    body = "\n".join(lines)
    content = frontmatter + "\n\n" + body

    filename = f"{slug}.md"
    return filename, content


# ---------------------------------------------------------------------------
# Write to vault
# ---------------------------------------------------------------------------

def write_artifact(date: datetime, filename: str, content: str) -> Path:
    month_name = MONTH_NAMES[date.month]
    date_str   = date.strftime("%Y-%m-%d")
    out_dir    = INBOX_DIR / str(date.year) / month_name / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path   = out_dir / filename

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

    print(f"[session-close] Source: {jsonl_path}")

    turns    = parse_jsonl(jsonl_path)
    messages = extract_messages(turns)

    if not messages:
        print("[session-close] No messages found in session file. Nothing to write.")
        sys.exit(0)

    origin = get_origin()
    stat   = jsonl_path.stat()
    created = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).astimezone()

    filename, content = build_artifact(jsonl_path, messages, origin)
    out_path = write_artifact(created, filename, content)

    print(f"[session-close] Written: {out_path}")
    print(f"[session-close] Turns captured: {sum(1 for m in messages if m['role'] == 'user')}")


if __name__ == "__main__":
    main()
