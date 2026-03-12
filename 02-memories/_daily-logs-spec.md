---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: spec
  pipeline_stage: canon
  status: active
  intent: reference

identity:
  title: "Daily Logs Spec"
  slug: "daily-logs-spec"
  record_id: "SV-20260202-NOW-CST-DLGS"

time:
  created_at: "2026-02-02"
  updated_at: "2026-03-01"
  timezone: "America/Chicago"

keywords:
  - daily-logs
  - atoms
  - atomic-layer
  - capture

tags:
  - servitus
  - spec
  - daily-logs
---

# Daily Logs Spec

## Altitude
**Level 02** — Atomic layer. One idea per file.

## Purpose

`02-daily-logs/` serves two functions in one flat folder:

1. **Atoms** — distilled concept notes extracted from witnesses. One idea, one file. The index card model.
2. **Session logs** — daily Obsidian notes and Servetus session records (`YYYY-MM-DD-servetus-log.md`).

This is the densest layer of the vault. Everything above it (events, projects, arcs, storymap) is built from atoms. Everything below it (witnesses) is the raw evidence those atoms were drawn from.

> *"I want only that idea in a stack of cards, and only this idea. Everything we said about this idea in its stack of cards... we atomize it, we split it up into its atomic structure."*

---

## The Atomic Model (Index Card)

Each atom:
- Captures **one idea, decision, concept, or insight**
- Has a `provenance` block linking back to its source witness
- Can stand alone and be understood without the witness
- Can link to related atoms via Obsidian `[[wikilinks]]`
- Has a `record_id` that makes it globally unique

Conversations weave in and out — topic A, B, C, back to A. Atomization untangles this and sorts everything into thematic buckets, each traceable to its source.

---

## Folder Structure

Flat. No subfolders. All files at root of `02-daily-logs/`.

```
02-daily-logs/
  _daily-logs-spec.md
  YYYY-MM-DD-servetus-log.md        ← session/daily log
  YYYY-MM-DD-slug.md                ← atom
  YYYY-MM-DD-slug.md                ← atom
  ...
```

---

## Naming Convention

```
YYYY-MM-DD-<slug>.md
```

- Date prefix: full ISO date with single dashes
- Slug: lowercase, hyphenated, descriptive of the concept
- No type suffix (type is declared in frontmatter `record_type`)
- Single dashes throughout — not double dashes

**Legacy naming** (pre-March 2026): Some files use `YYYY-MM-DD--slug--thread_export.md` with double dashes. These are valid but the convention has been normalized to single dashes.

---

## Record Types in this Folder

| `record_type` | Description |
|---------------|-------------|
| `concept` | A distilled idea or insight from a witness |
| `event` | A specific thing that happened (with timestamp context) |
| `daily_log` | The Servetus session log for a given day |
| `thread_export` | A processed ChatGPT or AI conversation export |
| `meta_dump` | A run log, processing record, or system note |

---

## Frontmatter Requirements (Atoms)

```yaml
---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: concept        # or event, thread_export, etc.
  pipeline_stage: distilled
  status: active
  intent: capture             # or reference

identity:
  title: "Human-readable title"
  slug: "YYYY-MM-DD-slug"
  record_id: "SV-YYYYMMDD-HHMM-TZ-CODE"

time:
  created_at: "YYYY-MM-DD"
  timezone: "America/Chicago"
  source_range: "session"     # or thread, today, etc.

keywords: [...]

tags:
  - servitus
  - <topic>

provenance:
  source_file: "01-witnesses/YYYY/MM-Month/YYYY-MM-DD/YYYY-MM-DD-slug.md"
  timestamp: "HH:MM:SS"       # timestamp within source where concept appears
  extracted: "YYYY-MM-DD"     # date atom was created
  arc: "[[arc-slug]]"         # optional, primary arc this atom belongs to
---
```

---

## Pipeline Stages for Files in This Folder

| `pipeline_stage` | Meaning |
|-----------------|---------|
| `inbox` | Processed but not yet placed — legacy status, being cleared |
| `distilled` | Placed and active — the normal state |
| `canon` | Spec or system file — authoritative, not subject to reprocessing |

---

## Relationship to Witnesses

Atoms are derived from witnesses. The `provenance.source_file` field creates the explicit link. An atom without a provenance link is orphaned — acceptable for some early imports but should be resolved over time.

The witness holds the full context. The atom holds the extracted meaning. Both are necessary.

---

## Relationship to Arcs

Atoms are indexed by arcs (`05-arcs/`). An arc lists the atoms relevant to its topic area. Atoms should be added to the relevant arc's `## Atoms in this Arc` section when created.

---

## Session Logs

`YYYY-MM-DD-servetus-log.md` files are the daily Servetus operating record. They follow a structured format:

1. **Raw Input** — unedited capture from the session
2. **Summary** — what happened
3. **Key Points** — decisions, findings, changes
4. **Events Detected** — discrete things that occurred
5. **Next Actions** — open items carried forward

Session logs are `record_type: daily_log`, not atoms. They document the system's own operation.

---

## Related Specs
- [[_witnesses-spec]] — the evidence layer atoms are drawn from
- [[_arcs-spec]] — arc index files that aggregate atoms
- [[_events-spec]] — events layer built from atoms
