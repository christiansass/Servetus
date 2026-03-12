#!/usr/bin/env python3
"""
Servetus CLI

Usage:
    python servetus_cli.py log "optional text here"
    python servetus_cli.py voice                     # Record and transcribe
    python servetus_cli.py voice --file input.wav    # Process existing audio
    python servetus_cli.py voice --model large-v3    # Use larger model
    python servetus_cli.py voice --no-prosody        # Skip SVP generation
    python servetus_cli.py voice --list-devices      # Show microphones
    python servetus_cli.py nc test                   # Test Nextcloud connection
    python servetus_cli.py nc sync                   # Sync vault to Nextcloud
    python servetus_cli.py nc listen                 # Listen on Talk room
    python servetus_cli.py archive "session text"    # Archive session to vault + Nextcloud

For log: if no text is passed, you'll be dropped into a prompt to type/paste,
finish with Ctrl-D (Linux/macOS) or Ctrl-Z + Enter (Windows).

Writes memory files into 02-memories/.
"""

import sys
import os
import socket
import uuid
import platform
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR    = VAULT_ROOT / "02-memories"


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
    overrides = VAULT_ROOT / "config" / "overrides.md"
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
# Memory builder (v0.2 flat frontmatter)
# ---------------------------------------------------------------------------

def build_memory(content: str) -> str:
    today    = datetime.now()
    date_iso = today.strftime("%Y-%m-%d")
    pretty   = today.strftime("%B %d, %Y")
    origin   = get_origin()

    return f"""---
type: memory
title: "Daily Log — {pretty}"
slug: "daily-log-{date_iso}"
date: {date_iso}

source_artifact: null
linked_event: null
linked_project: null
linked_arc: null

origin:
  machine: "{origin['machine']}"
  mac: "{origin['mac']}"
  ip: "{origin['ip']}"
  os: "{origin['os']}"

circles: []
published: false
tags: [memory, daily-log]
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
            f.write(build_memory(raw))
        print(f"Created new memory: {path}")


def cmd_voice(args):
    """Run the voice capture pipeline."""
    audio_file = None
    model = "base"
    language = None
    speaker = ""
    skip_prosody = False
    show_devices = False

    i = 0
    while i < len(args):
        if args[i] == "--file" and i + 1 < len(args):
            audio_file = args[i + 1]
            i += 2
        elif args[i] == "--model" and i + 1 < len(args):
            model = args[i + 1]
            i += 2
        elif args[i] == "--language" and i + 1 < len(args):
            language = args[i + 1]
            i += 2
        elif args[i] == "--speaker" and i + 1 < len(args):
            speaker = args[i + 1]
            i += 2
        elif args[i] == "--no-prosody":
            skip_prosody = True
            i += 1
        elif args[i] == "--list-devices":
            show_devices = True
            i += 1
        else:
            print(f"Unknown voice option: {args[i]}")
            sys.exit(1)

    from voice.pipeline import run
    run(
        audio_file=audio_file,
        model=model,
        language=language,
        speaker=speaker,
        skip_prosody=skip_prosody,
        show_devices=show_devices,
    )


def cmd_nc(args):
    """Nextcloud operations: test, sync, listen."""
    from nextcloud.config import load_config
    from nextcloud.webdav import WebDAVClient

    config = load_config()
    if config is None:
        print("Nextcloud not configured.")
        print("Copy 00-system/nextcloud/nextcloud.yaml.example → config/nextcloud.yaml")
        sys.exit(1)

    if not args:
        print("Usage: servetus nc <test|sync|listen>")
        sys.exit(1)

    subcmd = args[0]

    if subcmd == "test":
        client = WebDAVClient(config)
        if client.test_connection():
            print(f"  Connected to {config.url}")
            print(f"  User: {config.username}")
            print(f"  Vault root: {config.remote_root}")
        else:
            print(f"  Failed to connect to {config.url}")
            sys.exit(1)

    elif subcmd == "sync":
        client = WebDAVClient(config)
        if not client.test_connection():
            print(f"  Cannot reach {config.url}")
            sys.exit(1)
        print(f"  Syncing vault to {config.url}{config.remote_root}")
        for sync_path in config.sync_paths:
            local_dir = VAULT_ROOT / sync_path.rstrip("/")
            if local_dir.exists():
                print(f"\n  {sync_path}")
                counts = client.upload_directory(local_dir)
                print(f"    uploaded: {counts['uploaded']}, failed: {counts['failed']}")

    elif subcmd == "listen":
        if not config.talk_enabled:
            print("  Talk is not enabled in config/nextcloud.yaml")
            sys.exit(1)
        from nextcloud.talk import TalkListener
        listener = TalkListener(config)

        def handler(msg):
            text = msg.get("message", "")
            actor = msg.get("actorDisplayName", "unknown")
            return f"[Servetus received]: {text[:100]}"

        listener.listen(handler)

    else:
        print(f"  Unknown nc subcommand: {subcmd}")
        print("  Available: test, sync, listen")
        sys.exit(1)


def cmd_archive(args):
    """Archive a session transcript to vault + Nextcloud."""
    from nextcloud.archive import archive_session

    if args:
        content = " ".join(args)
    else:
        print("Paste session content. Press Ctrl-D (or Ctrl-Z on Windows) when done:")
        content = sys.stdin.read().strip()

    if not content:
        print("No content provided, aborting.")
        return

    archive_session(content=content, source="claude-code")


def main():
    if len(sys.argv) < 2:
        print("Servetus CLI")
        print()
        print("Commands:")
        print("  log [text...]          Create a memory entry")
        print("  voice [options]        Record, transcribe, and analyze voice")
        print("  nc <test|sync|listen>  Nextcloud operations")
        print("  archive [text...]      Archive session to vault + Nextcloud")
        print()
        print("Voice options:")
        print("  --file PATH        Process existing audio file")
        print("  --model SIZE       Whisper model (tiny/base/small/medium/large-v3)")
        print("  --language CODE    Language hint (e.g., en)")
        print("  --speaker NAME     Speaker name for SVP header")
        print("  --no-prosody       Skip prosodic analysis")
        print("  --list-devices     Show available microphones")
        sys.exit(1)

    command = sys.argv[1]
    args    = sys.argv[2:]

    if command == "log":
        cmd_log(args)
    elif command == "voice":
        cmd_voice(args)
    elif command == "nc":
        cmd_nc(args)
    elif command == "archive":
        cmd_archive(args)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
