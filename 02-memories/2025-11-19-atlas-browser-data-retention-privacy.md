---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Atlas Browser — Data Retention and Privacy Concerns"
  slug: "atlas-browser-data-retention-privacy"
  record_id: "SV-20251119-NOW-CST-ATL0"

time:
  created_at: "2025-11-19"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - atlas-browser
  - chromium
  - privacy
  - data-retention
  - form-filling
  - openai

tags:
  - chatgpt-import
  - research
  - privacy
  - tools

origin:
  source_file: "2025-11-19-Atlas_browser_data_retention.md"
  source_url: "https://chatgpt.com/c/691d3640-528c-8007-86f6-878f559406b5"
---

# Atlas Browser — Data Retention and Privacy Concerns

**Source:** 2025-11-19-Atlas_browser_data_retention.md
**Date:** 2025-11-19

## Summary

Research into whether Atlas Browser (Chromium-based, by OpenAI) retains data when filling out forms. Conclusion: unclear, and risks exist especially with AI features enabled.

## What Is Atlas Browser?

- Built on Chromium engine (behaves like Chrome underneath)
- AI features include "Smart Web Actions" — can fill out forms with one click
- **Browser Memories** feature: sends information about every page you visit to OpenAI's servers for processing (with filtering/deletion claims)

## Data Retention: What's Known

- Form import from other browsers: supported (passwords, bookmarks, etc.)
- "Fill out forms" = AI assistant fills them on your behalf if commanded
- **Not clearly documented**: whether unsubmitted form-input values are retained locally or sent for AI processing

## Risk Assessment (Practical)

- Assume: anything typed into Atlas, **especially with AI features enabled**, may be processed on OpenAI's side
- If Browser Memories is enabled: even browsing history is sent to servers
- For sensitive work (financial, medical, legal, production): treat Atlas like any cloud-connected AI tool

## Recommendation

- Disable Browser Memories for privacy-sensitive workflows
- Treat Atlas like a connected AI tool, not a private browser

## Links / References

- Placement unconfirmed.
