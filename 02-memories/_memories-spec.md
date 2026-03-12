---
type: spec
title: "Memories Spec"
slug: "memories-spec"
date: 2026-03-12

circles: []
published: false
tags: [spec, memories]
---

# Memories Spec

## Altitude
**Level 02** — Atomized thoughts extracted from artifacts.

## Purpose
Memories are the smallest unit of captured knowledge. One memory = one idea, one observation, one decision, one moment of insight. They are extracted from artifacts and organized upward into events, projects, and arcs.

## Characteristics
- **Atomic**: One memory = one thing. Split compound thoughts into separate memories.
- **Artifact-linked**: Every memory should point to a source artifact. Without one, it is subjective testimony — scored as Score 1.
- **Independent**: A memory doesn't have to belong to an event or project. It can stand alone.
- **Human-written**: The human writes memories. The machine helps organize them.

## Corroboration Score
- **Score 1** — One account. Testimony. Handle with care.
- **Score 2** — Two independent sources align. Established.
- **Score 3+** — Three or more independent sources. Confirmed.

## When to Use
- After listening to a recording: extract each distinct idea as a separate memory
- After a conversation: capture the key points while fresh
- A spontaneous thought you want to preserve
- Any claim you want to be able to trace back to evidence

## Frontmatter
```yaml
---
type: memory
title: "One atomized thought"
slug: "YYYY-MM-DD-brief-description"
date: YYYY-MM-DD

source_artifact: "YYYY-MM-DD-artifact-slug.md"
source_offset: "00:12:30"   # for audio/video
source_line: 47             # for transcripts

linked_event: null
linked_project: null
linked_arc: null

circles: []
published: false
tags: [memory]
---
```

## Links / References
- [[_artifacts-spec]]
- [[03-events/_events-spec]]
- [[S00.01-02-00-servetus-frontmatter-schema]]
