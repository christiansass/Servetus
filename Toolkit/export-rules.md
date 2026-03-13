---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: spec
  pipeline_stage: canon
  status: final
  intent: template

identity:
  title: "Servetus Export Rules (MVP)"
  slug: "servetus-export-rules-mvp"
  record_id: "SV-20260116-NOW-CST-EXPR"

time:
  created_at: "NOW"
  timezone: "America/Chicago"
  source_range: "today"

keywords:
  - export
  - obsidian
  - markdown
  - file-first

tags:
  - servitus
  - export
  - obsidian
  - markdown
---

# Servetus Export Rules (MVP)

## Purpose
Defines output constraints for Obsidian-ready exports.

## Export Output Format (hard rule)
When exporting, output ONLY:
1) `FILENAME: <name>.md`
2) one fenced code block labeled `markdown` containing the full file

No extra commentary unless explicitly requested.

## Filenames
Use the system naming grammar:
`S<version>-<priority>-<subpriority>-<descriptor>.md`

For exported content artifacts (non-kit), you may also use:
`YYYY-MM-DD--<slug>--<record_type>.md`
if the project prefers date-first organization.

Version tracking is handled in frontmatter (`system_version`), not filenames.

## Required Front Matter
All exported assets must follow:
- [[frontmatter-schema]]

## Topic switching
Obey:
- [[topic-segmentation]]

## Sorting prompt
Obey:
- [[sorting-and-placement]]

## Spelling enforcement
Obey:
- [[spelling-rules]]

## Time rules
Obey:
- [[time-rules]]

## Links / References
- [[bootloader]]
