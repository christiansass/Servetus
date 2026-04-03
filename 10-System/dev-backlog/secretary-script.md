---
type: backlog
title: "Secretary Script — Deterministic Context Layer"
slug: "secretary-script"
status: open
priority: high
created: "2026-03-25"
circle: inner
---

# Secretary Script

## What It Is

`10-System/secretary.py` — reads all known registers, outputs a structured JSON
context object. No LLM involvement. The data layer everything else stands on.

## Design Principle

Orientation is infrastructure. 50-75% of daily ops are deterministic lookups.
The secretary script handles all of them before any LLM is invoked.

## Data Sources

| Register | What it provides |
|----------|-----------------|
| `hopper-events.log` vs `hopper-cursor.txt` | New arrivals since last check |
| `06-Radar/open-loops.md` | What's waiting on Christian |
| `10-System/last-session-brief.md` | What was open at last session close |
| `08-Witnesses/` | Known person lookups |
| `config/talk-rooms.json` | Room → circle mapping |
| `config/talk-cursor.json` | Unread Talk messages |
| Calendar API | Upcoming events |
| `06-Radar/` items | Active radar, overdue items |
| `10-System/dev-backlog/` | System development status |

## Output

Structured JSON context object passed to packaging layer.
No LLM touches this output — it goes directly into the package assembler.

## Escalation Path

Script layer → Haiku synthesis (make it speakable) → Sonnet only if question requires reasoning

## Related

- `10-System/dev-backlog/context-packaging-spec.md`
- `10-System/dev-backlog/soc-session-format.md`
- `10-System/dev-backlog/agent-architecture.md`
