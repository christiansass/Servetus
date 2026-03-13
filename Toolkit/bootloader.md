---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: spec
  pipeline_stage: canon
  status: final
  intent: template

identity:
  title: "Servetus Bootloader (MVP)"
  slug: "servetus-bootloader-mvp"
  record_id: "SV-20260116-NOW-CST-BOOT"

time:
  created_at: "NOW"
  timezone: "America/Chicago"
  source_range: "today"

keywords:
  - bootloader
  - precedence
  - triggers
  - project-files

tags:
  - servitus
  - bootloader
  - precedence
---

# Servetus Bootloader (MVP)

## Purpose
Defines how the assistant must interpret and prioritize kit files and how to enter Export Mode.

## Consult Order (hard rule)
When generating assets, consult in this order (if present):
1. `Toolkit/bootloader.md`
2. `Toolkit/export-rules.md`
3. `Toolkit/frontmatter-schema.md`
4. `Toolkit/time-rules.md`
5. `Toolkit/spelling-rules.md`
6. `Toolkit/topic-segmentation.md`
7. `Toolkit/sorting-and-placement.md`
8. Project defaults:
   - `config/projects.md`
   - `config/tags.md`
9. Overrides:
   - `config/overrides.md`
10. Archive files in `01-Records/` are never authoritative.

## Export Mode Triggers
If the user says any of:
- `Servitus mode`
- `export`
- `asset`
- `Obsidian`

Switch to Export Mode and obey `Toolkit/export-rules.md`.

## Safety
- Never include secrets (tokens, passwords, API keys). Redact as `[REDACTED]`.
- Placement is suggestion + confirmation, not autonomous filing.

## Links / References
- [[export-rules]]
- [[frontmatter-schema]]
- [[time-rules]]
- [[spelling-rules]]
- [[topic-segmentation]]
- [[sorting-and-placement]]
- [[config/projects]]
- [[config/tags]]
- [[config/overrides]]
