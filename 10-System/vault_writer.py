#!/usr/bin/env python3
"""
vault_writer.py — Writes processed files into the Servetus vault.

Called after any file is processed — whether it arrived via:
  - NC Talk attachment (talk-webhook.py)
  - Hopper/inbox scan (inbox-triage.py)
  - Manual ingestion session

Two-tier write-back:
  Tier 1 — Artifact companion (.md in 00-Artifacts/ date hierarchy)
            Raw extracted text + full provenance. Evidence layer.
  Tier 2 — Memory note (.md in 02-Memories/, flat)
            Distilled content. Linked to witness + arc. Optional.

Artifact folder structure:
  00-Artifacts/YYYY/MM-Mon/DD/source/<original-file>
  00-Artifacts/YYYY/MM-Mon/DD/source/YYYY-MM-DD-<slug>.md

Caller provides:
  - ProcessedAttachment (from attachment_handler.py)
  - IngestionSource (who, where, when, surface)
"""

import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

VAULT_ROOT    = Path(__file__).parent.parent
ARTIFACTS_DIR = VAULT_ROOT / "00-Artifacts"
MEMORIES_DIR  = VAULT_ROOT / "02-Memories"
WITNESSES_DIR = VAULT_ROOT / "08-Witnesses"

MONTH_NAMES = {
    1: "01-Jan", 2: "02-Feb", 3: "03-Mar",  4: "04-Apr",
    5: "05-May", 6: "06-Jun", 7: "07-Jul",  8: "08-Aug",
    9: "09-Sep", 10: "10-Oct", 11: "11-Nov", 12: "12-Dec",
}


@dataclass
class IngestionSource:
    """Metadata about where the file came from."""
    surface: str              # "talk", "hopper", "manual"
    actor_id: str             # NC username or "csass"
    actor_display: str        # Human display name
    room_token: Optional[str] = None   # NC Talk room token (Talk surface only)
    room_name:  Optional[str] = None   # Room display name
    timestamp:  Optional[datetime] = None  # When received; defaults to now
    arc_hint:   Optional[str] = None   # Arc slug if known at call time

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class IngestionResult:
    artifact_dir:   Path
    artifact_file:  Optional[Path]   # The raw file (copied into vault)
    companion_md:   Path             # Companion .md in artifact folder
    memory_md:      Optional[Path]   # Memory note in 02-Memories/ (if written)
    slug:           str


# ── Path helpers ──────────────────────────────────────────────────────────────

def artifact_dir_for(dt: datetime, source_label: str = "") -> Path:
    """00-Artifacts/YYYY/MM-Mon/YYYY-MM-DD/"""
    month = MONTH_NAMES[dt.month]
    day_dir = dt.strftime("%Y-%m-%d")
    return ARTIFACTS_DIR / str(dt.year) / month / day_dir


def slugify(text: str, max_len: int = 40) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len]


def safe_filename(name: str) -> str:
    """Strip characters unsafe for filenames."""
    return re.sub(r'[<>:"/\\|?*]', "_", name)


# ── Frontmatter builders ──────────────────────────────────────────────────────

def _companion_frontmatter(slug: str, filename: str, source: IngestionSource,
                           mimetype: str, summary: str) -> str:
    ts    = source.timestamp.strftime("%Y-%m-%dT%H:%M:00-05:00")
    today = source.timestamp.strftime("%Y-%m-%d")
    rid   = f"SV-{today.replace('-','')}-NOW-CST-ARTF"

    room_line = ""
    if source.room_token:
        room_line = (
            f"\nsource:\n"
            f"  surface: {source.surface}\n"
            f"  actor_id: {source.actor_id}\n"
            f"  actor_display: \"{source.actor_display}\"\n"
            f"  room_token: {source.room_token}\n"
            f"  room_name: \"{source.room_name or source.room_token}\"\n"
        )
    else:
        room_line = (
            f"\nsource:\n"
            f"  surface: {source.surface}\n"
            f"  actor_id: {source.actor_id}\n"
            f"  actor_display: \"{source.actor_display}\"\n"
        )

    witness_link = f"\nlinked_witness: \"[[{source.actor_id}_witness]]\"\n" if source.actor_id else ""
    arc_link     = f"linked_arc: \"[[{source.arc_hint}_arc]]\"\n" if source.arc_hint else ""

    return f"""---
servitus:
  schema_version: 2
  system_version: 0.2.1
  record_type: artifact
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "{filename}"
  slug: "{slug}"
  record_id: "{rid}"

time:
  created_at: "{ts}"
  timezone: "America/Chicago"
  source_range: "today"

provenance:
  source_file: "{filename}"
  mimetype: "{mimetype}"
  summary: "{summary}"
{room_line}{witness_link}{arc_link}
tags:
  - servitus
  - artifact
  - {source.surface}
---

# {filename}

> {summary}

"""


def _memory_frontmatter(slug: str, title: str, source: IngestionSource,
                        artifact_slug: str) -> str:
    ts    = source.timestamp.strftime("%Y-%m-%dT%H:%M:00-05:00")
    today = source.timestamp.strftime("%Y-%m-%d")
    rid   = f"SV-{today.replace('-','')}-NOW-CST-MEMO"

    witness_block = (f'  - "[[{source.actor_id}_witness]]"' if source.actor_id else "  []")
    arc_block     = (f'  - "[[{source.arc_hint}_arc]]"'     if source.arc_hint  else "  []")

    return (
        "---\n"
        "servitus:\n"
        "  schema_version: 2\n"
        "  system_version: 0.2.1\n"
        "  record_type: concept\n"
        "  pipeline_stage: distilled\n"
        "  status: active\n"
        "  intent: capture\n"
        "\n"
        "identity:\n"
        f'  title: "{title}"\n'
        f'  slug: "{slug}"\n'
        f'  record_id: "{rid}"\n'
        "\n"
        "time:\n"
        f'  created_at: "{ts}"\n'
        '  timezone: "America/Chicago"\n'
        '  source_range: "today"\n'
        "\n"
        "linked_artifacts:\n"
        f'  - "[[{artifact_slug}]]"\n'
        "linked_witnesses:\n"
        f"{witness_block}\n"
        "linked_arcs:\n"
        f"{arc_block}\n"
        "\n"
        "tags:\n"
        "  - servetus\n"
        "  - memory\n"
        f"  - {source.surface}\n"
        "---\n\n"
    )


# ── Core write function ───────────────────────────────────────────────────────

def write_artifact(processed, source: IngestionSource,
                   write_memory: bool = True) -> IngestionResult:
    """
    Write a ProcessedAttachment into the vault.

    processed  — attachment_handler.ProcessedAttachment
    source     — IngestionSource metadata
    write_memory — whether to also write a 02-Memories/ note (default True)

    Returns IngestionResult with paths to what was written.
    """
    dt       = source.timestamp
    art_dir  = artifact_dir_for(dt)
    art_dir.mkdir(parents=True, exist_ok=True)
    MEMORIES_DIR.mkdir(parents=True, exist_ok=True)

    today    = dt.strftime("%Y-%m-%d")
    filename = safe_filename(processed.filename)
    base     = Path(filename).stem
    slug     = f"{today}-{slugify(base)}"

    # ── 1. Copy raw file into artifact folder ─────────────────────────────────
    src_path = Path(__file__).parent / "attachments" / filename
    artifact_file = None
    if src_path.exists():
        dest = art_dir / filename
        if not dest.exists():
            shutil.copy2(str(src_path), str(dest))
        artifact_file = dest

    # ── 2. Companion .md ──────────────────────────────────────────────────────
    companion_path = art_dir / f"{slug}.md"
    mimetype       = processed.media_type or "unknown"
    fm = _companion_frontmatter(slug, filename, source, mimetype, processed.summary)

    body = ""
    if processed.text:
        body = processed.text
    elif processed.image_data:
        body = f"*Image file — see {filename} in this folder.*"

    companion_path.write_text(fm + body)
    print(f"[vault] Artifact companion: {companion_path.relative_to(VAULT_ROOT)}")

    # ── 3. Memory note ────────────────────────────────────────────────────────
    memory_path = None
    if write_memory and processed.text and len(processed.text.strip()) > 50:
        mem_slug    = f"{today}-{slugify(base)}-memory"
        memory_path = MEMORIES_DIR / f"{mem_slug}.md"
        if not memory_path.exists():
            title     = f"{filename} — {source.actor_display}"
            mem_fm    = _memory_frontmatter(mem_slug, title, source, slug)
            # Truncate long content for the memory note — first 3000 chars
            excerpt   = (processed.text[:3000] + "\n\n*(truncated — full text in artifact)*"
                         if len(processed.text) > 3000 else processed.text)
            memory_path.write_text(mem_fm + f"## {filename}\n\n**Shared by:** {source.actor_display}"
                                   + (f"  \n**Via:** {source.room_name}" if source.room_name else "")
                                   + f"\n\n---\n\n{excerpt}\n")
            print(f"[vault] Memory note: {memory_path.relative_to(VAULT_ROOT)}")

    # ── 4. Update witness file with linked artifact ───────────────────────────
    _link_artifact_to_witness(source.actor_id, slug, filename, today)

    return IngestionResult(
        artifact_dir  = art_dir,
        artifact_file = artifact_file,
        companion_md  = companion_path,
        memory_md     = memory_path,
        slug          = slug,
    )


def _link_artifact_to_witness(actor_id: str, artifact_slug: str,
                               filename: str, today: str):
    """Add a linked_artifacts entry to the witness file if present."""
    if not actor_id or actor_id in ("csass", "servetus"):
        return
    witness_path = WITNESSES_DIR / f"{actor_id}_witness.md"
    if not witness_path.exists():
        return
    text = witness_path.read_text()

    # Add or append to linked_artifacts list in frontmatter
    artifact_ref = f"  - \"[[{artifact_slug}]]\""
    if artifact_slug in text:
        return  # Already linked

    if "linked_artifacts:" in text:
        text = text.replace(
            "linked_artifacts:",
            f"linked_artifacts:\n{artifact_ref}"
        )
    else:
        # Add before tags line
        text = text.replace(
            "\ntags:",
            f"\nlinked_artifacts:\n{artifact_ref}\n\ntags:"
        )
    witness_path.write_text(text)
    print(f"[vault] Linked artifact to witness: {actor_id}_witness.md")
