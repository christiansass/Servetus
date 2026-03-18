#!/usr/bin/env python3
"""
Servetus Inbox Watcher
----------------------
Watches Inbox/Otter.ai/ for new .docx files and auto-extracts transcripts
into a session queue file (10-System/inbox-queue.md) for Claude to review.

Rules:
- Only processes .docx files (Otter transcripts)
- Only processes files whose filename date is ON OR BEFORE the session cutoff date
- Skips files already seen this session
- Appends each new file's extracted text to the queue

Usage:
    python3 10-System/inbox-watcher.py [--session-date YYYY-MM-DD]

    Defaults to yesterday if no date given (covers prior-session recordings).
    Pass --session-date 2026-03-15 to explicitly set the cutoff.
"""

import sys
import re
import time
import zipfile
import argparse
from datetime import datetime, date
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
INBOX_ROOT = VAULT_ROOT.parent / "Inbox"

# Dirs watched recursively (extract + queue docx; announce everything else)
WATCH_DIRS_DEEP = [
    INBOX_ROOT / "Otter.ai",
    INBOX_ROOT / "Telegram",
]
# Dirs watched at root only (announce any new file, no extraction)
WATCH_DIRS_SHALLOW = [
    INBOX_ROOT,
]

QUEUE_FILE = Path(__file__).resolve().parent / "inbox-queue.md"
POLL_INTERVAL = 5  # seconds


def parse_date_from_name(name: str):
    """Extract YYYY-MM-DD from a filename or folder name. Returns date or None."""
    m = re.search(r'(\d{4}-\d{2}-\d{2})', name)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            return None
    return None


def extract_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as z:
            with z.open('word/document.xml') as x:
                content = x.read().decode('utf-8')
                text = re.sub(r'<[^>]+>', ' ', content)
                text = re.sub(r'\s+', ' ', text).strip()
                return text
    except Exception as e:
        return f"[extraction error: {e}]"


def append_to_queue(path: Path, text: str):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"""
---
## {path.name}
**Ingested:** {timestamp}
**Path:** `{path}`

{text[:6000]}{"...[truncated]" if len(text) > 6000 else ""}

"""
    with open(QUEUE_FILE, 'a') as f:
        f.write(entry)
    print(f"[watcher] queued: {path.name}")


def init_queue():
    if not QUEUE_FILE.exists():
        QUEUE_FILE.write_text(
            f"# Servetus Inbox Queue\n"
            f"*Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
            f"*Watcher running — new Otter transcripts appear below as they sync.*\n"
        )


def announce(path: Path):
    """Print a visible hopper announcement to the terminal."""
    print(f"\n\033[33m[HOPPER]\033[0m  {path.name}  ←  ready to process", flush=True)


def watch(cutoff: date):
    seen = set()

    # Seed seen with all existing files before watcher started
    for watch_dir in WATCH_DIRS_DEEP:
        if watch_dir.exists():
            for f in watch_dir.rglob("*"):
                if f.is_file():
                    seen.add(f)
    for watch_dir in WATCH_DIRS_SHALLOW:
        if watch_dir.exists():
            for f in watch_dir.glob("*"):
                if f.is_file():
                    seen.add(f)

    total_dirs = len(WATCH_DIRS_DEEP) + len(WATCH_DIRS_SHALLOW)
    print(f"[watcher] started — cutoff: {cutoff} | {total_dirs} dirs | {len(seen)} existing files seeded", flush=True)

    while True:
        time.sleep(POLL_INTERVAL)

        # Deep dirs — extract docx, announce everything
        for watch_dir in WATCH_DIRS_DEEP:
            if not watch_dir.exists():
                continue
            for f in watch_dir.rglob("*"):
                if not f.is_file() or f in seen:
                    continue
                seen.add(f)
                file_date = parse_date_from_name(f.name) or parse_date_from_name(f.parent.name)
                if file_date and file_date > cutoff:
                    continue
                announce(f)
                if f.suffix.lower() == ".docx":
                    text = extract_docx_text(f)
                    append_to_queue(f, text)

        # Shallow dirs — announce only (no extraction)
        for watch_dir in WATCH_DIRS_SHALLOW:
            if not watch_dir.exists():
                continue
            for f in watch_dir.glob("*"):
                if not f.is_file() or f in seen:
                    continue
                seen.add(f)
                announce(f)


def main():
    parser = argparse.ArgumentParser(description="Servetus inbox watcher")
    parser.add_argument(
        "--session-date",
        default=None,
        help="Cutoff date YYYY-MM-DD (only ingest files on or before this date). Defaults to today."
    )
    args = parser.parse_args()

    if args.session_date:
        cutoff = date.fromisoformat(args.session_date)
    else:
        cutoff = date.today()

    init_queue()
    watch(cutoff)


if __name__ == "__main__":
    main()
