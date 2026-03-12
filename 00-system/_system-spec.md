---
type: spec
title: "System Spec"
slug: "system-spec"
date: 2026-03-12

circles: []
published: false
tags: [spec, system]
---

# System Spec

## Altitude
**Level 00** — System. The operating layer beneath all content.

## Purpose

`00-system/` (to be renamed `10-system/` in a future migration) is the operational
infrastructure of the vault. It contains code, configuration, and system documentation
— not content. Nothing here is a memory, artifact, or record of events. It is the
engine that processes those things.

---

## Contents

```
00-system/
  VERSION                    ← Current system version (e.g. 0.2.2)
  system-info.md             ← Architecture overview and machine registry
  servetus_cli.py            ← CLI for creating logs and running commands
  session-close.py           ← Captures Claude Code session as artifact on exit
  voice/                     ← Voice capture and transcription pipeline
    capture.py               ← Record audio from microphone
    transcribe.py            ← Transcribe via local Whisper
    prosody.py               ← Prosodic analysis (pitch, pace, energy)
    witness.py               ← Write transcript as artifact record
    pipeline.py              ← Full voice → artifact pipeline
  nextcloud/                 ← Nextcloud integration adapter
    config.py                ← Sync path configuration
    webdav.py                ← WebDAV file operations
    talk.py                  ← Nextcloud Talk messaging
    archive.py               ← Session archival to Nextcloud
    nextcloud.yaml.example   ← Config template
```

---

## VERSION File

The single source of truth for the current system version. Read by Claude on boot.
Format: `MAJOR.MINOR.PATCH` on a single line.

---

## session-close.py

Runs automatically when `sc` (the Claude Code launcher) exits. Captures the
`.jsonl` session transcript from `~/.claude/projects/` and writes it as an
artifact to `00-inbox/` with full origin fingerprint (machine, MAC, IP, OS).

The session artifact is then processed manually: memories extracted, filed to
`01-artifacts/`, log moved to `02-memories/`.

---

## Voice Pipeline

The voice pipeline captures audio, transcribes locally (no cloud), and writes
a structured artifact with the SVP (Servetus Voice Performance) format.

- All processing happens locally — no audio leaves the device
- Whisper (CTranslate2) handles transcription
- Parselmouth handles prosodic analysis (optional)
- Output: `.m4a` audio + `.md` transcript in `00-inbox/`

See `Toolkit/S00.01-03-10-servetus-voice-pipeline*` for the full spec.

---

## Nextcloud Adapter

Provides WebDAV file sync, Nextcloud Talk messaging, and session archival.
Configured via `config/nextcloud.yaml` (gitignored).

---

## Planned Rename

`00-system/` will be renamed `10-system/` to reflect its correct position in the
altitude model — system infrastructure is the highest-altitude layer, not the lowest.
This rename requires coordinated path updates across:
- `session-close.py` (hardcoded paths)
- `servetus_cli.py`
- `Toolkit/` references
- `CLAUDE.md` / `templates/CLAUDE.md.example`
- `SETUP.md`

Not done until a migration script handles the path updates atomically.

---

## Related Specs
- `Toolkit/S00.01-03-10-servetus-voice-pipeline*` — voice pipeline spec
- `Toolkit/S00.01-04-00-servetus-talk-bot-service*` — talk bot spec
- `00-system/system-info.md` — architecture overview
