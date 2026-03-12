---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: spec
  pipeline_stage: canon
  status: active
  intent: reference

identity:
  title: "Witnesses Spec"
  slug: "witnesses-spec"
  record_id: "SV-20260202-NOW-CST-WITS"

time:
  created_at: "2026-02-02"
  updated_at: "2026-03-01"
  timezone: "America/Chicago"

keywords:
  - witnesses
  - ground-truth
  - artifacts
  - evidence
  - audio-first
  - lightroom

tags:
  - servitus
  - spec
  - witnesses
---

# Witnesses Spec

## Altitude
**Level 01** — Ground truth. Most zoomed in.

## Purpose

Witnesses are the immutable evidence layer. A witness captures *what actually happened* — the raw artifact and its human-readable representation as a pair. Nothing in Servetus is more authoritative than a witness. Everything above it (atoms, events, arcs, storymaps) is derived from witnesses.

> *"The audio file captures what text cannot: inflection, environment, organic thought. The transcript is the finding aid — it makes the audio searchable and atomic. Together as a pair they constitute a witness — neither is complete without the other."*

---

## Folder Structure — Lightroom Model

Witnesses are stored in a date-based hierarchy modeled on how Lightroom organizes photo libraries:

```
01-witnesses/
  YYYY/
    MM-MonthName/
      YYYY-MM-DD/
        YYYY-MM-DD-slug.md         ← transcript (finding aid)
        YYYY-MM-DD-slug.m4a        ← audio (primary artifact)
        YYYY-MM-DD-slug.docx       ← source export (when present)
```

Example:
```
01-witnesses/
  2026/
    02-February/
      2026-02-28/
        2026-02-28-robotics-drive-home.md
        2026-02-28-robotics-drive-home.m4a
        2026-02-28-robotics-drive-home.docx
```

All three files share the same base filename. The folder is named with the full date.

---

## The Witness Pair (and Triple)

### Minimum valid witness
- `.md` transcript file with Servetus frontmatter

### Standard witness pair
- `.m4a` audio file — the primary citizen; immutable ground truth
- `.md` transcript — the finding aid; makes audio searchable

### Extended triple (Otter.ai or similar export)
- `.m4a` audio
- `.docx` raw export (Otter.ai DOCX, verbatim as exported)
- `.md` processed transcript with Servetus frontmatter and formatting

The DOCX is kept for authenticity — it is the original unmodified export from the transcription service and forms part of the chain of custody.

---

## Audio-First Philosophy

Audio ranks above all other witness formats:

| Format | Strength |
|--------|---------|
| Audio | Cannot be faked without detectable artifacts. Captures inflection, environment, pauses. Stands up in court. |
| Video | Audio is 50% of its value. Stronger than photo but large. |
| Photo | Timestamped, embedded context, but fakeable. |
| Text | Weakest. Anyone could have typed it. Requires author to affirm. |

The `.md` transcript is **not** the witness — it is the finding aid for the audio. When the audio exists, it is the ground truth. When only text exists (e.g., a ChatGPT thread export), the text is the best available artifact.

---

## Naming Convention

```
YYYY-MM-DD-<slug>.<ext>
```

- Date prefix: full ISO date with single dashes
- Slug: lowercase, hyphenated, descriptive
- No type suffix in the filename (type is declared in frontmatter `record_type`)

---

## Frontmatter Requirements

```yaml
---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: witness
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Human-readable title"
  slug: "YYYY-MM-DD-slug"
  record_id: "SV-YYYYMMDD-HHMM-TZ-CODE"

time:
  created_at: "YYYY-MM-DD"
  timezone: "America/Chicago"
  source_range: "duration or range"

provenance:
  audio_file: "YYYY-MM-DD-slug.m4a"   # when audio exists
  docx_file: "YYYY-MM-DD-slug.docx"   # when source export exists
  recorded_at: "YYYY-MM-DD HH:MM"
  location: "description"             # optional

keywords: [...]
tags: [...]
---
```

---

## Ingestion Pipeline

Files land in `Obsidian/Inbox/Otter.ai/` (the drop zone). After processing:

1. `.docx` is extracted → text extracted → `.md` witness written
2. Atoms extracted → written to `02-daily-logs/`
3. All three files (`.docx`, `.m4a`, `.md`) move to `01-witnesses/YYYY/MM-Month/YYYY-MM-DD/`
4. Inbox drop zone is cleared

Audio (`.m4a`) is retrieved separately from Otter.ai (requires API or manual download) and added to the witness folder once available.

---

## Processing Notes Convention

Every witness `.md` should include a `## Processing Notes` section at the bottom flagging:
- Whether audio has been retrieved
- Whether atoms have been extracted (link to `02-daily-logs/`)
- Any transcription quality issues (misheard words, speaker misidentification)
- Whether the session was complete or cut off

---

## Related Specs
- [[_daily-logs-spec]] — the atomic layer derived from witnesses
- [[_arcs-spec]] — arc index files that aggregate atoms
