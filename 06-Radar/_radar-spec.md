---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: spec
  pipeline_stage: canon
  status: draft
  intent: template

identity:
  title: "Radar Spec"
  slug: "radar-spec"
  record_id: "SV-20260202-NOW-CST-RADR"

time:
  created_at: "2026-02-02"
  timezone: "America/Chicago"
  source_range: "today"

keywords:
  - radar
  - awareness
  - tracking
  - attention

tags:
  - servitus
  - spec
  - radar
---

# Radar Spec

## Altitude
**Level 06** — Current situational awareness.

## Purpose
Radar is the attention layer. It tracks what's currently on your mind without requiring you to move or restructure content.

## Characteristics
- **Non-destructive**: Tag anything with `radar: active: true` without moving it
- **Situational**: What matters *right now*
- **Temporary**: Items come on and off radar as attention shifts
- **Cross-cutting**: Can track items from any altitude level

## Frontmatter Schema
```yaml
radar:
  active: true           # Is this on radar?
  added: "2026-02-02"    # When it hit radar
  reason: "Waiting on response"  # Brief context
```

## When to Use
- Waiting on someone/something
- Active decisions pending
- Items requiring follow-up
- Anything you need to "keep an eye on"

## View
The `06-radar/` folder can contain:
- Index of all radar-active items
- Filtered views by reason or date
- Radar history (what was tracked, when it resolved)

## Links / References
- [[S00.01-02-00-servetus-frontmatter-schema]]
