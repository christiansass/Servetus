---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Cassette Bluetooth Adapter — Delco Deck Eject Fix"
  slug: "cassette-adapter-eject-fix-delco-deck"
  record_id: "SV-20250803-NOW-CST-CST0"

time:
  created_at: "2025-08-03"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - cassette-adapter
  - bluetooth
  - delco
  - gm
  - tape-deck
  - auto-eject
  - car-audio

tags:
  - chatgpt-import
  - vehicles
  - reference
  - tech

origin:
  source_file: "2025-08-03-Cassette_adapter_eject_fix.md"
  source_url: "https://chatgpt.com/c/688f9342-1c10-8327-b699-7eebc973f34e"
---

# Cassette Bluetooth Adapter — Delco Deck Eject Fix

**Source:** 2025-08-03-Cassette_adapter_eject_fix.md
**Date:** 2025-08-03

## Summary

Troubleshooting a Bluetooth cassette adapter being automatically ejected by a GM/Delco Electronics factory tape deck (late '90s–early 2000s). Adapter itself works fine in other decks.

## Why It Happens

- Delco decks use **reel rotation sensors and tape tension detection**
- If spindles aren't rotating as expected, deck assumes jam → ejects
- Delco decks are notoriously sensitive to adapter reel resistance and head engagement signals

## Fixes & Workarounds

### 1. Add Spindle Resistance
- Open adapter; add a small rubber band or felt piece to the rotating gear
- Goal: increase drag to simulate real tape tension
- Caution: too much drag = real jam

### 2. Try a Different Brand
- Generic adapters often fail with Delco decks
- Recommended brands: **Sony**, **Reshow**, **Arsvita** — better compatibility with GM decks

### 3. Additional Options (in source file)
- Clean the tape deck heads
- Try adapter in different orientations (some decks are side-sensitive)
- Use FM transmitter as alternative

## Links / References

- Placement unconfirmed.
