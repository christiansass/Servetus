---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: spec
  pipeline_stage: canon
  status: draft
  intent: template

identity:
  title: "Events Spec"
  slug: "events-spec"
  record_id: "SV-20260202-NOW-CST-EVTS"

time:
  created_at: "2026-02-02"
  timezone: "America/Chicago"
  source_range: "today"

keywords:
  - events
  - moments
  - discrete
  - timeline

tags:
  - servitus
  - spec
  - events
---

# Events Spec

## Altitude
**Level 03** — Discrete moments.

## Purpose
Events are distinct, bounded moments in time. They aggregate witnesses and represent "something that happened" as a coherent unit.

## Characteristics
- **Time-bounded**: Clear start and end
- **Witness-backed**: References one or more witnesses as evidence
- **Discrete**: One event = one thing that happened
- **Connectable**: Can be linked to projects, arcs, storymap

## When to Use
- A meeting, conversation, or gathering
- A trip or outing
- A milestone or achievement
- Anything with a clear "this happened" boundary

## Structure
Events reference witnesses (evidence) and connect upward to arcs (narrative threads) and projects (work clusters).

```
Witnesses → Events → Arcs/Projects → Storymap
```

## Links / References
- [[S00.01-02-00-servetus-frontmatter-schema]]
- [[01-witnesses/_witnesses-spec]]
