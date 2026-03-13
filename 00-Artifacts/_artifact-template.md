---
type: artifact
title: "YYYY-MM-DD Description"
slug: "YYYY-MM-DD-slug"
date: YYYY-MM-DDTHH:MM:SS-06:00

origin:
  machine: ""
  mac: ""
  ip: ""
  os: ""

source_files:
  audio: "YYYY-MM-DD-slug.m4a"       # primary — delete if not present
  export: "YYYY-MM-DD-slug.docx"     # raw export — delete if not present

capture_pipeline:
  - tool: ""                          # wispr-flow | otter | apple | whisper-local
    trust: 0                          # -1 per external/cloud tool
pipeline_score: 0

circles: []
published: false
tags: [artifact]                      # add: audio | transcript | photo | session | export
---

## Transcript
<!-- Full transcript or description of artifact content -->

## Context
<!-- Where, when, who was present, what prompted this capture -->

## Processing Notes
- [ ] Audio retrieved
- [ ] Memories extracted → [[02-memories/]]
- [ ] Transcription quality reviewed
- [ ] Session complete (not cut off)
