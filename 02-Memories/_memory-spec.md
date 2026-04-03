---
type: spec
title: Memories Spec
slug: memories-spec
date: 2026-03-12
circles: []
published: false
tags:
- spec
- memories
provenance:
  session_id: null
  session_jsonl: null
  session_jsonl_path: null
  extracted: null
---

# Memories Spec

## Altitude
**Level 02** — Atomic layer. One idea per file.

## Purpose

`02-memories/` serves two functions in one flat folder:

1. **Memories** — distilled concept notes extracted from artifacts. One idea, one file. The index card model.
2. **Session logs** — daily Obsidian notes and Servetus session records (`YYYY-MM-DD-servetus-log.md`).

This is the densest layer of the vault. Everything above it (events, projects, arcs, storymap) is built from memories. Everything below it (artifacts) is the raw evidence those memories were drawn from.

> *"I want only that idea in a stack of cards, and only this idea. Everything we said about this idea in its stack of cards... we atomize it, we split it up into its atomic structure."*

---

## The Atomic Model (Index Card)

Each memory:
- Captures **one idea, decision, concept, or insight**
- Has a `source_artifact` field linking back to its source artifact
- Can stand alone and be understood without the artifact
- Can link to related memories via Obsidian `[[wikilinks]]`
- Has a `slug` that makes it uniquely identifiable

Conversations weave in and out — topic A, B, C, back to A. Atomization untangles this and sorts everything into thematic buckets, each traceable to its source.

---

## Corroboration Score

Every memory carries a score — the number of independent artifacts and sources that support the same claim:

- **Score 1** — Testimony. One account. Handle with care.
- **Score 2** — Established. Two independent sources align.
- **Score 3+** — Confirmed. Geometrically solid.

A memory without a `source_artifact` is subjective testimony — valid, but scored accordingly (Score 1 by default).

---

## Folder Structure

Flat. No subfolders. All files at root of `02-memories/`.

```
02-memories/
  _memories-spec.md
  YYYY-MM-DD-servetus-log.md        ← session/daily log
  YYYY-MM-DD-slug.md                ← memory
  YYYY-MM-DD-slug.md                ← memory
  ...
```

---

## Naming Convention

```
YYYY-MM-DD-<slug>.md
```

- Date prefix: full ISO date with single dashes
- Slug: lowercase, hyphenated, descriptive of the concept
- No type suffix (type is declared in frontmatter `type`)
- Single dashes throughout — not double dashes

**Legacy naming** (pre-March 2026): Some files use `YYYY-MM-DD--slug--thread_export.md` with double dashes. These are valid but the convention has been normalized to single dashes.

---

## Record Types in this Folder

| `type` | Description |
|--------|-------------|
| `memory` | A distilled idea or insight from an artifact |
| `event` | A specific thing that happened (with timestamp context) |
| `session_log` | The Servetus session log for a given day |
| `thread_export` | A processed ChatGPT or AI conversation export |
| `meta_dump` | A run log, processing record, or system note |

---

## Frontmatter Requirements (Memories)

```yaml
---
type: memory
title: "One atomized thought"
slug: "YYYY-MM-DD-brief-description"
date: YYYY-MM-DD

source_artifact: "YYYY-MM-DD-artifact-slug.md"
source_offset: "00:12:30"   # timestamp within source (audio/video)
source_line: 47             # line number within source (transcripts)

linked_event: null
linked_project: null
linked_arc: null

circles: []
published: false
tags: [memory, <topic>]
---
```

---

## Pipeline Stages

| `pipeline_stage` | Meaning |
|-----------------|---------|
| `inbox` | Processed but not yet placed — legacy status, being cleared |
| `distilled` | Placed and active — the normal state |
| `canon` | Spec or system file — authoritative, not subject to reprocessing |

---

## Relationship to Artifacts

Memories are derived from artifacts. The `source_artifact` field creates the explicit link. A memory without a source link is orphaned — acceptable for some early imports but should be resolved over time.

The artifact holds the full context. The memory holds the extracted meaning. Both are necessary.

---

## Relationship to Arcs

Memories are indexed by arcs (`05-arcs/`). An arc lists the memories relevant to its topic area. Memories should be added to the relevant arc's `## Memories in this Arc` section when created.

---

## Session Logs

`YYYY-MM-DD-servetus-log.md` files are the daily Servetus operating record. They follow a structured format:

1. **Raw Input** — unedited capture from the session
2. **Summary** — what happened
3. **Key Points** — decisions, findings, changes
4. **Events Detected** — discrete things that occurred
5. **Next Actions** — open items carried forward

Session logs are `type: session_log`, not memories. They document the system's own operation.

---

## Related Specs
- [[_artifacts-spec]] — the evidence layer memories are drawn from
- [[03-events/_events-spec]] — events layer built from memories
- [[S00.01-02-00-servetus-frontmatter-schema]]
