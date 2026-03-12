---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Kinetic Text Web App — Directorial Script Presentation Tool"
  slug: "kinetic-text-web-app-concept"
  record_id: "SV-20250821-NOW-CST-KTX0"

time:
  created_at: "2025-08-21"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - kinetic-text
  - web-app
  - html-css
  - presentation
  - animation
  - audio-transcription
  - beat-mapping
  - directorial-script

tags:
  - chatgpt-import
  - creative
  - tech
  - production
  - content-creation

origin:
  source_file: "2025-08-21-Kinetic_Text_Web_App.md"
  source_url: "https://chatgpt.com/c/688cfc5f-96e0-8333-b82f-f479848c5d21"
---

# Kinetic Text Web App — Directorial Script Presentation Tool

**Source:** 2025-08-21-Kinetic_Text_Web_App.md
**Date:** 2025-08-21

## Summary

Concept and implementation session for a web app that turns a spoken/directed script into a cinematic kinetic text HTML presentation — fullscreen black background, white monospace text, self-animating with effects timed to the director's voice.

## Core Concept

User pastes a script, then records themselves "directing" it — speaking the timing, emphasis, pauses, and dramatic beats. The app:
1. Transcribes the direction
2. Maps timing cues and pauses
3. Generates a standalone HTML/CSS/JS kinetic text page that animates the script to match the spoken direction

## Workflow (Phase 1 Design)

### Input Screen
- Text area for script/copy
- Button to start audio recording for direction

### Audio Transcription + Beat Mapping
- Web Speech API or Whisper (server-side)
- Track pauses, inflections, pacing → timing and effects
- Generate "directorial script" structure

### Preview & Export
- Transform transcription into animated HTML/CSS/JS
- Cinematic effects: typewriter, glitch, dramatic emphasis, pause matching
- Export/copy final HTML code

## Reference File

- `bigtech_sucks_directing_notes.json` — referenced as input directing notes for a test run
- Script content: "Big tech sucks" theme; adversarial/provocative tone

## Aesthetic

- Fullscreen HTML
- Black background / white monospace text
- Types itself in real time
- Cinematic — matches spoken beat exactly (including silence as a beat)

## Links / References

- Placement unconfirmed.
- Strong Sastian/Binary Ranch content creation tool candidate.
