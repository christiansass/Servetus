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
│  00-system/  01-artifacts/  02-memories/ ...      │
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

## Machines

### MacBook Pro (christiansass-macbook-pro)
- **Tailscale IP:** 100.120.83.63
- **Vault:** `~/Nextcloud/Obsidian/Servetus`
- **Engine:** Claude Code (primary)
- **Launcher:** `sc` → `launch-menu.py` → Claude Code

### WordInFilm (Linux Mint 22.3 — Elgin)
- **Tailscale IP:** 100.114.61.2
- **Vault:** `/mnt/Cloud/Nextcloud/Obsidian/Servetus`
- **Engine:** Ollama (local, default) + Claude Code (escalation / `@claude`)
- **Launcher:** `servetus` → `servetus_router.py`
- **GPU:** NVIDIA GTX 1080 Ti
- **Local model:** llama3.1:8b via Ollama

#### Security notes — WordInFilm
- `sastian` has passwordless sudo via `/etc/sudoers.d/sastian-nopasswd` — set 2026-04-02
  - Rationale: machine is on private Tailscale network; convenience for remote admin via Claude Code SSH
  - To revoke: `sudo rm /etc/sudoers.d/sastian-nopasswd`
- SSH public key for Claude Code remote access stored in `~/.ssh/authorized_keys` (key: `claude-code@macbook`)
  - To revoke: remove the `claude-code@macbook` line from `~/.ssh/authorized_keys`

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
