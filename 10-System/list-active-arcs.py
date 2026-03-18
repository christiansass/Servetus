#!/usr/bin/env python3
"""Print titles of active arcs, one per line."""
import pathlib, re, sys

vault = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent
arcs_dir = vault / "05-Arcs"
if not arcs_dir.exists():
    sys.exit(0)
for f in sorted(arcs_dir.glob("*.md")):
    if f.name.startswith("_"):
        continue
    text = f.read_text(errors="replace")
    if not text.startswith("---"):
        continue
    end = text.find("\n---", 3)
    fm = text[3:end] if end != -1 else text[3:]
    sm = re.search(r'^\s*status:\s*(.+)$', fm, re.M)
    if sm and sm.group(1).strip().strip("'\"").lower() == "active":
        tm = re.search(r'^\s*title:\s*["\']?(.+?)["\']?\s*$', fm, re.M)
        print(tm.group(1).strip().strip("'\"") if tm else f.stem)
