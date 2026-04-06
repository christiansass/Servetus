#!/usr/bin/env python3
"""
flatten-artifact-dirs.py — One-time migration.

Flattens all source-type subdirectories (claude/, otter/, nextcloud-talk/,
telegram/, apple/, manual/, whisper/, otter-import/) inside artifact date
folders. Moves all files up to the date folder. Also fixes malformed date
folders (2026-02-02 -> 02).

The source is already referenced in each file's frontmatter — we don't need
directory structure to sort by source.

Usage:
  python3 10-System/migrations/flatten-artifact-dirs.py           # dry run
  python3 10-System/migrations/flatten-artifact-dirs.py --execute  # do it
"""

import argparse
import re
import shutil
from pathlib import Path

ARTIFACTS = Path("/mnt/Cloud/Nextcloud/Obsidian/Servetus/00-Artifacts")

MONTH_NAMES = {
    1: "01-Jan", 2: "02-Feb", 3: "03-Mar", 4: "04-Apr",
    5: "05-May", 6: "06-Jun", 7: "07-Jul", 8: "08-Aug",
    9: "09-Sep", 10: "10-Oct", 11: "11-Nov", 12: "12-Dec",
}


def fix_malformed_date_dirs(execute: bool) -> int:
    """
    Fix date folders like '2026-02-02' that should be just '02'.
    These sit at depth 3: ARTIFACTS/YYYY/MM-Mon/2026-MM-DD/
    """
    fixed = 0
    for year_dir in sorted(ARTIFACTS.iterdir()):
        if not year_dir.is_dir():
            continue
        for month_dir in sorted(year_dir.iterdir()):
            if not month_dir.is_dir():
                continue
            for day_dir in sorted(month_dir.iterdir()):
                if not day_dir.is_dir():
                    continue
                # Match malformed: 2026-02-02 instead of 02
                m = re.match(r"\d{4}-\d{2}-(\d{2})", day_dir.name)
                if not m:
                    continue
                correct_day = m.group(1)
                correct_dir = month_dir / correct_day
                print(f"  [fix-date] {day_dir.relative_to(ARTIFACTS)} -> {correct_dir.relative_to(ARTIFACTS)}")
                if execute:
                    correct_dir.mkdir(parents=True, exist_ok=True)
                    for item in day_dir.rglob("*"):
                        if item.is_file():
                            dest = correct_dir / item.relative_to(day_dir)
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            if not dest.exists():
                                shutil.move(str(item), str(dest))
                    # Remove the malformed dir if empty
                    try:
                        shutil.rmtree(day_dir)
                    except Exception:
                        pass
                fixed += 1
    return fixed


def flatten_source_dirs(execute: bool) -> tuple[int, int, int]:
    """
    Move all files from source subdirectories up to the date folder.
    Returns (moved, skipped, errors).
    """
    moved = 0
    skipped = 0
    errors = 0
    empty_dirs = set()

    # Walk ARTIFACTS/YYYY/MM-Mon/DD/ looking for subdirectories
    for year_dir in sorted(ARTIFACTS.iterdir()):
        if not year_dir.is_dir() or not re.match(r"\d{4}", year_dir.name):
            continue
        for month_dir in sorted(year_dir.iterdir()):
            if not month_dir.is_dir():
                continue
            for day_dir in sorted(month_dir.iterdir()):
                if not day_dir.is_dir() or not re.match(r"\d{2}", day_dir.name):
                    continue
                # Find all subdirectories inside this day folder
                for sub in sorted(day_dir.iterdir()):
                    if not sub.is_dir():
                        continue
                    # This is a source subdirectory — flatten it
                    for f in sorted(sub.rglob("*")):
                        if not f.is_file():
                            continue
                        dest = day_dir / f.name
                        rel_src = f.relative_to(ARTIFACTS)
                        rel_dst = dest.relative_to(ARTIFACTS)

                        if dest.exists():
                            print(f"  [SKIP] {rel_src} (destination exists)")
                            skipped += 1
                            continue

                        print(f"  {rel_src}")
                        print(f"    -> {rel_dst}")

                        if execute:
                            try:
                                shutil.move(str(f), str(dest))
                                moved += 1
                            except Exception as e:
                                print(f"    [ERROR] {e}")
                                errors += 1
                        else:
                            moved += 1

                    empty_dirs.add(sub)

    # Clean up empty source directories
    if execute:
        for d in sorted(empty_dirs, key=lambda p: len(str(p)), reverse=True):
            try:
                if d.exists():
                    shutil.rmtree(d)
                    print(f"  [cleanup] Removed: {d.relative_to(ARTIFACTS)}")
            except Exception as e:
                print(f"  [cleanup-err] {d.relative_to(ARTIFACTS)}: {e}")

    return moved, skipped, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    mode = "EXECUTE" if args.execute else "DRY RUN"
    print(f"[flatten] {mode}\n")

    # Phase 1: Fix malformed date directories
    print("--- Phase 1: Fix malformed date directories ---")
    fixed = fix_malformed_date_dirs(args.execute)
    print(f"  {fixed} malformed date dirs found\n")

    # Phase 2: Flatten source subdirectories
    print("--- Phase 2: Flatten source subdirectories ---")
    moved, skipped, errors = flatten_source_dirs(args.execute)

    print(f"\n[flatten] Done: {moved} moved, {skipped} skipped, {errors} errors, {fixed} date dirs fixed")
    if not args.execute:
        print("[flatten] Run with --execute to actually move files.")


if __name__ == "__main__":
    main()
