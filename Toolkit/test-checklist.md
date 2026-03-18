---
type: spec
title: "Test Checklist"
slug: "test-checklist"
status: active
date: 2026-03-17
tags: [toolkit, testing, qa]
---

# Servetus Test Checklist

Each item maps to a feature described in `09-Shared/what-servetus-does.md`.
Status: [ ] untested  [x] verified  [~] partial / known issue

---

## Launch Brief (`10-System/launch-brief.py`)

### Box rendering
- [ ] All row borders align with top/bottom corners (no right-side overflow)
- [ ] No extra trailing spaces inside rows

### Header
- [ ] Current date and time display in top-right corner
- [ ] Vault version displays correctly

### SESSION row
- [ ] Context fill percentage is accurate
- [ ] Token count and turn count display
- [ ] Last active timestamp shows most recent session activity
- [ ] Fill bar color: green < 60%, yellow 60–80%, red > 80%
- [ ] Context warning line appears at 60% and 80%

### LAST row
- [ ] Shows elapsed time since last closed session (e.g. "8h 37m ago")
- [ ] Shows human-readable close time ("today 05:13", "yesterday 22:41", "Mar 15 10:20")
- [ ] Shows room name of last session
- [ ] Once session-close writes summary fields: shows turns, duration, files touched
- [ ] On very first session ever: shows "first session — no prior history"

### OPEN row (multi-session)
- [ ] Does NOT appear when only one session is running
- [ ] Appears when a second terminal has an active session open
- [ ] Shows room and start time of the other session
- [ ] Does not show the current session as "another open session"

### MEMORY row
- [ ] Shows CLAUDE.md file size in kb
- [ ] Shows count of Toolkit specs
- [ ] Lists spec names, truncating with +N if too many to fit

### RADAR row
- [ ] Shows item count when 06-Radar has files
- [ ] Shows "no items filed" when empty

### ARC row
- [ ] Lists active arc titles
- [ ] Truncates with +N overflow count
- [ ] Shows "no active arcs" when none

### PROJECTS row
- [ ] Lists project folder names sorted by most recent activity
- [ ] Shows most recently touched project and its date
- [ ] Truncates with +N overflow count

### TEMPORAL row
- [ ] Shows "present" in green when last artifact is current month
- [ ] Shows "historical" in yellow when last artifact is a prior month

### WRITE row
- [ ] Path reflects current date correctly

### SYSTEM row
- [ ] session-close: green check when script exists, red X when missing
- [ ] statusline: green check when configured, red X when missing
- [ ] git: shows pending count in yellow, "clean" in green

---

## Session Close (`10-System/session-close.py`)

### Empty session gate
- [ ] Open sc, type nothing, exit → run session-close → no artifact written, no Hopper entry
- [ ] Open sc, paste image only, exit → run session-close → no artifact written
- [ ] Open sc, have a real conversation → run session-close → artifact IS written

### Artifact contents
- [ ] Frontmatter includes session ID, model, timestamps, machine origin
- [ ] Full transcript with timestamps on every turn
- [ ] Tool activity log present
- [ ] Images extracted and saved as separate files in session folder
- [ ] JSONL witness file co-located in session folder

### Hopper destination
- [ ] Artifact lands in `Inbox/Claude/<date>-claude-session-<id>/`
- [ ] Falls back to `00-inbox/claude/` if sibling Inbox vault not found
- [ ] Does not overwrite existing artifact if re-run on same session

### Session registry
- [ ] Registry entry marked "closed" after session-close runs
- [ ] Closed timestamp recorded
- [ ] `turns`, `duration`, `files_touched`, `tool_calls` written to registry entry

---

## Session Registry (`~/.servetus_sessions.json`)

- [ ] New "open" entry written when launch-brief runs
- [ ] Entry transitions to "closed" when session-close runs
- [ ] Multiple vaults tracked independently (entries scoped by vault path)
- [ ] Registry survives repeated launches without corruption

---

---

## Statusline Timecode (`10-System/statusline.sh`)

Acceptance criteria defined by CS Lewis bot, 2026-03-18 — promoted from conversation to specification:

### Rollover stability
- [ ] Clock handles midnight boundary without resetting or freezing
- [ ] Day/date transitions display correctly without restart
- [ ] Session age counter rolls over hours → days cleanly

### Sync with saved records
- [ ] Timecode displayed in statusline matches `captured_at` in most recent session record
- [ ] After session-close runs, the closed timestamp in registry matches what statusline showed at exit
- [ ] No drift between statusline clock and filesystem timestamps over a multi-hour session

### Behavior on interruption/restart
- [ ] KITT scanner resumes correctly after terminal sleep/wake
- [ ] If Claude Code is killed and restarted mid-session, statusline recovers without stale state
- [ ] Session age picks up from original start time, not restart time

---

## To Add (features not yet built)
- Inbox triage (`inbox-triage.py`) — pending test spec
- Inbox watcher (`inbox-watcher.py`) — pending test spec
- Morning reminder system — pending test spec
- Voice pipeline — pending test spec
