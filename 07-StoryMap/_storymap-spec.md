---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: spec
  pipeline_stage: canon
  status: draft
  intent: template

identity:
  title: "Storymap Spec"
  slug: "storymap-spec"
  record_id: "SV-20260202-NOW-CST-SMAP"

time:
  created_at: "2026-02-02"
  timezone: "America/Chicago"
  source_range: "today"

keywords:
  - storymap
  - overview
  - 30000ft
  - life-map

tags:
  - servitus
  - spec
  - storymap
---

# Storymap Spec

## Altitude
**Level 07** — 30,000ft view. Most zoomed out.

## Purpose
Storymap is the big picture. It's the view of your life from above — the shape of where you've been and where you're going.

## Characteristics
- **High-level**: Overview, not detail
- **Arc-backed**: Composed of narrative arcs
- **Temporal + Spatial**: Can be mapped by time and/or geography
- **Shareable surface**: The public-facing layer (see sharing model)

## When to Use
- Life review and reflection
- Seeing patterns across years
- Sharing your journey (selectively)
- Understanding the shape of your story

## The Privacy Pyramid
```
        ┌─────────────┐
        │  STORYMAP   │  ← Public surface (map outline)
        │  (shared)   │
        ├─────────────┤
        │   EVENTS    │  ← Selectively shareable
        ├─────────────┤
        │  WITNESSES  │  ← Private by default (ground truth)
        └─────────────┘
```

Storymap shows the shape without exposing the depth.

## Future: Social Layer
See [[S00.02-00-00-storymap-sharing-model]] for the planned interoperability and permission model.

## Links / References
- [[S00.02-00-00-storymap-sharing-model]]
- [[S00.03-00-00-artifact-witness-architecture]]
- [[05-arcs/_arcs-spec]]
