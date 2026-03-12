---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: concept
  pipeline_stage: distilled
  status: active
  intent: reference

identity:
  title: "Frontal Cortex — Session Awareness and Orchestration Design"
  slug: "2026-03-02-frontal-cortex-design-notes"
  record_id: "SV-20260302-1555-CST-FC01"

time:
  created_at: "2026-03-02"
  timezone: "America/Chicago"
  source_range: "session"

keywords:
  - frontal-cortex
  - session-awareness
  - orchestration
  - process-table
  - radar
  - time-awareness
  - multi-session
  - voice-interface

tags:
  - servitus
  - servetus-vision
  - architecture
  - frontal-cortex
  - orchestration

provenance:
  source_file: "Claude Code CLI session transcript"
  timestamp: "2026-03-02 15:55 CST"
  extracted: "2026-03-02"
  arc: "[[arc-storymap]]"
---

# Frontal Cortex — Session Awareness and Orchestration Design

Captured March 2, 2026 from a Claude Code CLI session. These are design notes from Christian Sass — not a spec yet, but the architectural thinking that a spec will be built from.

---

## The Problem

Multiple Claude sessions can run concurrently against the same Servetus vault. Without shared awareness:
- One session makes architecture decisions, another runs with old rules
- Files get placed in the wrong location
- No session knows what any other session is doing or has done
- Time gaps between interactions are invisible — the system can't tell "5 seconds" from "15 hours"

**Proven by:** The March 1-2 session where one Claude instance followed outdated sorting rules while another was establishing new ones.

---

## The Concept: Frontal Cortex

The frontal cortex is the **executive function layer** for Servetus. It provides:

1. **Session registry** — what sessions are active right now
2. **Session history** — what happened in the last N sessions
3. **Time awareness** — understanding the passage of time between interactions
4. **Radar feed** — world/system context gathered during gaps
5. **Traffic control** — preventing conflicts between concurrent sessions

It lives in the file system (because everything in Servetus lives in the file system):

```
00-system/
  active-sessions.md      ← the process table
```

---

## Process Table — Active Sessions

Before any session does work, it:

1. **Checks in** — registers itself (who, when, what it's doing)
2. **Reads the table** — sees every other active session and what files they're touching
3. **Claims work** — locks files/folders it's about to process
4. **Proceeds with awareness** — makes decisions with full system state

When a session ends, it clears its entry and writes a summary to the history.

---

## Session History — Recent Context

Not just active sessions — the last N completed sessions, tagged, with:
- Start/end timestamps
- What arcs/topics were touched
- What files were created or modified
- What decisions were made that affect future sessions
- Tags (e.g., `ingestion`, `architecture`, `linux`, `spec-update`)

How far back? Keep all of it (it's just text), but only load the last 5-10 into active context. The radar determines the window.

The daily logs are the long-form session history. The process table is the compact, machine-readable index that points into them.

---

## Time Awareness

The system must understand contextually what's happening with time. Every user message should be timestamped. The gap between messages IS information:

- 30-second gap → still mid-thought
- 30-minute gap → stepped away, came back
- 15-hour gap → slept, lived life, came back with a different headspace

**The gap is the trigger.** Gap length determines how much re-orientation is needed.

---

## Interaction Cadence — The Anti-Alexa Pattern

> *"Everything needs to be relevant and permissions-based, but it should be aware of the passage of time."*

The system is aware of everything but **offers, doesn't push**. The Labrador knows where every ball in the yard is, but sits at the door wagging until you're ready.

| Gap Length | Behavior |
|-----------|---------|
| < 5 min | Say nothing. You're still here. Keep working. |
| 5-60 min | Single line: "Welcome back. Still on [topic]. Ready when you are." |
| 1-8 hours | Offer orientation: "Want a refresher on where we left off?" — wait for permission |
| 8+ hours | Full co-worker greeting: accomplishments, world radar (offered not pushed), where we left off, ask what to do next |

Each layer is a **permission gate**. It doesn't dump a briefing — it offers each section and waits.

---

## Radar Feed — What Happened While You Were Away

`06-radar/` already exists in the vault. What fills it:

- **World events** — RSS, news API (programmable: what topics you care about)
- **Market prices** — oil, silver, gold (directly relevant to ongoing research)
- **Calendar** — Nextcloud calendar (what's on today? research night?)
- **System health** — disk space, Nextcloud sync status, Ollama model status
- **Personal reminders** — flagged in previous sessions
- **Session accomplishments** — what the system did while you were away

All of this runs locally. RSS, calendar, clock — none of it needs Claude. The local model or a simple script assembles the briefing. Claude only gets called when you start talking.

---

## Voice Interface (Future)

> *"Eventually, this will become something that gets transferred into a verbal interface, and I expect it to be the co-worker mentality."*

The tone matters as much as the content. It's a colleague handing you coffee and a one-page brief, not a news anchor reading at you. The voice interface inherits the same permission-gate cadence — offer, wait, deliver only what's asked for.

---

## Design Principles

1. **Offer, don't push** — anti-Alexa; relevant and permissioned
2. **Time is the first axis** — the clock is checked before anything else
3. **File system is the medium** — process table, history, radar all live as files
4. **Local first** — briefing assembly doesn't require cloud; Claude is the specialist, not the scheduler
5. **The gap is the trigger** — gap length determines re-orientation depth

---

## Status

Design notes only. No spec written yet. No implementation. This is the first architectural sketch for the orchestration layer that makes multi-session Servetus possible.

## Related
- [[arc-storymap]] — Servetus as the memory/orchestration layer
- [[2026-02-28-servetus-voice-to-storymap-loop]] — the pipeline this orchestrates
- [[2026-02-28-verbal-processor-memory-system]] — why time awareness and re-orientation matter for this user
