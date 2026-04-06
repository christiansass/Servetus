#!/usr/bin/env python3
"""
rename-day-folders.py — Rename day folders from DD to YYYY-MM-DD.

Before: 00-Artifacts/2025/12-Dec/06/
After:  00-Artifacts/2025/12-Dec/2025-12-06/

Every folder becomes globally unique — no collision risk on flat sync.

Usage:
  python3 10-System/migrations/rename-day-folders.py           # dry run
  python3 10-System/migrations/rename-day-folders.py --execute  # do it
"""

import argparse
import json
import re
from pathlib import Path

VAULT_ROOT  = Path("/mnt/Cloud/Nextcloud/Obsidian/Servetus")
ARTIFACTS   = VAULT_ROOT / "00-Artifacts"
STATE_FILE  = VAULT_ROOT / "10-System" / ".transcription-queue-state.json"

# Reverse lookup: month dir name -> month number
MONTH_NUM = {
    "01-Jan": "01", "02-Feb": "02", "03-Mar": "03", "04-Apr": "04",
    "05-May": "05", "06-Jun": "06", "07-Jul": "07", "08-Aug": "08",
    "09-Sep": "09", "10-Oct": "10", "11-Nov": "11", "12-Dec": "12",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    mode = "EXECUTE" if args.execute else "DRY RUN"
    print(f"[rename-days] {mode}\n")

    renames = []  # (old_path, new_path)

    for year_dir in sorted(ARTIFACTS.iterdir()):
        if not year_dir.is_dir() or not re.match(r"\d{4}$", year_dir.name):
            continue
        year = year_dir.name
        for month_dir in sorted(year_dir.iterdir()):
            if not month_dir.is_dir() or month_dir.name not in MONTH_NUM:
                continue
            mm = MONTH_NUM[month_dir.name]
            for day_dir in sorted(month_dir.iterdir()):
                if not day_dir.is_dir():
                    continue
                # Skip if already in YYYY-MM-DD format
                if re.match(r"\d{4}-\d{2}-\d{2}$", day_dir.name):
                    continue
                # Match bare DD format
                if not re.match(r"\d{2}$", day_dir.name):
                    continue
                dd = day_dir.name
                new_name = f"{year}-{mm}-{dd}"
                new_path = month_dir / new_name
                renames.append((day_dir, new_path))

    if not renames:
        print("[rename-days] No day folders to rename.")
        return

    print(f"  {len(renames)} folders to rename\n")

    renamed = 0
    for old, new in renames:
        rel_old = old.relative_to(ARTIFACTS)
        rel_new = new.relative_to(ARTIFACTS)
        print(f"  {rel_old} -> {rel_new}")

        if args.execute:
            if new.exists():
                print(f"    [WARN] Destination exists, skipping")
                continue
            old.rename(new)
            renamed += 1

    # Update artifact paths in state file
    if args.execute and STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        processed = state.get("processed", state)
        updated = 0
        for key, info in processed.items():
            art = info.get("artifact", "")
            if not art:
                continue
            new_art = art
            for old, new in renames:
                old_rel = str(old.relative_to(VAULT_ROOT))
                new_rel = str(new.relative_to(VAULT_ROOT))
                if old_rel in new_art:
                    new_art = new_art.replace(old_rel, new_rel)
            if new_art != art:
                info["artifact"] = new_art
                updated += 1
        if updated:
            STATE_FILE.write_text(json.dumps(state, indent=2, default=str))
            print(f"\n  [state] Updated {updated} artifact paths")

    print(f"\n[rename-days] Done: {renamed if args.execute else len(renames)} renamed")
    if not args.execute:
        print("[rename-days] Run with --execute to actually rename.")


if __name__ == "__main__":
    main()
