---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: spec
  pipeline_stage: canon
  status: draft
  intent: template

identity:
  title: "Daily Logs Spec"
  slug: "daily-logs-spec"
  record_id: "SV-20260202-NOW-CST-DLGS"

time:
  created_at: "2026-02-02"
  timezone: "America/Chicago"
  source_range: "today"

keywords:
  - daily-logs
  - capture
  - stream
  - journal

tags:
  - servitus
  - spec
  - daily-logs
---

# Daily Logs Spec

## Altitude
**Level 02** — Daily capture stream.

## Purpose
Daily logs are the running capture of thoughts, sessions, and activities. They are the stream that feeds into higher-altitude structures.

## Characteristics
- **Date-stamped**: One log per day, or session exports within a day
- **Low friction**: Quick capture, minimal structure required
- **Source material**: Gets processed into events, projects, arcs later

## Naming Convention
```
YYYY-MM-DD--<slug>--<record_type>.md
```

Example:
```
2026-02-02--servetus-manifesto-session--thread-export.md
```

## When to Use
- Daily journaling
- Session exports from AI conversations
- Quick capture that needs a home
- Stream-of-consciousness that will be processed later

## Links / References
- [[S00.01-02-00-servetus-frontmatter-schema]]
- [[S00.01-01-00-servetus-export-rules]]
