---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Silencing HVAC for Sound Stage / Studio Use"
  slug: "silencing-hvac-for-sound-stage-studio"
  record_id: "SV-20250712-NOW-CST-HVC0"

time:
  created_at: "2025-07-12"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - hvac
  - sound-stage
  - studio
  - acoustic-treatment
  - noise-reduction
  - silencer
  - ventilation

tags:
  - chatgpt-import
  - production
  - studio-build
  - reference

origin:
  source_file: "2025-07-12-Silencing_HVAC_for_Studios.md"
  source_url: "https://chatgpt.com/c/68720e9b-88c0-8007-b294-c9fbcda318e9"
---

# Silencing HVAC for Sound Stage / Studio Use

**Source:** 2025-07-12-Silencing_HVAC_for_Studios.md
**Date:** 2025-07-12

## Summary

Comprehensive guide to eliminating HVAC noise in a sound stage or studio environment. Three noise vectors: airflow noise, mechanical noise, vibration transmission.

## Option 1: Eliminate HVAC Use During Recording (Gold Standard)

- **HVAC kill switch** (wall plate or tablet control) — shut off during takes
- **Timed HVAC cycles**: cool/heat to temp, then shut off for recording window
- **Home Assistant / Crestron** automation to suspend HVAC during scheduled sessions

## Option 2: Design HVAC for Silent Operation (If Must Run)

### A. Low-Velocity Ducting
- Oversized ducts to reduce air velocity below **300 FPM**
- Duct liners (closed-cell acoustic foam)

### B. Sound Attenuators / Duct Silencers
- Acoustic baffles or mufflers in-line with duct runs
- **S-shaped labyrinth silencers** with fiberglass or perforated metal
- Brands: Kinetics Noise Control, Price Industries

### C. Decouple HVAC Equipment
- Vibration isolators and anti-vibration mounts
- Spring-loaded bases for air handlers
- Locate air handlers **outside** the acoustic envelope

### D. Mini-Splits
- Ductless mini-splits are quieter than central HVAC
- Some are near-silent; locate compressor outside

## Links / References

- Placement unconfirmed.
- See also: studio build notes (Oct 2025 — Binary Ranch LED wall studio session)
