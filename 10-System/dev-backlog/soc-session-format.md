---
type: backlog
title: "SOC Session Format — Time-Segmented with AFK Detection"
slug: "soc-session-format"
status: open
priority: high
created: "2026-03-25"
circle: inner
---

# SOC Session Format

## Current State

SOC files use `2026-03-25_SOC` — one per day, no time segmentation.
No AFK detection. No auto-close. No secretary-style resume brief.

## Target Format

`2026-03-25_SOC_0401` — date + SOC + start time (HHMM).
Multiple segments per day. Each one a discrete watch period.

## Behavior

**On start:**
- New SOC file created with timestamp in name
- Secretary script runs — hopper, radar, calendar, open loops
- Resume brief pre-loaded into session context

**While active:**
- Heartbeat every 10 minutes — re-read registers, surface changes naturally
- No announcement unless something changed

**On AFK timeout:**
- Session auto-closes
- Handoff brief written from secretary.py output
- New SOC file ready for next resume

**On resume:**
- Secretary script runs again — diff since last close
- Brief includes: what was open, what came in, what's on calendar, what moved on radar
- New SOC segment opens with context pre-loaded

## AFK Threshold

TBD — candidate values: 30 minutes, 1 hour. Needs decision.

## Server-Side Question

Talk bot currently makes stateless API calls — no persistent session, no JSONL
accumulating server-side. Need to understand the thread model before building
SOC management for the server. Research task.

## Related

- `10-System/dev-backlog/secretary-script.md`
- `10-System/launch-menu.py` — needs update for new naming format
