---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: spec
  pipeline_stage: canon
  status: final
  intent: template

identity:
  title: "Servetus Topic Segmentation (MVP)"
  slug: "servetus-topic-segmentation-mvp"
  record_id: "SV-20260116-NOW-CST-TSEG"

time:
  created_at: "NOW"
  timezone: "America/Chicago"
  source_range: "today"

keywords:
  - topic-switch
  - segmentation
  - long-threads

tags:
  - servitus
  - topic-segmentation
  - export
---

# Servetus Topic Segmentation (MVP)

## Purpose
Detect topic switching and create clean breaks that can become separate assets.

## Explicit Topic Switch Triggers (highest priority)
If the user uses any explicit indicator of topic change, start a new topic section immediately:
- “new topic”
- “switching topics”
- “switching gears”
- “by the way”
- “another thing”
- “separate thought”
- “next”
- “back to X / moving on”
- any user-defined codeword meaning “topic switch”

## Required Header Format (topic switch marker)
When a topic switch is detected, insert this exact structure:

```markdown
## New Topic — <short descriptive label>
**Timestamp:** <YYYY-MM-DDTHH:MM America/Chicago>  
**Suggested Tags:** <tag1>, <tag2>, <tag3>  
**Sort Suggestion:** <project/topic guess OR inbox>  
**Confirm Placement?:** ☐ yes ☐ different ☐ decide later
