---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: spec
  pipeline_stage: canon
  status: draft
  intent: template

identity:
  title: "Witnesses Spec"
  slug: "witnesses-spec"
  record_id: "SV-20260202-NOW-CST-WITS"

time:
  created_at: "2026-02-02"
  timezone: "America/Chicago"
  source_range: "today"

keywords:
  - witnesses
  - ground-truth
  - artifacts
  - evidence

tags:
  - servitus
  - spec
  - witnesses
---

# Witnesses Spec

## Altitude
**Level 01** — Ground truth. Most zoomed in.

## Purpose
Witnesses are time-bound text representations of artifacts. They are the raw evidence layer — the closest thing to "what actually happened."

## Characteristics
- **Time envelope**: Defined by the largest artifact's span
- **Multi-artifact**: A witness can reference multiple artifacts
- **Device tracking**: Independent corroboration via device metadata
- **Validity scoring**: Artifact count, device count, coverage overlap

## When to Use
- Capturing raw evidence from a moment
- Documenting something that happened with artifacts to prove it
- Building the foundation for events, arcs, and storymaps

## Future: Artifact Separation
See [[S00.03-00-00-artifact-witness-architecture]] for planned separation of artifacts (raw files) from witnesses (metadata wrappers).

## Links / References
- [[S00.01-02-00-servetus-frontmatter-schema]]
- [[S00.03-00-00-artifact-witness-architecture]]
