---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: spec
  pipeline_stage: draft
  status: active
  intent: reference

identity:
  title: "Servetus Event Pipeline Spec"
  slug: "event-pipeline-spec"
  record_id: "SV-20260321-NOW-CDT-EVP0"

time:
  created_at: "2026-03-21"
  timezone: "America/Chicago"
  source_range: "today"

keywords:
  - event-pipeline
  - arc-writeback
  - session-close
  - automation
  - consolidation
  - context

tags:
  - servitus
  - spec
  - session
  - pipeline
  - architecture
---

# Servetus Event Pipeline Spec

## The Problem

Sessions produce artifacts but those artifacts don't automatically consolidate
into the arc. The result: arcs stay thin, context stays siloed in JSONL files,
and every new session starts partially blind. The human has to manually brief
the next instance of the LLM — which defeats the purpose of the system.

## The Principle

**The artifact landing is the trigger. Processing begins immediately.**

No polling. No manual triage step. No human has to say "now process this."
Session close = commit. Pipeline = compiler. Arc = the executable.

Resuming a room should mean: *"open a fresh instance that already knows
everything — because every closed session has already written itself into
the arc."*

---

## Two Trigger Points

### Trigger 1 — Session Close (artifact arrival)

```
session-close.py runs
    → artifact written to Inbox/Claude/<session>/
    → PostToolUse hook fires on Write
    → arc-update.py runs:
        1. Read session artifact
        2. Extract: decisions, blockers, people, atoms, topic switches
        3. Detect which arcs were touched (by room label + content scan)
        4. Write updates back to each arc file
        5. Regenerate context-card.md
    → arcs are current before next session opens
```

### Trigger 2 — Git Commit (spec/code change)

```
git commit runs
    → post-commit hook fires
    → context-card.py regenerates
    → bootloader re-evaluates if spec files changed
```

---

## Arc Write-Back (the missing wire)

When a session closes, `arc-update.py` updates each arc touched:

### What gets written back

| Source | Destination |
|---|---|
| Decisions made | `## Current Blockers` or `## Decisions` section |
| People mentioned | `## Team` — update status/notes |
| New atoms extracted | `## Atoms in this Arc` |
| Topic switches detected | Routes to appropriate arc |
| Open loops resolved | Remove from blockers |
| New open loops | Add to blockers |

### How arcs are detected

1. `SERVETUS_ROOM` env var → primary arc match
2. Content scan for arc slugs, people names, project names
3. Topic segmentation spec (`Toolkit/topic-segmentation.md`) → secondary arcs

### Write rules

- Append only — never overwrite existing content
- New entries go under the correct section header
- Source reference always included: `<!-- from session {short_id} {date} -->`
- If section doesn't exist, create it
- Placement is automatic for factual updates; flag for human review if ambiguous

---

## Room Launch — Arc-First Context

When a room is opened via the launch menu:

### Current (wrong) behavior
- Offers to resume old JSONL
- Loads isolated conversation history
- LLM starts with partial, siloed context

### Target behavior
- Opens **fresh** Claude Code session
- Injects arc file as system context (via `--context` flag or CLAUDE.md injection)
- LLM starts with consolidated arc knowledge, not old thread
- Old JSONL stays archived as tape — not the working context

### Resume vs. Continue distinction

| Action | Meaning |
|---|---|
| **Continue** (default) | Fresh session, arc loaded as context |
| **Resume** | Reload old JSONL — for mid-session recovery only |

---

## inbox-watcher.py — Promote to Pipeline Runner

`inbox-watcher.py` already exists as a file detector. Promote it:

1. Watch `Inbox/Claude/` for new session folders
2. On new artifact detected → call `arc-update.py`
3. On new Otter/audio file → call transcription pipeline
4. Report: "Session `{id}` processed → updated arcs: colo node, Servetus"

---

## Implementation Sequence

### Phase 1 — Arc write-back (highest value)
- [ ] `arc-update.py` — reads artifact, extracts updates, writes to arcs
- [ ] Wire into `session-close.py` — call after artifact is written
- [ ] Test: close a session, verify arc updated

### Phase 2 — PostToolUse hook
- [ ] Add hook to `settings.json`: PostToolUse on Write matching `Inbox/Claude/**`
- [ ] Hook calls `arc-update.py` on artifact arrival
- [ ] Eliminates need for manual triage of session artifacts

### Phase 3 — Arc-first launch
- [ ] Modify `launch-menu.py`: "Continue" opens fresh session with arc injected
- [ ] Keep "Resume" as secondary option for recovery
- [ ] Show arc last-updated timestamp in launch menu

### Phase 4 — Git post-commit hook
- [ ] `git config core.hooksPath .githooks`
- [ ] `post-commit`: regenerate context card if arc or spec files changed

---

## Key Constraint

Arc write-back is **append + flag, never overwrite**. The human reviews
arc updates at their discretion — the pipeline proposes, the human confirms.
Automated writes use a `<!-- pipeline: {date} -->` comment so they're
identifiable and reversible.

---

## Session Identity — Sub-labels Within a Room

Sessions within the same arc cannot all share the same name. The launch menu
becomes unnavigable when 4 sessions all read "colo node Arc."

### Design

Each session gets a two-part identity:

```
{Arc} › {focus-slug}

colo node Arc › mike-mazur-onboarding
colo node Arc › nextcloud-migration
Servetus Development Arc › event-pipeline-spec
```

### How the focus-slug is set

**At open (optional):** Launch menu prompts for a focus after room selection.
Can be skipped — defaults to arc name until close derives one.

**At close (automatic):** `session-close.py` derives the slug from session
content — the primary topic, key proper nouns, or dominant tool activity.
Writes it to the session registry and artifact frontmatter as `session-focus`.

**In the launch menu:** Display as `{Arc} › {focus}` with focus derived from
last close. If no focus set, show `{Arc} #{n}` where n is session count in
that arc.

### Artifact naming

Current: `2026-03-21-claude-session-0f81edaf.md`
Target:  `2026-03-21-binary-ranch-mike-mazur-onboarding-0f81edaf.md`

The short_id stays as the unique anchor. The slug makes it human-readable
without opening it.

---

## Related Specs

- `context-card-spec.md` — what the pipeline regenerates on every close
- `session-close-spec.md` — the close ritual this plugs into
- `Toolkit/topic-segmentation.md` — how topic/arc detection works
- `Toolkit/sorting-and-placement.md` — where extracted atoms land

---

## Origin

Conceived 2026-03-21, Servetus Development Arc session.
Context: multiple siloed colo node Arc sessions visible simultaneously,
each with partial divergent context. The close loop wasn't wired — sessions
produced artifacts but didn't write back into arcs. Every new session started
blind instead of informed.

The insight: **resuming should mean the arc is already current, not that
you have to search the archives.**
