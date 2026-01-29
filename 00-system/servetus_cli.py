#!/usr/bin/env python3
"""
Servetus Phase 0 CLI Prototype

Usage:
    python servetus_cli.py log "optional text here"
If no text is passed, you'll be dropped into a prompt to type/paste,
finish with Ctrl-D (Linux/macOS) or Ctrl-Z + Enter (Windows).

This writes a dated daily-log markdown file into `01-daily-logs/`.
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

def main():
    if len(sys.argv) < 2:
        print("Usage: python servetus_cli.py log [text...]")
        sys.exit(1)
    command = sys.argv[1]
    args = sys.argv[2:]
    if command == "log":
        cmd_log(args)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
