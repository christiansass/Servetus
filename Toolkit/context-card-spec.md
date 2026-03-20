---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: spec
  pipeline_stage: draft
  status: active
  intent: reference

identity:
  title: "Servetus Context Card Spec"
  slug: "context-card-spec"
  record_id: "SV-20260319-NOW-CST-CCS0"

time:
  created_at: "2026-03-19"
  timezone: "America/Chicago"
  source_range: "today"

keywords:
  - context-card
  - session-close
  - portable-memory
  - situational-awareness
  - disconnected-mode

tags:
  - servitus
  - spec
  - session
  - memory
---

# Servetus Context Card Spec

## Purpose

The context card is a **portable situational awareness file** — a single Markdown
document generated from the vault at session close. It allows any LLM interface
(Claude Code, Claude.ai web, Claude mobile, API) to know the current state of the
owner's world, even without direct vault access.

It is not the memory. It is the **field briefing**. The vault is the authority.

---

## The Two Modes

### Connected Mode (Claude Code + vault)
- LLM has direct file access to the full vault
- Context card is loaded for quick orientation but not strictly required
- No warning shown — system operates normally

### Disconnected Mode (Claude.ai web, mobile, API, any other interface)
- LLM does not have vault access
- Context card is the only persistent context available
- LLM **must announce** at session start:

```
Working from Servetus context card — last synchronized 2026-03-19 14:32 CST.
Vault not connected. Operating on last known state. Some details may be outdated.
```

---

## File Location

```
10-System/context-card.md
```

Generated automatically by `session-close.py` at every session close.
Human-readable at all times. Plain Markdown, no binaries.

---

## Context Card Structure

```markdown
---
generated_at: "YYYY-MM-DD HH:MM TZ"
vault_version: "0.2.1"
sync_status: "current"
---

# Servetus Context Card
**Owner:** [Vault Owner Name]
**Generated:** [timestamp]
**Vault:** [vault path / hostname]

## Active Arcs
[List of active arcs with one-line summaries]

## Open Questions / Decisions Pending
[Highest-priority unresolved items]

## Team / Witnesses (Active)
[Names, roles, runway status if relevant]

## Current Projects
[Active projects with brief status]

## Key Directives
[Standing instructions that apply across all sessions]

## Last Session Summary
[One paragraph — what happened, what was decided, where things stand]

## Radar (What's Being Tracked)
[Items in 06-Radar/ — active monitoring]

## Memory Architecture Note
This card was generated from a sovereign Servetus vault.
The vault is the authority. This card is a snapshot.
If connected, verify against live vault before acting on any item here.
```

---

## Generation Rules

1. **Always generated at session close** — `session-close.py` writes this file before
   packaging the session artifact
2. **Timestamped** — `generated_at` in frontmatter is always UTC + local time
3. **Flat, not deep** — summaries only, no raw content. Each arc = one sentence.
   Each witness = name + role + one status note. Never paste full file contents.
4. **Standing directives included in full** — these are load-bearing; truncation is
   not allowed for the directives section
5. **Last session summary** — pulled from the session artifact being closed
6. **Max size: ~500 lines** — if the card exceeds this, truncate lower-priority
   sections (radar, projects) before touching arcs or directives

---

## Synchronization to Other Interfaces

### Claude.ai Projects (manual, current)
1. Session closes → `10-System/context-card.md` is updated
2. User uploads the file to their Claude.ai Project as project knowledge
3. All Claude.ai conversations in that project load it automatically

### Claude.ai Projects (automated, future)
- Session-close script pushes updated card to Claude.ai project via API
- No manual step required
- Sync timestamp in card reflects last push

### Other LLM interfaces
- Any interface that accepts a system prompt or document upload can receive the card
- The card is designed to be paste-able as a system message if needed

---

## Disconnected Mode Behavior (LLM Instructions)

When operating without vault access and a context card is present:

1. Read the card at session start
2. Announce disconnected mode with the `generated_at` timestamp
3. Use card contents to orient — treat it as approximate, not authoritative
4. Flag any decision that should be verified against the live vault before acting
5. Do not write new memories — note them for the user to file manually when connected
6. At session end, remind the user to sync the card if significant decisions were made

---

## Relationship to Other Specs

- `session-close-spec.md` — defines when and how this file is generated
- `bootloader.md` — defines the consult order; context card is loaded before
  any other spec when in disconnected mode
- `CLAUDE.md` — instructs connected LLM to read `10-System/last-session-brief.md`
  at start; context card serves the equivalent role across interfaces

---

## Design Principle

> The card is the passport. The vault is the homeland.
> You can travel without the homeland, but you carry proof of where you're from.
