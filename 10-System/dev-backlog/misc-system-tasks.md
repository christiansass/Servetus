---
type: backlog
title: "Misc System Tasks"
slug: "misc-system-tasks"
status: open
priority: low
created: "2026-03-25"
circle: inner
---

# Misc System Tasks

Small items that don't warrant individual files yet.

| Task | Notes | Priority |
|------|-------|----------|
| **Vault migration** | `servetus migrate --apply` — only `02-Memories` migrated. Rest of vault still schema_version 1. | medium |
| **config/projects.md** | Still has placeholder names. Needs real project names. | low |
| **Anthropic API key** | Move from `nextcloud.env` to `~/.zshenv` or system keychain. | low |
| **docs/index.html** | Evidence-grade tagline + Jim Coler quote added. Modified but not committed. | low |
| **10-System/local/ folder** | Create gitignored, Nextcloud-synced folder for machine-specific scripts. Move `restart-wisprflow.sh` there. | low |
| **Machine fingerprint capture** | Extend `launch-brief.py` to collect MAC, Wi-Fi SSID, local IP, outbound IP, OS at session start. | medium |
| **Circle assignment for Talk rooms** | Tag each room in `config/talk-rooms.json` with trust circle. Disclosure spec written — needs application. | medium |
| **servetus user — Collectives write access** | Give servetus Nextcloud user write access to DEVOPS Manual. | low |
| **Verifiability score** | Add `verifiability` + `conflict_flag` to frontmatter schema. Define scoring weights. | medium |
| **Backlink audit** | Rename vault files to `subject_type.md` convention. Blocking ingestion. | medium |
| **Whisper queue requeue** | Requeue failed `core:audio2text` tasks via occ. 2-minute task. | low |
| **Architecture diagram** | Move from `Library/` to correct location. | low |
| **Double `---` in behavioral rules** | Lines 68-69 in `S00.01-04-00-servetus-behavioral-rules.md`. Minor cleanup. | low |
