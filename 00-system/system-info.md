---
type: system
purpose: OS identity and status
---
[[]]
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
│                   USER INTERFACE                     │
│              (conversation / terminal)               │
├─────────────────────────────────────────────────────┤
│                      SHELL                           │
│           (Claude interprets commands)               │
├─────────────────────────────────────────────────────┤
│                     KERNEL                           │
│         (Claude processes instructions)              │
├──────────────────┬──────────────────────────────────┤
│   SYSTEM LIBS    │         USER SPACE               │
│    (Toolkit/)    │         (config/)                │
├──────────────────┴──────────────────────────────────┤
│                   FILE SYSTEM                        │
│  00-system/  01-witnesses/  02-daily-logs/ ...      │
├─────────────────────────────────────────────────────┤
│                  STORAGE LAYER                       │
│         (Obsidian vault on local disk)              │
└─────────────────────────────────────────────────────┘
```

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
| User config | `config/` |
| Preload script | `CLAUDE.md` |
