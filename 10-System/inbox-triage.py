#!/usr/bin/env python3
"""
Servetus Inbox Triage
---------------------
Tiered inbox scan with file-type classification, arc matching,
and suggested next actions.

Run this whenever the user says "check the inbox/hopper" or reports
new evidence. Returns a numbered triage list for Claude to present.

Tier 1: files modified in the last 120 minutes
Tier 2: files modified in the last 24 hours (fallback)

Usage:
    python3 inbox-triage.py
    python3 inbox-triage.py --inbox ~/Nextcloud/Obsidian/Inbox
    python3 inbox-triage.py --inbox ~/... --vault ~/Nextcloud/Obsidian/Servetus
"""

import argparse
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

TIER1_MINUTES = 120
TIER2_HOURS   = 24
EXCLUDE_NAMES = {".DS_Store"}

# ── File type registry ────────────────────────────────────────────────────────
# Maps extension groups → (label, suggested actions)

FILE_TYPES = {
    frozenset([".m4a", ".mp3", ".wav", ".aac", ".ogg", ".flac", ".aiff"]):
        ("Audio recording",
         ["Transcribe with Otter", "Transcribe locally with Whisper", "Archive as-is"]),

    frozenset([".mp4", ".mov", ".avi", ".mkv", ".m4v", ".webm"]):
        ("Video file",
         ["Transcribe + extract timestamps", "Archive with reference record", "Skip"]),

    frozenset([".pdf"]):
        ("PDF document",
         ["Read + file to arc", "Extract text + file", "Skip"]),

    frozenset([".json"]):
        ("Data export",
         ["Inspect + run ingestion pipeline", "File raw to artifacts", "Skip"]),

    frozenset([".md", ".txt"]):
        ("Text / note",
         ["Review + file to arc", "Extract memories", "Skip"]),

    frozenset([".png", ".jpg", ".jpeg", ".heic", ".webp", ".gif", ".tiff"]):
        ("Image / photo",
         ["File to witnesses", "Add to arc evidence", "Skip"]),

    frozenset([".docx", ".doc", ".pages", ".rtf"]):
        ("Word document",
         ["Read + file to arc", "Convert + extract text", "Skip"]),

    frozenset([".html", ".htm"]):
        ("Web export",
         ["Extract text + file", "Archive as reference", "Skip"]),

    frozenset([".zip", ".tar", ".gz"]):
        ("Archive / bundle",
         ["Inspect contents", "Unpack + triage", "Skip"]),

    frozenset([".csv", ".xlsx", ".xls"]):
        ("Spreadsheet / data",
         ["Review + file to arc", "Extract relevant rows", "Skip"]),
}

def classify(path: Path) -> tuple:
    """Return (type_label, [actions]) for a file."""
    ext = path.suffix.lower()
    for exts, (label, actions) in FILE_TYPES.items():
        if ext in exts:
            return label, actions
    return "Unknown file type", ["Review manually", "Skip"]


# ── Arc loading ───────────────────────────────────────────────────────────────

def load_active_arcs(vault: Path) -> list:
    """Return list of {title, short_name, keywords, path} for active arcs."""
    arcs_dir = vault / "05-Arcs"
    if not arcs_dir.exists():
        return []
    arcs = []
    for f in arcs_dir.glob("*.md"):
        if f.name.startswith("_"):
            continue
        try:
            text = f.read_text(errors="replace")
            if not text.startswith("---"):
                continue
            end = text.find("\n---", 3)
            fm  = text[3:end] if end != -1 else text[3:]
            sm  = re.search(r'^\s*status:\s*(.+)$', fm, re.M)
            if not sm or sm.group(1).strip().strip("'\"").lower() not in \
                    ("active", "open", "in-progress", "ongoing"):
                continue
            tm = re.search(r'^\s*title:\s*["\']?(.+?)["\']?\s*$', fm, re.M)
            sn = re.search(r'^\s*short_name:\s*["\']?(.+?)["\']?\s*$', fm, re.M)
            kw = re.search(r'^\s*tags:\s*(.+)$', fm, re.M)
            title      = tm.group(1).strip().strip("'\"") if tm else f.stem
            short_name = sn.group(1).strip().strip("'\"") if sn else title
            # keywords: title words + tags
            words = set(re.findall(r'\w+', title.lower()))
            if kw:
                words |= set(re.findall(r'\w+', kw.group(1).lower()))
            arcs.append({
                "title":      title,
                "short_name": short_name,
                "keywords":   words,
                "path":       f,
            })
        except Exception:
            pass
    return arcs


def match_arc(filename: str, arcs: list):
    """Return the best-matching arc title, or None."""
    words = set(re.findall(r'\w+', filename.lower()))
    best_arc, best_score = None, 0
    for arc in arcs:
        score = len(words & arc["keywords"])
        if score > best_score:
            best_score, best_arc = score, arc["short_name"]
    return best_arc if best_score > 0 else None


# ── File scan ─────────────────────────────────────────────────────────────────

def scan(inbox: Path, cutoff: float) -> list:
    results = []
    for root, dirs, files in os.walk(inbox):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            if name.startswith(".") or name in EXCLUDE_NAMES:
                continue
            p = Path(root) / name
            try:
                st = p.stat()
            except OSError:
                continue
            if st.st_mtime >= cutoff:
                results.append((st.st_mtime, st.st_size, p))
    results.sort(key=lambda x: x[0], reverse=True)
    return results


# ── Formatting ────────────────────────────────────────────────────────────────

def fmt_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

def fmt_age(mtime: float, now: float) -> str:
    secs = int(now - mtime)
    if secs < 60:     return f"{secs}s ago"
    if secs < 3600:   return f"{secs // 60}m ago"
    h, m = divmod(secs, 3600)
    return f"{h}h {m // 60:02d}m ago"


# ── Output ────────────────────────────────────────────────────────────────────

def print_triage(results: list, inbox: Path, arcs: list, tier: int, window: str) -> None:
    now = datetime.now(timezone.utc).timestamp()
    print(f"\n{'─' * 60}")
    print(f"  INBOX TRIAGE  —  Tier {tier} ({window})")
    print(f"  {len(results)} item{'s' if len(results) != 1 else ''} found")
    print(f"{'─' * 60}\n")

    for i, (mtime, size, path) in enumerate(results, 1):
        rel       = path.relative_to(inbox)
        age       = fmt_age(mtime, now)
        dt        = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        ftype, actions = classify(path)
        arc_match = match_arc(path.name, arcs)

        print(f"  {i}.  {path.name}")
        print(f"       {dt}  ({age})   {fmt_size(size)}   ← {rel.parent}" if rel.parent != Path('.') else
              f"       {dt}  ({age})   {fmt_size(size)}")
        print(f"       Type:  {ftype}")
        if arc_match:
            print(f"       Arc:   {arc_match}  ← likely match")
        else:
            print(f"       Arc:   no match — needs manual filing")
        print(f"       Do:    {' / '.join(actions)}")
        print()

    print(f"{'─' * 60}")
    print(f"  Reply with a number to act, or describe what to do.\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Servetus inbox triage")
    parser.add_argument(
        "--inbox",
        type=Path,
        default=Path.home() / "Nextcloud" / "Obsidian" / "Inbox",
    )
    parser.add_argument(
        "--vault",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    args = parser.parse_args()

    inbox = args.inbox.expanduser().resolve()
    vault = args.vault.expanduser().resolve()

    if not inbox.exists():
        print(f"Error: inbox not found: {inbox}", file=sys.stderr)
        sys.exit(1)

    arcs = load_active_arcs(vault)
    now  = datetime.now(timezone.utc).timestamp()

    # Tier 1
    results = scan(inbox, now - TIER1_MINUTES * 60)
    if results:
        print_triage(results, inbox, arcs, tier=1, window="last 120 minutes")
        return

    # Tier 2
    results = scan(inbox, now - TIER2_HOURS * 3600)
    if results:
        print(f"\n  (nothing in the last 120 minutes — expanding to 24 hours)")
        print_triage(results, inbox, arcs, tier=2, window="last 24 hours")
    else:
        print(f"\n  Inbox is clear — nothing modified in the last 24 hours.\n")


if __name__ == "__main__":
    main()
