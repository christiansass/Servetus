---
type: spec
title: "Records Spec"
slug: "records-spec"
date: 2026-03-13

circles: []
published: false
tags: [spec, records]
---

# Records Spec

## Altitude
**Level 01** — Markdown field records. One step above raw evidence.

## Purpose

A Record is the **human-readable Markdown representation of an artifact**. It is not the artifact itself — the artifact is the original binary file (audio, photo, export) in `00-Artifacts/`. The Record is the finding aid: faithful transcription or description, Servetus frontmatter, and a provenance chain pointing back to the source.

If `00-Artifacts` is the evidence locker, `01-Records` is the case file.

---

## What Belongs Here

| Content | Belongs in 01-Records? |
|---------|----------------------|
| Faithful transcript of audio artifact | Yes |
| Field notes describing a photo | Yes |
| Formatted export of a session (Otter, Wispr, ChatGPT) | Yes |
| The original audio file | No — stays in 00-Artifacts |
| Atomized single thoughts | No — those go to 02-Memories |
| The original .docx export | No — stays in 00-Artifacts |

---

## Folder Structure

```
01-Records/
  YYYY/
    MM-Mon/
      YYYY-MM-DD-slug.md
```

One Markdown file per artifact. If an artifact has a supporting file (original audio, export), the record references it by filename — it does not copy it here.

---

## Relationship to 00-Artifacts

Every record points back to its source artifact via frontmatter:

```yaml
source_artifact: "YYYY-MM-DD-slug.m4a"
source_hash: "sha256:..."          # optional but recommended
source_offset: "00:12:30"          # for time-indexed references
```

The artifact is the ground truth. The record is never more authoritative than the artifact it describes. If the record contradicts the artifact, the artifact wins.

---

## Naming Convention

```
YYYY-MM-DD-<slug>.md
```

- Date is the artifact's capture date, not the processing date
- Slug matches the source artifact's slug where possible
- Single dashes throughout

---

## Frontmatter Requirements

```yaml
---
type: record
title: "Human-readable title"
slug: "YYYY-MM-DD-slug"
date: YYYY-MM-DDTHH:MM:SS-06:00

source_artifact: "YYYY-MM-DD-slug.m4a"
source_offset: null                  # or "HH:MM:SS" for time-indexed

linked_event: null
linked_project: null
linked_arc: null

circles: []
published: false
tags: [record]
---
```

---

## Faithfulness Rule

Records are **faithful transcriptions**, not curated documents. Do not:
- Correct speaker errors (note them in Processing Notes instead)
- Remove filler words unless they obscure meaning
- Add interpretation beyond what the source material contains

Interpretation belongs in `02-Memories/` as atomic thoughts — not in the record itself.

---

## Processing Notes Convention

Every record should include a `## Processing Notes` section:
- Source artifact location
- Transcription tool used and trust tier
- Any quality issues (misheard words, speaker misidentification, gaps)
- Whether memories have been extracted (link to `02-Memories/`)

---

## Related Specs
- [[00-Artifacts/_artifact-spec]] — the raw evidence this record describes
- [[02-Memories/_memory-spec]] — atomic thoughts extracted from records
- [[Toolkit/frontmatter-schema]] — full frontmatter reference
- [[Toolkit/sorting-and-placement]] — placement rules
