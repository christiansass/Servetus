---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "ATEM Mini Pro ISO — macOS HDMI Extended Display Flicker Fix"
  slug: "atem-mini-macos-hdmi-flicker-fix"
  record_id: "SV-20260204-NOW-CST-ATEM"

time:
  created_at: "2026-02-04"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - atem-mini
  - macos
  - hdmi
  - display
  - broadcast
  - edid
  - live-production

tags:
  - chatgpt-import
  - hardware
  - troubleshooting
  - production

origin:
  source_file: "2026-02-04-ATEM_Mini_macOS_Display_Issue.md"
  source_url: "https://chatgpt.com/c/69828eff-3168-8328-a1ee-87cf9f9d249d"
---

# ATEM Mini Pro ISO — macOS HDMI Extended Display Flicker Fix

**Source:** 2026-02-04-ATEM_Mini_macOS_Display_Issue.md
**Date:** 2026-02-04

## Summary

Mac connected to ATEM Mini Pro ISO via HDMI would flash for a moment and then drop. Root cause: macOS treating the ATEM as a monitor and failing the EDID/handshake. The ATEM only accepts broadcast formats, not native macOS display modes.

## Key Points

- **Root cause**: resolution/refresh/HDR/EDID mismatch — ATEM is not a display device, macOS negotiates against it like one
- **Critical clarification**: ATEM is an HDMI *input* device, not a monitor — use Mac as a camera feed source, not a display
- **Fix 1**: Set macOS to strict broadcast resolution before plugging in — 1920×1080, 60Hz (or 59.94), disable HDR, disable True Tone, disable auto-adjust
- **Fix 2**: Avoid USB-C hubs — use Apple USB-C → HDMI adapter or direct HDMI (Intel Mac); many hubs output non-broadcast timings
- **Fix 3**: Match ATEM video standard in ATEM Software Control → Settings → Video → 1080p60; reboot ATEM after changing
- **Fix 4**: Kill HDCP sources — no Netflix/Apple TV/protected video on screen during capture; test with desktop background or Keynote only
- **Fix 5 (pro)**: HDMI EDID emulator between Mac and ATEM — passive device that locks resolution and prevents renegotiation; common in live production rigs
- **Important**: Using ATEM as a monitor for the Mac will never work reliably — it is not designed for that

## Links / References

- Placement unconfirmed.
