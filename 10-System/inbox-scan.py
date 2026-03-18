#!/usr/bin/env python3
"""
Servetus Inbox Scanner
----------------------
Tiered evidence search against the Inbox folder.
Run this first whenever new evidence arrives.

Tier 1: files modified in the last 120 minutes
Tier 2: files modified in the last 24 hours (fallback if Tier 1 is empty)

Usage:
    python3 inbox-scan.py
    python3 inbox-scan.py --inbox ~/Nextcloud/Obsidian/Inbox
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

TIER1_MINUTES = 120
TIER2_HOURS   = 24

EXCLUDE_NAMES = {".DS_Store"}


def scan(inbox: Path, cutoff_secs: float) -> list:
    results = []
    for root, dirs, files in os.walk(inbox):
        # Prune hidden dirs and .git in-place
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            if name.startswith(".") or name in EXCLUDE_NAMES:
                continue
            p = Path(root) / name
            try:
                st = p.stat()
            except OSError:
                continue
            if st.st_mtime >= cutoff_secs:
                results.append((st.st_mtime, st.st_size, p))
    results.sort(key=lambda x: x[0], reverse=True)
    return results


def fmt_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def fmt_age(mtime: float, now: float) -> str:
    secs = int(now - mtime)
    if secs < 60:
        return f"{secs}s ago"
    if secs < 3600:
        return f"{secs // 60}m ago"
    h, m = divmod(secs, 3600)
    return f"{h}h {m // 60:02d}m ago"


def print_results(results: list, inbox: Path, tier: int, window: str) -> None:
    now = datetime.now(timezone.utc).timestamp()
    label = f"Tier {tier} — modified in the last {window}"
    print(f"\n  {label}")
    print(f"  {'─' * len(label)}")
    for mtime, size, path in results:
        dt  = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        age = fmt_age(mtime, now)
        rel = path.relative_to(inbox)
        print(f"  {dt}  ({age:<12})  {fmt_size(size):>8}   {rel}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Servetus inbox evidence scanner")
    parser.add_argument(
        "--inbox",
        type=Path,
        default=Path.home() / "Nextcloud" / "Obsidian" / "Inbox",
        help="Path to Inbox folder (default: ~/Nextcloud/Obsidian/Inbox)",
    )
    args = parser.parse_args()

    inbox = args.inbox.expanduser().resolve()
    if not inbox.exists():
        print(f"Error: inbox not found: {inbox}", file=sys.stderr)
        sys.exit(1)

    now = datetime.now(timezone.utc).timestamp()

    # Tier 1: last 120 minutes
    t1_cutoff = now - (TIER1_MINUTES * 60)
    results   = scan(inbox, t1_cutoff)

    if results:
        print(f"\n  Inbox: {inbox}")
        print_results(results, inbox, tier=1, window="120 minutes")
        return

    # Tier 2: last 24 hours
    t2_cutoff = now - (TIER2_HOURS * 3600)
    results   = scan(inbox, t2_cutoff)

    print(f"\n  Inbox: {inbox}")
    if results:
        print("  (nothing in the last 120 minutes — expanding to 24 hours)\n")
        print_results(results, inbox, tier=2, window="24 hours")
    else:
        print("\n  No files modified in the last 24 hours.\n")


if __name__ == "__main__":
    main()
