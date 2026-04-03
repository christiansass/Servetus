#!/usr/bin/env python3
"""
Servetus Migration Runner

Usage:
    python3 migrate.py                    # dry run — shows what would change
    python3 migrate.py --apply            # write changes to disk
    python3 migrate.py --path 02-Memories # scope to a subfolder
    python3 migrate.py --from-version 1   # only apply migrations from this version

No LLM. No network. Pure Python.
"""

import sys
import os
import re
import argparse
import importlib.util
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Run: pip3 install pyyaml")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
MIGRATIONS_DIR = Path(__file__).resolve().parent

# Current target schema version — increment with each major release
CURRENT_VERSION = 2

# Ordered list of (from_version, to_version, module_filename)
MIGRATIONS = [
    (1, 2, "v1_to_v2.py"),
]

# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)", re.DOTALL)


def parse_frontmatter(text: str) -> Tuple[Optional[Dict], str]:
    """Returns (frontmatter_dict, body). frontmatter is None if not present."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
        return fm, m.group(2)
    except yaml.YAMLError:
        return None, text


def render_frontmatter(fm: dict, body: str) -> str:
    """Serialize frontmatter back to a markdown string."""
    yaml_str = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_str}---\n{body}"


def get_schema_version(fm: dict) -> int:
    """Extract schema_version from frontmatter. Returns 0 if absent."""
    try:
        return int(fm.get("servitus", {}).get("schema_version", 0))
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# Migration loading
# ---------------------------------------------------------------------------

def load_migration(module_file: str):
    """Dynamically load a migration module by filename."""
    path = MIGRATIONS_DIR / module_file
    if not path.exists():
        raise FileNotFoundError(f"Migration module not found: {path}")
    spec = importlib.util.spec_from_file_location(module_file, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# File processing
# ---------------------------------------------------------------------------

def process_file(path: Path, apply: bool, from_version: int) -> Dict[str, Any]:
    """
    Process a single file. Returns a result dict with keys:
      status: "current" | "migrated" | "skipped" | "error"
      changes: list of change descriptions
      error: error message (if status == "error")
    """
    try:
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)

        if fm is None:
            return {"status": "skipped", "changes": [], "reason": "no frontmatter"}

        version = get_schema_version(fm)

        if version >= CURRENT_VERSION:
            return {"status": "current", "changes": []}

        if version < from_version:
            return {"status": "skipped", "changes": [], "reason": f"below --from-version {from_version}"}

        all_changes = []

        for (v_from, v_to, module_file) in MIGRATIONS:
            if version < v_to and version >= v_from:
                try:
                    mod = load_migration(module_file)
                    fm, body, changes = mod.up(fm, body)
                    all_changes.extend(changes)
                    version = v_to
                except Exception as e:
                    return {"status": "error", "changes": all_changes, "error": str(e)}

        if not all_changes:
            return {"status": "current", "changes": []}

        if apply:
            new_text = render_frontmatter(fm, body)
            # Atomic write
            dir_ = path.parent
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=dir_, delete=False, suffix=".tmp"
            ) as tmp:
                tmp.write(new_text)
                tmp_path = tmp.name
            os.replace(tmp_path, path)

        return {"status": "migrated", "changes": all_changes}

    except Exception as e:
        return {"status": "error", "changes": [], "error": str(e)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Servetus vault migration runner")
    parser.add_argument("--apply", action="store_true", help="Write changes to disk (default: dry run)")
    parser.add_argument("--path", default=None, help="Scope to a subfolder relative to vault root")
    parser.add_argument("--from-version", type=int, default=0, dest="from_version",
                        help="Only migrate files at or above this version")
    args = parser.parse_args()

    search_root = VAULT_ROOT
    if args.path:
        search_root = VAULT_ROOT / args.path
        if not search_root.exists():
            print(f"ERROR: Path not found: {search_root}")
            sys.exit(1)

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"\nServetus Migration Runner [{mode}]")
    print(f"Vault:   {VAULT_ROOT}")
    print(f"Scope:   {search_root}")
    print(f"Target:  schema_version {CURRENT_VERSION}")
    print()

    files = sorted(search_root.rglob("*.md"))

    counts = {"current": 0, "migrated": 0, "skipped": 0, "error": 0}
    migrated_files = []
    errors = []

    for path in files:
        result = process_file(path, apply=args.apply, from_version=args.from_version)
        status = result["status"]
        counts[status] += 1

        if status == "migrated":
            rel = path.relative_to(VAULT_ROOT)
            migrated_files.append((rel, result["changes"]))

        elif status == "error":
            rel = path.relative_to(VAULT_ROOT)
            errors.append((rel, result["error"]))

    # Report
    if migrated_files:
        verb = "Updated" if args.apply else "Would update"
        print(f"{verb} {len(migrated_files)} file(s):\n")
        for rel, changes in migrated_files:
            print(f"  {rel}")
            for change in changes:
                print(f"    + {change}")
        print()

    if errors:
        print(f"Errors ({len(errors)}):\n")
        for rel, err in errors:
            print(f"  {rel}: {err}")
        print()

    print(f"Summary: {counts['migrated']} to migrate  |  "
          f"{counts['current']} current  |  "
          f"{counts['skipped']} skipped  |  "
          f"{counts['error']} errors  |  "
          f"{len(files)} total")

    if not args.apply and counts["migrated"] > 0:
        print(f"\nRun with --apply to write changes.")

    if counts["error"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
