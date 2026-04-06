#!/usr/bin/env python3
"""
Servetus Inbox Filer
---------------------
Two-stage pipeline for filing a Hopper item into the vault.

STAGE 1 — process:
  Extracts content, creates 01-Records stub, prints text for LLM to work with.
  File stays in the Hopper. Record is created with pipeline_stage: staged.
  LLM fills in the record, extracts memories, links arcs.

STAGE 2 — finalize:
  Moves the original from Hopper → 00-Artifacts. This is the completion signal.
  Updates record pipeline_stage: staged → distilled.
  Hopper slot empties. Processing is done.

The move is always last. If a file is still in the Hopper, it is not done.

Usage:
    python3 10-System/inbox-file.py process <source-path> [options]
    python3 10-System/inbox-file.py finalize <source-path> [options]
    python3 10-System/inbox-file.py process <source-path> --dry-run

    --arc SLUG    Arc slug to link (repeatable, e.g. --arc the-inklings)
    --date        Override date YYYY-MM-DD (defaults to file mtime)
    --title       Human-readable title for the record
    --dry-run     Print what would happen without writing anything
"""

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
INBOX_ROOT = VAULT_ROOT.parent / "Inbox"

MONTH_NAMES = {
    1: "01-Jan", 2: "02-Feb", 3: "03-Mar", 4: "04-Apr",
    5: "05-May", 6: "06-Jun", 7: "07-Jul", 8: "08-Aug",
    9: "09-Sep", 10: "10-Oct", 11: "11-Nov", 12: "12-Dec",
}

def local_timezone_name() -> str:
    """Return the system's IANA timezone name (e.g. America/Chicago).
    Falls back to the UTC offset string if zone name is unavailable."""
    try:
        # macOS / Linux: read /etc/localtime symlink → zoneinfo path
        import os
        lt = os.readlink("/etc/localtime")
        if "zoneinfo/" in lt:
            return lt.split("zoneinfo/", 1)[1]
    except Exception:
        pass
    try:
        result = subprocess.check_output(
            ["timedatectl", "show", "--property=Timezone", "--value"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        if result:
            return result
    except Exception:
        pass
    # Final fallback: offset string e.g. "UTC-05:00"
    dt = datetime.now().astimezone()
    return dt.strftime("UTC%z")


LOCAL_TZ = local_timezone_name()

SOURCE_LABELS = {
    "otter.ai":  "otter",
    "otter":     "otter",
    "telegram":  "telegram",
    "claude":    "claude",
    "chatgpt":   "chatgpt",
    "apple":     "apple",
    "wispr":     "wispr",
    "photos":    "photos",
}

TEXT_EXTENSIONS  = {".md", ".txt", ".csv"}
DOCX_EXTENSIONS  = {".docx", ".doc"}
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac", ".aiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".webm"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def source_label(path: Path) -> str:
    parts = path.parts
    try:
        inbox_idx = next(
            i for i, p in enumerate(parts)
            if Path(*parts[:i + 1]) == INBOX_ROOT
        )
        folder = parts[inbox_idx + 1] if inbox_idx + 1 < len(parts) else "unknown"
    except StopIteration:
        folder = path.parent.name
    return SOURCE_LABELS.get(folder.lower(), folder.lower().replace(" ", "-"))


def file_date(path: Path, override: str = None) -> datetime:
    if override:
        return datetime.fromisoformat(override)
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).astimezone()


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text).strip('-')
    return text


def artifact_dest(dt: datetime, label: str, filename: str) -> Path:
    month   = MONTH_NAMES[dt.month]
    day_dir = dt.strftime("%Y-%m-%d")
    return VAULT_ROOT / "00-Artifacts" / str(dt.year) / month / day_dir / filename


def record_dest(dt: datetime, slug: str) -> Path:
    month    = MONTH_NAMES[dt.month]
    date_str = dt.strftime("%Y-%m-%d")
    return VAULT_ROOT / "01-Records" / str(dt.year) / month / f"{date_str}-{slug}_record.md"


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in TEXT_EXTENSIONS:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"[read error: {e}]"
    if ext in DOCX_EXTENSIONS:
        try:
            with zipfile.ZipFile(path) as z:
                xml  = z.read("word/document.xml").decode("utf-8")
                text = re.sub(r'<[^>]+>', ' ', xml)
                text = re.sub(r'\s+', ' ', text).strip()
                return text
        except Exception as e:
            return f"[docx extraction error: {e}]"
    if ext in AUDIO_EXTENSIONS:
        return "[audio — transcription required before content is available]"
    if ext in VIDEO_EXTENSIONS:
        return "[video — transcription required before content is available]"
    return "[binary or unsupported format — no text extraction]"


def _arc_links_yaml(arcs: list) -> str:
    if not arcs:
        return "  []"
    return "\n".join(f"  - [[05-Arcs/{a}_arc]]" for a in arcs)


def _arc_links_md(arcs: list) -> str:
    if not arcs:
        return "- (none — add arc links here)"
    return "\n".join(f"- [[05-Arcs/{a}_arc]]" for a in arcs)


def build_record(source_path: Path, artifact_path: Path, dt: datetime,
                 slug: str, title: str, arcs: list, label: str,
                 extracted_text: str, pipeline_stage: str = "staged",
                 detected_by: str = "turn") -> str:
    date_str     = dt.strftime("%Y-%m-%d")
    now          = datetime.now().astimezone()
    captured_at  = now.strftime("%Y-%m-%dT%H:%M:%S") + now.strftime("%z")
    # Seconds == :00 on a 5-minute boundary → automated/cron detection
    # Seconds != :00 → turn-triggered (human interaction)
    try:
        artifact_rel = artifact_path.relative_to(VAULT_ROOT)
    except ValueError:
        artifact_rel = artifact_path

    record_id_suffix = slug[:4].upper().replace('-', '')

    preview = extracted_text[:3000].strip()
    if len(extracted_text) > 3000:
        preview += "\n\n<!-- [truncated — full text in artifact] -->"

    return f"""---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: meta_dump
  pipeline_stage: {pipeline_stage}
  status: active
  intent: capture

identity:
  title: "{title}"
  slug: "{slug}"
  record_id: "SV-{dt.strftime('%Y%m%d')}-NOW-{record_id_suffix}"

time:
  created_at: "{date_str}"
  timezone: "{LOCAL_TZ}"
  source_range: "{date_str}"

source:
  label: "{label}"
  original_name: "{source_path.name}"
  artifact_path: "{artifact_rel}"
  captured_at: "{captured_at}"
  detected_by: "{detected_by}"

linked_arcs:
{_arc_links_yaml(arcs)}

keywords:
  - {label}
  - {slug}

tags:
  - servitus
  - record
  - {label}
---

# {title}

## Source
- **Original:** `{source_path.name}`
- **Label:** {label}
- **Artifact:** `[[{artifact_rel}]]`
- **Filed:** {date_str}

## Linked Arcs
{_arc_links_md(arcs)}

## Extracted Content

{preview}

## Memories
<!-- LLM: extract atomic notes here, then create linked files in 02-Memories/ -->

## Notes
<!-- Context, provenance, or filing decisions go here -->
"""


# ── Stage 1: process ──────────────────────────────────────────────────────────

def cmd_process(args):
    source = args.source.expanduser().resolve()
    if not source.exists():
        print(f"Error: file not found: {source}", file=sys.stderr)
        sys.exit(1)

    dt    = file_date(source, args.date)
    label = source_label(source)
    title = args.title or source.stem.replace("-", " ").replace("_", " ").title()
    slug  = slugify(args.title or source.stem)

    artifact_path = artifact_dest(dt, label, source.name)
    record_path   = record_dest(dt, slug)

    print(f"\n{'─' * 60}")
    print(f"  STAGE 1 — PROCESS")
    print(f"{'─' * 60}")
    print(f"  Source:      {source}")
    print(f"  Date:        {dt.strftime('%Y-%m-%d')}")
    print(f"  Label:       {label}")
    print(f"  Arcs:        {', '.join(args.arcs) if args.arcs else '(none)'}")
    print(f"  Record →     {record_path.relative_to(VAULT_ROOT)}")
    print(f"  Artifact →   {artifact_path.relative_to(VAULT_ROOT)}  [pending finalize]")

    if args.dry_run:
        print(f"\n  [DRY RUN] — nothing written.\n")
        return

    # Extract content
    text = extract_text(source)

    # Create 01-Records stub (pipeline_stage: staged — not done yet)
    if record_path.exists():
        print(f"\n  [skip] Record already exists: {record_path.relative_to(VAULT_ROOT)}")
    else:
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_content = build_record(
            source_path=source,
            artifact_path=artifact_path,
            dt=dt,
            slug=slug,
            title=title,
            arcs=args.arcs,
            label=label,
            extracted_text=text,
            pipeline_stage="staged",
            detected_by=args.detected_by,
        )
        record_path.write_text(record_content, encoding="utf-8")
        print(f"\n  [record]  → {record_path.relative_to(VAULT_ROOT)}")

    print(f"\n  File stays in Hopper until 'finalize' is called.")
    print(f"\n  Next steps for LLM:")
    print(f"    1. Review extracted content in the record above")
    print(f"    2. Write memories → 02-Memories/ with backlinks")
    print(f"    3. Fill in arc Sources sections")
    print(f"    4. Run: python3 10-System/inbox-file.py finalize '{source}'")
    print(f"\n{'─' * 60}\n")


# ── Stage 2: finalize ─────────────────────────────────────────────────────────

def cmd_finalize(args):
    source = args.source.expanduser().resolve()
    if not source.exists():
        print(f"Error: file not found: {source}", file=sys.stderr)
        sys.exit(1)

    dt    = file_date(source, args.date)
    label = source_label(source)
    slug  = slugify(args.title or source.stem) if args.title else slugify(source.stem)

    artifact_path = artifact_dest(dt, label, source.name)
    record_path   = record_dest(dt, slug)

    print(f"\n{'─' * 60}")
    print(f"  STAGE 2 — FINALIZE")
    print(f"{'─' * 60}")
    print(f"  Source:    {source}")
    print(f"  Artifact → {artifact_path.relative_to(VAULT_ROOT)}")

    if args.dry_run:
        print(f"\n  [DRY RUN] — nothing written.\n")
        return

    # Move original → 00-Artifacts (completion signal)
    if artifact_path.exists():
        print(f"\n  [skip] Artifact already exists — file may have already been finalized.")
    else:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), artifact_path)
        print(f"\n  [move]   → {artifact_path.relative_to(VAULT_ROOT)}")

    # Update pipeline_stage in record: staged → distilled
    if record_path.exists():
        text = record_path.read_text(encoding="utf-8")
        updated = text.replace("pipeline_stage: staged", "pipeline_stage: distilled", 1)
        if updated != text:
            record_path.write_text(updated, encoding="utf-8")
            print(f"  [record] pipeline_stage: staged → distilled")
        else:
            print(f"  [record] already distilled or stage not found")
    else:
        print(f"  [warn] Record not found — run 'process' first: {record_path}")

    print(f"\n  Hopper slot cleared. Processing complete.")
    print(f"\n{'─' * 60}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Servetus inbox filer — two-stage pipeline")
    sub    = parser.add_subparsers(dest="cmd", required=True)

    def add_common(p):
        p.add_argument("source", type=Path, help="Path to file in Hopper")
        p.add_argument("--arc", action="append", dest="arcs", default=[],
                       metavar="SLUG", help="Arc slug to link (repeatable)")
        p.add_argument("--date", default=None, help="Override date YYYY-MM-DD")
        p.add_argument("--title", default=None, help="Human title for the record")
        p.add_argument("--dry-run", action="store_true",
                       help="Print what would happen without writing anything")
        p.add_argument("--detected-by", default="turn", choices=["turn", "cron"],
                       help="How the file was detected: turn (interactive) or cron (automated)")

    add_common(sub.add_parser("process",  help="Stage 1: extract + create record stub"))
    add_common(sub.add_parser("finalize", help="Stage 2: move to 00-Artifacts (completion signal)"))

    args = parser.parse_args()

    if args.cmd == "process":
        cmd_process(args)
    elif args.cmd == "finalize":
        cmd_finalize(args)


if __name__ == "__main__":
    main()
