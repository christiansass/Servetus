---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Obsidian Terminal Resizer Error 9009 (Windows/WSL)"
  slug: "obsidian-terminal-resizer-error-9009"
  record_id: "SV-20260211-NOW-CST-OTRE"

time:
  created_at: "2026-02-11"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - obsidian
  - terminal-resizer
  - error-9009
  - wsl
  - nodejs

tags:
  - chatgpt-import
  - obsidian
  - troubleshooting
  - windows
  - wsl

origin:
  source_file: "2026-02-11-Terminal_Resizer_Fix_OBS.md"
  source_url: "https://chatgpt.com/c/698bcc7c-9c68-8333-a651-8a09090123f6"
---

# Obsidian Terminal Resizer Error 9009 (Windows/WSL)

**Source:** 2026-02-11-Terminal_Resizer_Fix_OBS.md
**Date:** 2026-02-11

## Summary

The user encountered an Obsidian error "Terminal resizer exited unexpectedly: 9009" alongside "Cannot call write after a stream was destroyed." On Windows, error 9009 means a command was not found — the terminal resizer helper process could not be launched. The session covered troubleshooting steps focused on Node.js not being installed or not in PATH, WSL vault placement issues, and plugin reinstallation. The session appears to be from a Windows/WSL context, not the current Linux Mint machine.

## Key Points

- **Error 9009 on Windows** = command not found; Node.js most likely cause
- **Fix order (priority):**
  1. Verify `node -v` works in Windows PowerShell — if not, install Node LTS
  2. Verify `node -v` works inside WSL — install separately if needed
  3. Check Windows PATH includes Node install directory
  4. Reinstall the terminal plugin cleanly (delete from `.obsidian/plugins/`, reinstall)
  5. Run Obsidian as Administrator to test if it's a permissions issue
- **WSL vault warning:** If the vault lives inside the WSL filesystem (`\\wsl$\...`), terminal plugins often fail because Windows tries to spawn a process inside WSL and the stream gets destroyed — recommended fix is to keep vault on `C:\Users\...\Documents\`
- **Root cause (80% probability):** Node not installed in Windows PATH

## Open Items

- Session appears to be from a different machine/OS (Windows/WSL) — resolution status unknown

## Links / References

- Source: [[Inbox/ChatGPT/2026-02-11-Terminal_Resizer_Fix_OBS.md]]
- Placement unconfirmed.
