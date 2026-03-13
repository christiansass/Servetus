---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: method
  pipeline_stage: canon
  status: draft
  intent: template

identity:
  title: "Session Start (MVP)"
  slug: "session-start-mvp"
  record_id: "SV-20260116-NOW-CST-SESS"

time:
  created_at: "NOW"
  timezone: "America/Chicago"
  source_range: "today"

keywords:
  - session-start
  - checklist
  - mvp

tags:
  - servitus
  - session
  - mvp
---

# Session Start (MVP)

## Goal
Run a Servetus-friendly session and export vault-ready Markdown assets.

## Checklist
- Kit files present (authority + defaults + overrides)
- Spelling rules loaded (see spelling-rules spec)
- Timezone: America/Chicago
- Topic switching enabled

## Quick Commands (user phrases)
- "Servitus mode" → enable export behavior
- "export" → produce files only (FILENAME + markdown blocks)
- "new topic: <label>" → force a topic break with timestamp + suggested tags + sort suggestion

## GitHub Commit Notes (manual)
1) Create repo folder and add files.
2) Commit with a message like:
   - `feat: add Servetus Toolkit`

## Links / References
- [[bootloader]]
- [[export-rules]]
- [[frontmatter-schema]]
- [[time-rules]]
- [[spelling-rules]]
- [[topic-segmentation]]
- [[sorting-and-placement]]
- [[config/projects]]
- [[config/tags]]
- [[config/overrides]]
