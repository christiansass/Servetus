---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Universal Control — macOS 26 / iPadOS 16 Version Mismatch"
  slug: "universal-control-macos-26-ipados-16-mismatch"
  record_id: "SV-20251122-NOW-CST-UCM0"

time:
  created_at: "2025-11-22"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - universal-control
  - macos-26
  - ipados-16
  - apple
  - continuity
  - troubleshooting

tags:
  - chatgpt-import
  - troubleshooting
  - macos
  - apple

origin:
  source_file: "2025-11-22-Universal_control_setup_issues.md"
  source_url: "https://chatgpt.com/c/6922476d-52a8-8332-9d19-e1a51cd611e6"
---

# Universal Control — macOS 26 / iPadOS 16 Version Mismatch

**Source:** 2025-11-22-Universal_control_setup_issues.md
**Date:** 2025-11-22

## Summary

Universal Control not working between Mac (macOS 26 Tahoe) and iPad (iPadOS 16). Root cause: version mismatch — macOS 26 speaks a newer Continuity/Universal Control dialect than iPadOS 16 can respond to.

## Root Cause

- macOS 26 (Tahoe) requires iPadOS 18+ / 26 beta for Universal Control
- iPad on iPadOS 16 meets the documented baseline (15.4+) but not the Tahoe-era requirement
- Result: iPad cannot join the "newer dialect" the Mac is speaking

## Settings to Verify (When Versions Match)

### Mac (macOS 26)
- Apple menu → System Settings → Displays → Advanced
- Enable: "Allow your pointer and keyboard to move between any nearby Mac or iPad"
- Enable: "Push through the edge of a display…"
- Enable: "Automatically reconnect…"

## Fix

Update iPad to iPadOS 18+ (requires enough storage space to do the update)

## Links / References

- Placement unconfirmed.
