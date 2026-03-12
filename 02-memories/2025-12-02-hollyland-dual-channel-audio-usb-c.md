---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Hollyland Lark Max 2 — Dual Channel Audio via USB-C"
  slug: "hollyland-dual-channel-audio-usb-c"
  record_id: "SV-20251202-NOW-CST-HLD0"

time:
  created_at: "2025-12-02"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - hollyland
  - lark-max-2
  - dual-channel
  - usb-c
  - audio
  - wireless-mic

tags:
  - chatgpt-import
  - troubleshooting
  - audio
  - production

origin:
  source_file: "2025-12-02-Dual_channel_audio_USB-C.md"
  source_url: "https://chatgpt.com/c/692f0f35-22a0-8329-a34c-622d09d70930"
---

# Hollyland Lark Max 2 — Dual Channel Audio via USB-C

**Source:** 2025-12-02-Dual_channel_audio_USB-C.md
**Date:** 2025-12-02

## Summary

How to get dual-channel (separate L/R) audio from a Hollyland wireless mic system over USB-C, specifically the Lark Max 2.

## Confirmed: Lark Max 2 Supports Dual Channel via USB-C

- USB-C connection sends two discrete channels (Left = TX1, Right = TX2)
- Requires: receiver set to **Stereo mode**
- Hollyland defines Stereo = two separate audio tracks, one per channel

## Setup Steps

1. Power on TX1, TX2, and Camera RX
2. On Camera RX: **Settings → Channel Mode → Stereo**
3. Connect Camera RX to phone/PC via USB-C
4. In OS audio settings, select Hollyland receiver as input
5. Record/monitor — each mic isolated on L and R channels

## Gotchas

- **Safety Track does NOT work over USB-C** — only via 3.5mm TRS
- **Timecode disables Stereo** — can't have both simultaneously
- Computer sees receiver as: "Wireless Microphone RX"

## Links / References

- Placement unconfirmed.
