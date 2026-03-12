---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "HDMI/NDI Latency — Blackmagic and NDI Bridge Tools"
  slug: "hdmi-ndi-blackmagic-latency-bridge"
  record_id: "SV-20250718-NOW-CST-NDI0"

time:
  created_at: "2025-07-18"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - ndi
  - hdmi
  - blackmagic
  - latency
  - sienna-ndi
  - versaport
  - live-production

tags:
  - chatgpt-import
  - production
  - gear
  - reference

origin:
  source_file: "2025-07-18-HDMI_to_NDI_Latency.md"
  source_url: "https://chatgpt.com/c/687a7b3b-4800-8007-8503-9f8c58b4e7fc"
---

# HDMI/NDI Latency — Blackmagic and NDI Bridge Tools

**Source:** 2025-07-18-HDMI_to_NDI_Latency.md
**Date:** 2025-07-18

## Summary

Partial audio session with a substantive text question: Does Blackmagic support NDI natively? Short answer: No. Bridge tools required.

## Blackmagic + NDI Status

**Blackmagic does NOT offer native NDI support** on their switchers or capture devices.

## Bridge Solutions (HDMI/SDI → NDI)

### Sienna NDI Source (macOS)
- Converts SDI/HDMI inputs from Blackmagic DeckLink / UltraStudio to NDI 6 output
- Single-channel; low latency (~just a few frames)
- Web interface; ~$99.99 USD

### Sienna NDI Source Multi (macOS/Linux/Windows)
- Multi-channel SDI/HDMI (DeckLink Duo 2, Quad 2, 8K Pro, etc.)
- Each input becomes individual NDI stream
- Scales to UHD/8K depending on hardware

## NDI → HDMI/SDI

"NDI Outlet" tools available (full specs in source file)

## Latency Note

Audio content also covered HDMI-to-NDI latency (audio stubs — no text). Topic likely relates to Seven Talents or Binary Ranch live production setup.

## Links / References

- Placement unconfirmed.
