---
type: system
purpose: OS identity and status
---

# Servetus System Info

## Identity
- **Name:** Servetus
- **Type:** Human-readable operating system for personal knowledge sovereignty
- **Kernel:** Claude (AI assistant as instruction processor)
- **Version file:** `00-system/VERSION`
- **Changelog:** `CHANGELOG.md`

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  I/O ADAPTERS                        │
│   CLI  │  Obsidian Plugin  │  NC Talk  │  Sys Tray  │
├─────────────────────────────────────────────────────┤
│                      SHELL                           │
│           (interprets commands via Toolkit)           │
├─────────────────────────────────────────────────────┤
│                     KERNEL                           │
│    (AI processes instructions — same interpreter)    │
├──────────────────┬──────────────────────────────────┤
│   SYSTEM LIBS    │         USER SPACE               │
│    (Toolkit/)    │         (config/)                │
├──────────────────┴──────────────────────────────────┤
│                   FILE SYSTEM                        │
│  00-system/  01-witnesses/  02-daily-logs/ ...      │
├─────────────────────────────────────────────────────┤
│         STORAGE + SYNC (trust-tiered)                │
│  Local disk ──→ Nextcloud (Sovereign)               │
│                 Git (Controlled/Public)               │
└─────────────────────────────────────────────────────┘
```

### I/O Adapters

The kernel is one interpreter. These are different mouths and ears:

| Adapter | Interface | Status | Code |
|---------|-----------|--------|------|
| **CLI** | Terminal commands | Active | `00-system/servetus_cli.py` |
| **Obsidian Plugin** | Vault UI + graph | Planned | — |
| **Nextcloud Talk** | Chat room listener | Scaffolded | `00-system/nextcloud/talk.py` |
| **System Tray** | Desktop assist tray | Planned | — |

All adapters share: same Toolkit specs, same vault filesystem, same kernel logic.
The adapter only handles I/O — receiving input and delivering output.

### Destination Trust Tiers

| Tier | Destination | Clearance |
|------|------------|-----------|
| **Sovereign** | Nextcloud / self-hosted | Everything |
| **Controlled** | Private Git repo | Code + specs only |
| **Public** | Public Git repo | Standards only |
| **Transient** | Ephemeral LLM session | Processing only |

## Query Commands

Ask Claude:
- "What version am I running?" → Reads VERSION, reports current release
- "What's new?" → Reads CHANGELOG.md, summarizes recent changes
- "System status" → Reports version, folder structure, config state
- "Help" → Lists available operations

## Version History

See `CHANGELOG.md` for full release notes.

## File Locations

| Component | Path |
|-----------|------|
| Version | `00-system/VERSION` |
| Changelog | `CHANGELOG.md` |
| System specs | `Toolkit/` |
| User config | `config/` (gitignored) |
| Preload script | `CLAUDE.md` |
| Voice pipeline | `00-system/voice/` |
| Nextcloud adapter | `00-system/nextcloud/` |
| NC config template | `00-system/nextcloud/nextcloud.yaml.example` |
