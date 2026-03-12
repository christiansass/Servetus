---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "OtterAI WebM Support Complaint — AI Chatbot Case Study"
  slug: "otterai-webm-support-case-study"
  record_id: "SV-20250906-NOW-CST-OTR0"

time:
  created_at: "2025-09-06"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - otterai
  - webm
  - chatbot
  - customer-support
  - ai-integration
  - openproject
  - nextcloud
  - local-ai

tags:
  - chatgpt-import
  - binary-ranch
  - infrastructure
  - reference
  - content-creation

origin:
  source_file: "2025-09-06-AI_chatbot_integration_analysis.md"
  source_url: "https://chatgpt.com/c/68bc9585-b284-832c-b057-9d8b26853a9f"
---

# OtterAI WebM Support Complaint — AI Chatbot Case Study

**Source:** 2025-09-06-AI_chatbot_integration_analysis.md
**Date:** 2025-09-06

## Summary

Christian's frustrating conversation with OtterAI's support chatbot about WebM file format support — framed by Christian as a case study for what their own AI chatbot integrations should do better.

## The Problem

- OtterAI does not support WebM format for transcription import
- Supported formats: AVI, MOV, MPEG, MP4, WMV, MPG, MKV, M4P, 3GP (no WebM)
- Christian had been manually converting WebM files to MP4 to use Otter — unnecessary CPU overhead
- Nextcloud already supports WebM natively ("open source can do something you can't")
- OtterAI chatbot offered no useful solution; just repeated the supported formats list

## Design Insight (Key Framing)

> "This is a case study in what we should be able to do in our chatbots for our support — they should be directly tied into submitting tickets, going directly into OpenProject."

An effective support chatbot should:
1. Understand the feature gap being reported
2. Accept the request as a formal ticket/suggestion
3. Route it into a project management system (OpenProject in this case)
4. Acknowledge the user's effort and give a real resolution path

## Migration Context

- Plans to stop using OtterAI once local AI is installed on Binary Ranch infrastructure
- Nextcloud as the alternative platform for transcription and file handling

## Links / References

- Placement unconfirmed.
- See also: `2025-09-13--automator-webm-conversion-script-dropbox-pause` — the workaround script
