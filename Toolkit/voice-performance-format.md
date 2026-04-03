---
type: spec
title: "Servetus Voice Performance Format (SVP)"
slug: "voice-performance-format"
status: active
version: 0.1
created: 2026-03-20
---

# Servetus Voice Performance Format (SVP)

> **Naming note (2026-03-22):** "Prosody" is the candidate name for the Servetus transcription engine. The word refers to the rhythm, stress, and intonation of speech — exactly what this pipeline captures. The alignment with SVP's design intent is not accidental.

The SVP is the notation system for how something was said, as distinct from what
was said. It is the performance layer of a transcript — the dynamics, rhythm, and
prosody that change the meaning of words entirely.

The model is sheet music. The transcript is the score. The SVP notation sits
directly beneath each line, the way expression marks sit under the staff. They
are inseparable. You cannot lift the melody off the page and leave the dynamics
behind.

---

## Design Principles

1. **Inseparable from the transcript** — SVP notation appears on the line
   immediately below the spoken text, not in a separate document.

2. **Human-readable at a glance** — a person reading the transcript two years
   from now should be able to feel the room without playing back the audio.

3. **Grounded in audio** — every notation is auditable against the source MP3.
   Nothing is invented; everything is interpretive but verifiable.

4. **RaP-informed, not RaP-bound** — RaP (Rhythm and Pitch) is the closest
   standardized system to what SVP requires. SVP borrows its vocabulary where
   it works and simplifies where academic precision exceeds readability.

5. **AuToBI as first pass** — automatic prosody annotation (AuToBI or Wav2ToBI)
   provides a mechanical first pass from the MP3. Human review corrects and
   enriches. Same multi-pass model as transcription.

---

## The Two-Stave Model

Every spoken turn has two staves:

```
## 00:04:23 — Mike Mazur
"I think we should move forward with the infrastructure decision."
*[340ms] · ↗think · steady · [1.2s] · ↘infra[stress]structure · trails ↘*
```

**Stave 1** — the transcript: words, speaker, timecode.
**Stave 2** — the SVP notation: timing, pitch direction, stress, register.

The timecode is the bar number. The speaker is the instrument. The words are
the notes. The SVP line is the expression marking.

---

## Notation Reference

### Timing
| Symbol | Meaning |
|--------|---------|
| `[10ms]` | Pause duration in milliseconds |
| `[1.2s]` | Pause duration in seconds |
| `[overlap]` | Speakers talking simultaneously |
| `[latch]` | Zero gap — next speaker starts immediately |

### Pitch Direction
| Symbol | Meaning |
|--------|---------|
| `↗word` | Rising pitch on word |
| `↘word` | Falling pitch on word |
| `→word` | Level/flat pitch |
| `↗↘word` | Rise then fall (circumflex) |
| `↘↗word` | Fall then rise |

### Stress and Emphasis
| Symbol | Meaning |
|--------|---------|
| `[stress]word` | Primary stress |
| `[soft]word` | Reduced/unstressed |
| `[drawn]word` | Lengthened vowel — drawn out |
| `[clipped]word` | Shortened — cut off |
| `[slide→]word` | Glides into word |

### Dynamics (borrowed from musical notation)
| Symbol | Meaning |
|--------|---------|
| `pp` | Very soft |
| `p` | Soft |
| `mp` | Medium soft |
| `mf` | Medium loud |
| `f` | Loud |
| `ff` | Very loud |
| `cresc` | Getting louder |
| `dim` | Getting softer |

### Register and Quality
| Symbol | Meaning |
|--------|---------|
| `[breathy]` | Breathy voice quality |
| `[tense]` | Tense/pressed voice |
| `[laugh]` | Laughing while speaking |
| `[trail]` | Trails off, incomplete |
| `[cut]` | Self-interrupted |
| `[restart]` | Abandoned and restarted |

### Interpretive (human reviewer only — not AuToBI)
| Symbol | Meaning |
|--------|---------|
| `[unsure]` | Hesitation suggests uncertainty |
| `[deflect]` | Redirecting away from topic |
| `[commit]` | Strong conviction in delivery |
| `[perform]` | Register shift — speaking for effect |

---

## Full Example

```markdown
## 00:04:23 — Mike Mazur
"I think we should move forward with the infrastructure decision."
*mp · ↗think · [340ms] · steady → · [1.2s] · ↘infra[stress]structure · [trail] ↘ · [unsure]*

## 00:04:51 — Christian Sass
"AJ needs to be in that conversation before we commit to anything."
*mf · [latch] · f[stress]AJ · [commit] · steady → · ↘anything*
```

---

## Call Artifact Package

The SVP transcript is one of five derivatives produced from a recorded call:

```
Recording.webm                    ← source artifact, never moved
├── contact-sheet.jpg             ← one frame per minute, visual scan of full call
├── audio.mp3                     ← audio extraction for transcription pipeline
├── attachments/                  ← anything shared in the Talk chat during the call
├── transcript-svp.md             ← what was said + how (this format)
└── summary.md                    ← call summary, decisions, action items, arc links
```

The contact sheet, MP3, and attachments are mechanical extractions.
The SVP transcript requires a human pass (after AuToBI first pass).
The summary is generated last, after the transcript is complete.

---

## Relationship to Standards

| System | Relationship |
|--------|-------------|
| **RaP** (Rhythm and Pitch) | Primary reference — perception-based, no spectrogram required, comparable accuracy to ToBI |
| **ToBI** | Too academic — requires spectrogram analysis, not human-readable at a glance |
| **AuToBI** | First-pass automation tool — generates initial pitch accent and boundary annotations from MP3 |
| **Wav2ToBI** | Alternative first-pass tool, newer approach |
| **Musical dynamics** | Borrowed directly — pp/p/mp/mf/f/ff are universally readable |

SVP is not a research tool. It is a human-readable performance record designed
to be read by a non-linguist years after the recording was made.

---

## Status

- [x] Conceptual model established
- [x] Two-stave architecture defined
- [x] Core notation vocabulary drafted
- [ ] AuToBI integration into extraction pipeline
- [ ] Validated against real transcript (BinaryRanch call 2026-03-18)
- [ ] RaP comparison — confirm symbol conflicts and resolve
- [ ] Obsidian rendering — confirm notation displays correctly
