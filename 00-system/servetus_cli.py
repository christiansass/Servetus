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
"""

import sys
import os
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = VAULT_ROOT / "01-daily-logs"

def ensure_dirs():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def build_daily_log(content: str) -> str:
    today = datetime.now()
    date_iso = today.strftime("%Y-%m-%d")
    pretty = today.strftime("%B %d, %Y")
    return f"""---
type: daily-log
date: {date_iso}
title: "Daily Log — {pretty}"
source: servetus-cli
status: draft
tags: [daily-log]
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

def cmd_log(args):
    ensure_dirs()
    if args:
        raw = " ".join(args)
    else:
        print("Enter your log content. Press Ctrl-D (or Ctrl-Z on Windows) when done:")
        raw_lines = sys.stdin.read()
        raw = raw_lines.strip()
    if not raw:
        print("No content provided, aborting.")
        return
    today = datetime.now()
    filename = today.strftime("%Y-%m-%d-servetus-log.md")
    path = LOG_DIR / filename
    if path.exists():
        # append with separator
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n\n---\n# Additional Entry\n\n")
            f.write(raw + "\n")
        print(f"Appended to existing log: {path}")
    else:
        text = build_daily_log(raw)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Created new daily log: {path}")

def cmd_voice(args):
    """Run the voice capture pipeline."""
    # Parse voice-specific flags
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
            """Stub handler — replace with kernel dispatch."""
            text = msg.get("message", "")
            actor = msg.get("actorDisplayName", "unknown")
            # For now, just acknowledge. The real kernel goes here.
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
        print("  log [text...]       Create a daily log entry")
        print("  voice [options]     Record, transcribe, and analyze voice")
        print("  nc <test|sync|listen>  Nextcloud operations")
        print("  archive [text...]   Archive session to vault + Nextcloud")
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
    args = sys.argv[2:]
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
