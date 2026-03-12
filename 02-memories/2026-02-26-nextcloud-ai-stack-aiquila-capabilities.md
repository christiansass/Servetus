---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Nextcloud AI Stack — AIquila Capabilities and Talk Transcription"
  slug: "nextcloud-ai-stack-aiquila-capabilities"
  record_id: "SV-20260226-NOW-CST-NCAI"

time:
  created_at: "2026-02-26"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - nextcloud
  - aiquila
  - talk-transcription
  - whisper
  - ai-stack

tags:
  - chatgpt-import
  - infrastructure
  - nextcloud
  - ai
  - sovereignty

origin:
  source_file: "2026-02-26-Aquila_API_Key_Error.md"
  source_url: "https://chatgpt.com/c/699fc3f8-9d54-8331-b478-c96d62245574"
---

# Nextcloud AI Stack — AIquila Capabilities and Talk Transcription

**Source:** 2026-02-26-Aquila_API_Key_Error.md
**Date:** 2026-02-26

## Summary

After getting AIquila connected (see companion note on the stopReason error), the user found it underwhelming — it does not feel like a chat interface and did not produce Talk transcriptions. This note captures the architectural explanation of what AIquila actually does and what separate components are needed for transcription and Talk summaries in Nextcloud.

## Key Points

**What AIquila is (and isn't):**
- AIquila is an AI *backend service provider* — other Nextcloud apps hook into it
- It is NOT a user-facing chat assistant or interface
- Without other apps wired to it, it appears to "do nothing"
- It can power: Files summaries, Text app rewriting, Talk message summaries, Mail reply drafting, Workflow automation/classification

**Why Talk transcription requires a separate app:**
- Transcription (speech-to-text) needs a dedicated STT provider app
- **Local Whisper Speech-To-Text** (`stt_whisper2`) — runs Whisper on-server; CPU-heavy; transcription backend for Assistant/Talk
- **Live Transcription** (`live_transcription`, based on Vosk) — alternative for live Talk transcription
- AIquila alone will not transcribe anything regardless of configuration

**Why Talk message summaries require another app:**
- Talk chat summaries use the **Summary Bot** app, which calls registered LLM providers
- Summary Bot is not the same as AIquila unless AIquila is specifically registered as the LLM provider in the way Summary Bot expects
- Must install Summary Bot separately, then configure it against an LLM provider

**Practical checklist for transcription:**
1. Install `stt_whisper2` (or Vosk live transcription)
2. Enable in Administration → AI/Assistant
3. For recorded call transcription, enable via `occ` settings
4. For chat summaries: install Summary Bot, configure LLM provider

**Assessment for Binary Ranch / Ops_SevenTalents context:**
- AIquila is worth keeping IF: auto-summarizing internal docs, classifying uploads, workflow automation, AI as part of sovereign infra experiment
- Not compelling if: just want a chat UI, not using Nextcloud Text/Talk heavily, don't need automated processing

## Open Items

- Nextcloud version not confirmed (28/29/30 affects which apps are available)
- Whether `stt_whisper2` was installed was not confirmed in session
- Uninstall decision deferred ("give it a day")

## Links / References

- Companion: [[2026-02-26--aiquila-stopreason-api-error-fix--thread_export]]
- Source: [[Inbox/ChatGPT/2026-02-26-Aquila_API_Key_Error.md]]
- Placement unconfirmed.
