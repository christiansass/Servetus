#!/usr/bin/env python3
"""
otter-import.py — Import Otter.ai transcriptions, skip redundant Whisper runs.

Scans Talk/Audio mp3s against the Otter.ai folder. When a matching .docx
transcription exists (by timestamp in the filename), this script:

  1. Extracts text from the Otter .docx
  2. Writes a vault artifact (same format as transcription-queue.py)
  3. Marks the file as "otter-imported" in the Whisper state file so the
     transcription queue daemon skips it
  4. Optionally moves the Talk/Audio mp3 to the artifact folder (--move-mp3)

Does NOT use an LLM. Pure Python file processing.

Usage:
  python3 10-System/otter-import.py                  # dry run (default)
  python3 10-System/otter-import.py --execute         # actually import
  python3 10-System/otter-import.py --execute --move-mp3  # import + relocate mp3s
"""

import argparse
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────

VAULT_ROOT   = Path("/mnt/Cloud/Nextcloud/Obsidian/Servetus")
ARTIFACTS    = VAULT_ROOT / "00-Artifacts"
TALK_AUDIO   = Path("/mnt/Cloud/Nextcloud/Talk/Audio")
OTTER_DIR    = Path("/mnt/Cloud/Nextcloud/Obsidian/Inbox/Otter.ai")
STATE_FILE   = VAULT_ROOT / "10-System" / ".transcription-queue-state.json"

MONTH_NAMES  = {
    1: "01-Jan", 2: "02-Feb", 3: "03-Mar", 4: "04-Apr",
    5: "05-May", 6: "06-Jun", 7: "07-Jul", 8: "08-Aug",
    9: "09-Sep", 10: "10-Oct", 11: "11-Nov", 12: "12-Dec",
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def extract_ts(name: str) -> str | None:
    """Extract 'YYYY-MM-DD HH-MM-SS' timestamp from a filename."""
    m = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}-\d{2}-\d{2})", name)
    return m.group(1) if m else None


def slugify(text: str, max_len: int = 50) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len]


def read_docx_text(docx_path: Path) -> str:
    """Extract plain text from a .docx file (no external deps)."""
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(docx_path) as z:
        xml_bytes = z.read("word/document.xml")
    root = ET.fromstring(xml_bytes)
    paragraphs = []
    for p in root.iter(f"{ns}p"):
        texts = [t.text for t in p.iter(f"{ns}t") if t.text]
        if texts:
            paragraphs.append("".join(texts))
    return "\n\n".join(paragraphs)


# ── Index Otter docx files by timestamp ──────────────────────────────────────

def build_otter_index() -> dict[str, Path]:
    """Map timestamp -> Otter .docx path."""
    index = {}
    for f in OTTER_DIR.glob("*.docx"):
        ts = extract_ts(f.name)
        if ts:
            index[ts] = f
    return index


# ── Artifact writer (matches transcription-queue.py format) ──────────────────

def recording_date(mp3_name: str) -> datetime | None:
    """Extract recording date from filename like 'Recording 2025-09-05 12-15-25.mp3'."""
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})\s+(\d{2})-(\d{2})-(\d{2})", mp3_name)
    if m:
        return datetime(int(m[1]), int(m[2]), int(m[3]),
                        int(m[4]), int(m[5]), int(m[6]))
    return None


def write_otter_artifact(mp3_name: str, otter_docx: Path, transcript: str,
                         now: datetime) -> Path:
    """Write an artifact .md file from an Otter transcription.
    Files by recording date (from filename), not import date."""
    dt      = recording_date(mp3_name) or now
    month   = MONTH_NAMES[dt.month]
    day_dir = dt.strftime("%Y-%m-%d")
    art_dir = ARTIFACTS / str(dt.year) / month / day_dir
    art_dir.mkdir(parents=True, exist_ok=True)

    rec_date = dt.strftime("%Y-%m-%d")
    ts_iso   = dt.strftime("%Y-%m-%dT%H:%M:00-05:00")
    slug     = slugify(Path(mp3_name).stem)
    rid      = f"SV-{rec_date.replace('-', '')}-{dt.strftime('%H%M')}-CST-OTTR"
    md_path = art_dir / f"{slug}.md"

    # Avoid collisions
    counter = 1
    while md_path.exists():
        counter += 1
        md_path = art_dir / f"{slug}-{counter}.md"

    frontmatter = f"""---
servitus:
  schema_version: 2
  system_version: 0.2.1
  record_type: artifact
  pipeline_stage: raw
  status: active
  intent: capture

identity:
  title: "{mp3_name}"
  slug: "{slug}"
  record_id: "{rid}"

time:
  created_at: "{ts_iso}"
  timezone: "America/Chicago"
  source_range: "today"

provenance:
  source_file: "{mp3_name}"
  mimetype: "audio/mpeg"
  transcribed_by: "Otter.ai (imported by otter-import.py)"
  otter_docx: "{otter_docx.name}"
  source_path: "{TALK_AUDIO / mp3_name}"
  imported_on: "{now.strftime('%Y-%m-%d')}"

tags:
  - servitus
  - artifact
  - otter
  - transcript
  - imported
---

# {mp3_name}

*Recorded {rec_date} — transcribed by Otter.ai, imported {now.strftime('%Y-%m-%d')} by otter-import.py*
*Original docx: {otter_docx.name}*

---

"""
    md_path.write_text(frontmatter + transcript)
    return md_path


# ── State file management ────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Import Otter.ai transcriptions for Talk/Audio mp3s")
    parser.add_argument("--execute", action="store_true",
                        help="Actually import (default is dry run)")
    parser.add_argument("--move-mp3", action="store_true",
                        help="Move mp3 from Talk/Audio to artifact folder after import")
    args = parser.parse_args()

    otter_index = build_otter_index()
    state = load_state()
    processed = state.setdefault("processed", {})
    now = datetime.now()

    # Find Talk/Audio mp3s that have Otter docx and are NOT yet in state
    # State keys are full paths, e.g. "/mnt/Cloud/Nextcloud/Talk/Audio/Recording ..."
    candidates = []
    for mp3 in sorted(TALK_AUDIO.glob("*.mp3")):
        key = str(mp3)
        if key in processed:
            continue  # already processed (by Whisper or previous import)
        ts = extract_ts(mp3.name)
        if ts and ts in otter_index:
            candidates.append((mp3, otter_index[ts]))

    if not candidates:
        print("[otter-import] No unprocessed Talk/Audio files with Otter matches.")
        return

    mode = "EXECUTE" if args.execute else "DRY RUN"
    print(f"[otter-import] {mode} — {len(candidates)} files to import\n")

    imported = 0
    errors = 0

    for mp3_path, docx_path in candidates:
        print(f"  {mp3_path.name}")
        print(f"    <- {docx_path.name}")

        if not args.execute:
            continue

        try:
            transcript = read_docx_text(docx_path)
            if not transcript.strip():
                print(f"    [WARN] Empty transcript in {docx_path.name}, skipping")
                errors += 1
                continue

            md_path = write_otter_artifact(mp3_path.name, docx_path, transcript, now)
            art_rel = str(md_path.relative_to(VAULT_ROOT))

            # Mark in state so Whisper queue skips this file
            # Keys must be full paths to match transcription-queue.py
            # Status "ok" is what the queue checks to skip files
            processed[str(mp3_path)] = {
                "status": "ok",
                "processed_at": now.isoformat(),
                "artifact": art_rel,
                "otter_docx": docx_path.name,
                "size_bytes": mp3_path.stat().st_size,
                "source": "otter-import",
            }
            save_state(state)

            print(f"    -> {art_rel}")

            if args.move_mp3:
                dest_dir = md_path.parent
                dest = dest_dir / mp3_path.name
                mp3_path.rename(dest)
                print(f"    [moved] {dest.relative_to(VAULT_ROOT)}")

            imported += 1

        except Exception as e:
            print(f"    [ERROR] {e}")
            errors += 1

    print(f"\n[otter-import] Done: {imported} imported, {errors} errors")
    if not args.execute:
        print(f"[otter-import] Run with --execute to actually import.")


if __name__ == "__main__":
    main()
