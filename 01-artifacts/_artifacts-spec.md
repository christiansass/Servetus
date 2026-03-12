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
**Level 01** — Ground truth. The tape.

## Purpose
Artifacts are raw evidence that something happened. They are the lowest layer of the hierarchy — uninterpreted, unedited, courtroom-clean. Everything above them is derived from them.

## Characteristics
- **Immutable**: Never edited after capture. Annotations go in linked memories, not the artifact itself.
- **Timestamped**: Date/time as precise as the source allows (EXIF, embedded metadata, filename, manual)
- **Origin-fingerprinted**: Machine, MAC, IP, OS recorded at time of capture
- **Terminal**: Nothing links below an artifact. It is the floor.

## Types
- Audio recordings (.m4a, .mp3, .wav)
- Video recordings (.mp4, .mov)
- Photos (.jpg, .png, .heic)
- Transcripts (.md, .txt)
- Screenshots
- Document exports (.pdf, .html)
- Session logs (Claude Code .jsonl → .md)

## Storage
- **Native**: Stored directly in `01-artifacts/YYYY/MM-MonthName/YYYY-MM-DD/`
- **Linked**: Binary stored in Nextcloud; artifact record is metadata + pointer

## When to Use
Every memory must have a source artifact. If you can't point to an artifact, the memory is subjective testimony — valid, but scored accordingly.

## Frontmatter
```yaml
---
type: artifact
title: "Description of what this is"
slug: "YYYY-MM-DD-description"
date: YYYY-MM-DDTHH:MM:SS-06:00

origin:
  machine: "MachineName"
  mac: "aa:bb:cc:dd:ee:ff"
  ip: "10.0.0.x"
  os: "macOS 15.x"

circles: []
published: false
tags: [artifact, session]
---
```

## Links / References
- [[_memories-spec]]
- [[S00.01-02-00-servetus-frontmatter-schema]]
