---
type: backlog
title: "Library Spec — Source vs Artifact, Intake Pipeline"
slug: "library-spec"
status: open
priority: medium
created: "2026-03-25"
circle: inner
---

# Library Spec

## What Library Is

`Library/` holds reference works created by others — books, papers, recordings.
Not artifacts (things Christian captured). Not memories (things distilled from processing).
Source material that validates research and enables local search.

Current contents:
- `lewis-cs/` — C.S. Lewis PDFs
- `tolkien-jrr/` — Tolkien PDFs
- `servetus-miguel/` — Miguel Servetus scholarship
- `wierwille-vpw/` — VPW works (to be added)
- `bullinger-etw/` — Bullinger's Figures of Speech (to be found and added)

## Intake Pipeline

Three stages per source:

1. **Source** (mp3, PDF, original file) → lives in Library under author folder
2. **Raw transcript** (Otter .docx/.txt) → lives alongside source in Library
3. **Processed document** (crosslinked .md) → filed to `02-Memories/` once refined

The processed .md is new work — Christian's contribution even when source is another's.

## VPW STS Recordings

Sunday Teaching Series — weekly recordings produced by The Way International.
Christian transcribed via Otter. Significant corpus.

Pipeline:
- Source mp3 → `Library/wierwille-vpw/sts/`
- Raw Otter transcript → alongside mp3
- Processed crosslinked .md → `02-Memories/` with scripture refs, concept links, date

## Sorting-and-Placement Update Needed

Add Library tier to `S00.01-01-20-servetus-sorting-and-placement-protocol.md`:

| Content Type | Destination |
|---|---|
| Reference works (books, papers) — not authored by Christian | `Library/<author>/` |
| Audio recordings by others | `Library/<author>/` |
| Raw transcripts of others' recordings | `Library/<author>/` alongside source |
| Processed/crosslinked .md derived from Library source | `02-Memories/` |

## Related

- [[S00.01-01-20-servetus-sorting-and-placement-protocol]]
- `10-System/dev-backlog/vpw-corpus-intake.md`
