#!/usr/bin/env python3
"""
migrate-artifact-dates.py — One-time migration.

Moves whisper/otter transcript artifacts from transcription-date folders
to recording-date folders, removes source subdirectories (whisper/, otter-import/),
and strips the transcription date prefix from filenames.

Before: 00-Artifacts/2026/04-Apr/03/whisper/2026-04-03-recording-2025-09-05-12-15-25.md
After:  00-Artifacts/2025/09-Sep/05/recording-2025-09-05-12-15-25.md

Usage:
  python3 10-System/migrations/migrate-artifact-dates.py           # dry run
  python3 10-System/migrations/migrate-artifact-dates.py --execute  # do it
"""

import argparse
import json
import re
import shutil
from pathlib import Path

VAULT_ROOT = Path("/mnt/Cloud/Nextcloud/Obsidian/Servetus")
ARTIFACTS  = VAULT_ROOT / "00-Artifacts"
STATE_FILE = VAULT_ROOT / "10-System" / ".transcription-queue-state.json"

MONTH_NAMES = {
    1: "01-Jan", 2: "02-Feb", 3: "03-Mar", 4: "04-Apr",
    5: "05-May", 6: "06-Jun", 7: "07-Jul", 8: "08-Aug",
    9: "09-Sep", 10: "10-Oct", 11: "11-Nov", 12: "12-Dec",
}


def find_transcript_artifacts():
    """Find all .md files in whisper/ or otter-import/ subdirectories."""
    results = []
    for subdir_name in ("whisper", "otter-import"):
        for md in ARTIFACTS.rglob(f"{subdir_name}/*.md"):
            results.append(md)
    return sorted(results)


def extract_recording_date(filename: str):
    """Extract recording date from filename. Returns (year, month, day) or None."""
    # Match patterns like "recording-2025-09-05-12-15-25" in the filename
    m = re.search(r"recording-(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})", filename)
    if m:
        return int(m[1]), int(m[2]), int(m[3])
    return None


def strip_transcription_date_prefix(filename: str) -> str:
    """Remove leading YYYY-MM-DD- transcription date prefix from filename.
    e.g. '2026-04-02-recording-2025-09-05-12-15-25.md' -> 'recording-2025-09-05-12-15-25.md'
    """
    # Strip one or more leading date prefixes (YYYY-MM-DD-)
    cleaned = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", filename)
    return cleaned


def compute_new_path(md_path: Path) -> Path | None:
    """Given a current artifact path, compute where it should live."""
    filename = md_path.name
    rec = extract_recording_date(filename)
    if not rec:
        return None

    year, month, day = rec
    new_name = strip_transcription_date_prefix(filename)
    new_dir = ARTIFACTS / str(year) / MONTH_NAMES[month] / f"{day:02d}"
    return new_dir / new_name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    artifacts = find_transcript_artifacts()
    if not artifacts:
        print("[migrate] No transcript artifacts found in whisper/ or otter-import/ subdirs.")
        return

    mode = "EXECUTE" if args.execute else "DRY RUN"
    print(f"[migrate] {mode} — {len(artifacts)} artifacts to relocate\n")

    moved = 0
    skipped = 0
    errors = 0
    empty_dirs = set()

    for md in artifacts:
        new_path = compute_new_path(md)
        if not new_path:
            print(f"  [SKIP] No recording date in: {md.name}")
            skipped += 1
            continue

        rel_old = md.relative_to(ARTIFACTS)
        rel_new = new_path.relative_to(ARTIFACTS)

        if md == new_path:
            skipped += 1
            continue

        print(f"  {rel_old}")
        print(f"    -> {rel_new}")

        if args.execute:
            try:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                if new_path.exists():
                    print(f"    [WARN] Destination exists, skipping")
                    skipped += 1
                    continue
                shutil.move(str(md), str(new_path))
                empty_dirs.add(md.parent)
                moved += 1
            except Exception as e:
                print(f"    [ERROR] {e}")
                errors += 1
        else:
            moved += 1

    # Clean up empty whisper/ and otter-import/ directories
    if args.execute:
        for d in empty_dirs:
            try:
                if d.exists() and not any(d.iterdir()):
                    d.rmdir()
                    print(f"  [cleanup] Removed empty dir: {d.relative_to(ARTIFACTS)}")
            except Exception:
                pass

    # Update artifact paths in the transcription queue state file
    if args.execute and STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        processed = state.get("processed", state)
        updated = 0
        for key, info in processed.items():
            art = info.get("artifact", "")
            if not art:
                continue
            art_path = VAULT_ROOT / art
            if not art_path.exists():
                # Try to find new location
                new = compute_new_path(art_path)
                if new and new.exists():
                    info["artifact"] = str(new.relative_to(VAULT_ROOT))
                    updated += 1
        if updated:
            STATE_FILE.write_text(json.dumps(state, indent=2, default=str))
            print(f"  [state] Updated {updated} artifact paths in queue state file")

    print(f"\n[migrate] Done: {moved} moved, {skipped} skipped, {errors} errors")
    if not args.execute:
        print("[migrate] Run with --execute to actually move files.")


if __name__ == "__main__":
    main()
