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
<<<<<<<< HEAD:Toolkit/S00.01-01-00-servetus-export-rules.md
- [[S00.01-02-00-servetus-frontmatter-schema]]

## Topic switching
Obey:
- [[S00.01-01-10-servetus-topic-segmentation]]

## Sorting prompt
Obey:
- [[S00.01-01-20-servetus-sorting-and-placement-protocol]]

## Spelling enforcement
Obey:
- [[S00.01-02-20-servetus-spelling-rules]]

## Time rules
Obey:
- [[S00.01-02-10-servetus-time-rules]]

## Links / References
- [[S00.01-00-00-servetus-bootloader]]
========
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
>>>>>>>> feature/servetus-ui:Toolkit/export-rules.md
