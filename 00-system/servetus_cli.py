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


def main():
    if len(sys.argv) < 2:
        print("Servetus CLI")
        print()
        print("Commands:")
        print("  log [text...]    Create a daily log entry")
        print("  voice [options]  Record, transcribe, and analyze voice")
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
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
