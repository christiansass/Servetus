---
type: spec
title: "Artifacts Spec"
slug: "artifacts-spec"
date: 2026-03-12

circles: []
published: false
tags: [spec, artifacts]
---

# Artifacts Spec

## Altitude
**Level 00** — Ground truth. Most zoomed in.

## Purpose

Artifacts are the immutable evidence layer. An artifact captures *what actually happened* — the raw file and its human-readable representation as a pair. Nothing in Servetus is more authoritative than an artifact. Everything above it (memories, events, arcs, storymap) is derived from artifacts.

> *"The audio file captures what text cannot: inflection, environment, organic thought. The transcript is the finding aid — it makes the audio searchable and atomic. Together as a pair they constitute an artifact — neither is complete without the other."*

---

## Folder Structure — Lightroom Model

Artifacts are stored in a date-based hierarchy modeled on how Lightroom organizes photo libraries:

```
00-Artifacts/
  YYYY/
    MM-MonthName/
      YYYY-MM-DD/
        YYYY-MM-DD-slug.md         ← transcript (finding aid)
        YYYY-MM-DD-slug.m4a        ← audio (primary artifact)
        YYYY-MM-DD-slug.docx       ← source export (when present)
```

Example:
```
00-Artifacts/
  2026/
    02-February/
      2026-02-28/
        2026-02-28-robotics-drive-home.md
        2026-02-28-robotics-drive-home.m4a
        2026-02-28-robotics-drive-home.docx
```

All three files share the same base filename. The folder is named with the full date.

---

## The Artifact Pair (and Triple)

### Minimum valid artifact
- `.md` transcript file with Servetus frontmatter

### Standard artifact pair
- `.m4a` audio file — the primary citizen; immutable ground truth
- `.md` transcript — the finding aid; makes audio searchable

### Extended triple (Otter.ai or similar export)
- `.m4a` audio
- `.docx` raw export (Otter.ai DOCX, verbatim as exported)
- `.md` processed transcript with Servetus frontmatter and formatting

The DOCX is kept for authenticity — it is the original unmodified export from the transcription service and forms part of the chain of custody.

---

## Audio-First Philosophy

Audio ranks above all other artifact formats:

| Format | Strength |
|--------|---------|
| Audio | Cannot be faked without detectable artifacts. Captures inflection, environment, pauses. Stands up in court. |
| Video | Audio is 50% of its value. Stronger than photo but large. |
| Photo | Timestamped, embedded context, but fakeable. |
| Text | Weakest. Anyone could have typed it. Requires author to affirm. |

The `.md` transcript is **not** the artifact — it is the finding aid for the audio. When the audio exists, it is the ground truth. When only text exists (e.g., a ChatGPT thread export), the text is the best available artifact.

---

## Naming Convention

```
YYYY-MM-DD-<slug>.<ext>
```

- Date prefix: full ISO date with single dashes
- Slug: lowercase, hyphenated, descriptive
- No type suffix in the filename (type is declared in frontmatter `type`)

---

## Immutability

Artifacts are never edited after capture. If an artifact contains an error (e.g., transcription mistake), the correction goes into a linked memory — not the artifact. The artifact is the record of what was captured, not a curated document.

---

## Origin Fingerprint

Every artifact record carries machine provenance at time of capture:

```yaml
origin:
  machine: "MachineName"
  mac: "aa:bb:cc:dd:ee:ff"
  ip: "10.0.0.x"
  os: "macOS 15.x"
```

This fingerprint establishes which machine captured the artifact and when — part of the chain of custody.

---

## Frontmatter Requirements

```yaml
---
type: artifact
title: "Human-readable title"
slug: "YYYY-MM-DD-slug"
date: YYYY-MM-DDTHH:MM:SS-06:00

origin:
  machine: "MachineName"
  mac: "aa:bb:cc:dd:ee:ff"
  ip: "10.0.0.x"
  os: "macOS 15.x"

circles: []
published: false
tags: [artifact, audio]   # or transcript, photo, session, etc.
---
```

---

## Ingestion Pipeline

```
Nextcloud/Obsidian/Inbox/<source>/     ← permanent originals, never touched
        ↓ Servetus COPIES (never moves)
00-Artifacts/YYYY/MM-Mon/DD/<source>/  ← evidence locker, original names
        ↓ Servetus processes
01-Records/YYYY/MM-Mon/                ← Markdown field record, provenance hash
        +
02-Memories/YYYY/MM-Mon/               ← atomic thoughts extracted
```

The original stays in the Inbox permanently. `00-Artifacts` is the vault's working copy. The `.md` record and extracted memories go up the altitude stack from there.

---

## Processing Notes Convention

Every artifact `.md` should include a `## Processing Notes` section at the bottom flagging:
- Whether audio has been retrieved
- Whether memories have been extracted (link to `02-Memories/`)
- Any transcription quality issues (misheard words, speaker misidentification)
- Whether the session was complete or cut off

---

## Related Specs
- [[02-Memories/_memory-spec]] — the atomic layer derived from artifacts
- [[Toolkit/frontmatter-schema]]
