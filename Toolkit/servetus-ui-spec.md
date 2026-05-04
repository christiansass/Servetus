---
title: "Servetus UI Architecture"
status: design
created: 2026-03-17
branch: feature/servetus-ui
---

# Servetus UI Architecture

This spec covers all rendering surfaces for the Servetus system — from the
terminal session wrapper up through web and native app layers.

**Core principle:** data collection and rendering are strictly separated.
The same structured JSON that drives the terminal brief drives every other
surface. The terminal is renderer #1. It is not the ceiling.

---

## Renderer Stack

```
                    ┌─────────────────────────────┐
                    │      Servetus Data Layer      │
                    │  session JSON · vault state   │
                    │  arcs · projects · artifacts  │
                    └──────────────┬────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
     ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐
     │   Terminal     │  │    Web UI        │  │   Native / App   │
     │  (renderer 1)  │  │  (renderer 2)    │  │  (renderer 3)    │
     │                │  │                  │  │                  │
     │  launch-brief  │  │  dashboard       │  │  iOS / Android   │
     │  launch-menu   │  │  arc timeline    │  │  menubar widget  │
     │  statusline    │  │  StoryMap view   │  │  voice interface │
     │  session-close │  │  witness viewer  │  │  Talk Bot        │
     └────────────────┘  └─────────────────┘  └──────────────────┘
```

All renderers read from the same source. No renderer owns the data.

---

## Renderer 1 — Terminal

The current working layer. Everything here is in `10-System/`.

### 1.1 Launch sequence

```
sc
 ├── launch-menu.py     → pick LLM + context
 ├── launch-brief.py    → 8-gauge cluster + funnel animation
 └── exec <llm-cmd>     → hand off to selected LLM
```

### 1.2 Launch animation

A funnel renders below the brief box, tapering from the Servetus box width
(W=72) down to a 32-char brain box representing the active LLM.

**Geometry:**
- Box width `W = 72` (matches brief box)
- Funnel tapers from col 0→71 down to col 20→51 (32-char brain, centered)
- Step = 4 cols per side per row → 5 funnel rows + flat bottom
- Brain inner width = 30 chars

**Behavior:**
- Phase 1: funnel outline prints dim/grey, line-by-line (0.03s/line)
- Phase 2: brain box materializes in green, line-by-line (0.045s/line)
- Total: ~0.5s

**Brain art is LLM-aware** — swaps based on selected LLM. Art pending for
each entry (see §3.2). Claude brain = pixel-art robot matching Claude Code
footer mascot. **Claude art pending from user.**

**Implementation:** `10-System/launch-brief.py` → `funnel_animation(llm_key)`

### 1.3 Per-session LLM selection

The launch menu gains an LLM picker above the context picker.

```
╔══════════════════════════════════════════════════════════════════════╗
║  SERVETUS  ●  Choose your session                                   ║
╠══════════════════════════════════════════════════════════════════════╣
║  LLM                                                                ║
║   1. claude-sonnet-4-6    remote · default                         ║
║   2. claude-opus-4-6      remote · heavy                           ║
║   3. ollama / llama3      local  · no cost                         ║
║   4. ollama / mistral     local  · fast                            ║
╠══════════════════════════════════════════════════════════════════════╣
║  CONTEXT — arc / project / session                                  ║
║   5. colo-node Arc      2h ago                                   ║
║   6. T-Mobile Breach      yesterday                                ║
╠══════════════════════════════════════════════════════════════════════╣
║  [1–N] pick   [N] new label   [Enter] defaults                     ║
╚══════════════════════════════════════════════════════════════════════╝
```

**LLM roster** defined in `config/llm-roster.json`:

```json
[
  {
    "key":     "claude",
    "label":   "claude-sonnet-4-6",
    "tag":     "remote · default",
    "cmd":     "claude",
    "args":    [],
    "default": true
  },
  {
    "key":     "claude-opus",
    "label":   "claude-opus-4-6",
    "tag":     "remote · heavy",
    "cmd":     "claude",
    "args":    ["--model", "claude-opus-4-6"]
  },
  {
    "key":     "ollama-llama3",
    "label":   "ollama / llama3",
    "tag":     "local · no cost",
    "cmd":     "ollama",
    "args":    ["run", "llama3"]
  }
]
```

**Data flow:**

```
launch-menu.py
  → user picks LLM key + context label
  → writes ~/.servetus_session.json:
      { "llm_key": "claude", "llm_cmd": "claude", "llm_args": [], "room": "..." }

servetus script
  → reads llm_cmd + llm_args
  → runs launch-brief.py (reads llm_key → correct brain art in animation)
  → exec's the selected LLM command

session-close.py
  → records llm_key in session frontmatter (auditable)
```

### 1.4 Statusline

`10-System/statusline.sh` — reads `~/.servetus_session.json`, renders
one-line context bar in the terminal prompt or tmux statusline.
Spec: separate from this doc — see `Toolkit/session-start.md`.

### 1.5 Terminal open questions

- **`servetus` script:** resolved — canonical file at `~/bin/servetus`, `sv` symlink for short access
- **Offline detection:** warn in menu if `ollama` is not running
- **Default fallback:** Enter with no LLM → use `"default": true` from roster
- **Brain art:** all LLM mascots pending design (see §3.2)

---

## Renderer 2 — Web UI

Not yet built. Design intent only.

### Purpose

A browser-based dashboard for reviewing vault state, browsing arcs and
artifacts, and visualizing the StoryMap timeline. Not a chat interface —
the LLM still lives in the terminal. The web layer is read-mostly with
lightweight filing actions.

### Views planned

| View | Description |
|------|-------------|
| **Dashboard** | Same 8-gauge cluster as the terminal brief, rendered as cards |
| **Arc timeline** | Visual bar for each arc spanning its time envelope (see StoryMap design) |
| **Artifact browser** | Navigate `00-Artifacts/` with preview |
| **Witness viewer** | People records from `08-Witnesses/` |
| **Inbox / Hopper** | Review and file items without opening a terminal |
| **Session log** | Browse past session artifacts with full transcript |

### Data source

A lightweight local server (FastAPI or similar) that reads vault state and
serves JSON to the browser. Same data the terminal reads — no separate DB.
Server runs locally; no cloud dependency.

### StoryMap integration

The arc timeline view is the first step toward StoryMap.me — color-coded
bars per entity, week-grid calendar, artifact thumbnails at actual dates.
Design reference: `10-System/memory/design_arc_visualization.md`.

### Web open questions

- Local server vs. static site generation (rebuild on vault change)?
- Auth — localhost only, or plan for remote access from phone?
- How does it receive new artifacts? Watch `00-Artifacts/` for changes?

---

## Renderer 3 — Native / App

Not yet designed. Placeholder for future surfaces.

### Surfaces anticipated

| Surface | Notes |
|---------|-------|
| **iOS / Android app** | Session review, witness lookup, artifact submission from phone camera |
| **macOS menubar widget** | Session state at a glance — active arc, context usage, last artifact |
| **Voice interface (Talk Bot)** | Phase 1 target — mic in, spoken LLM response out, auto-capture to vault |
| **Obsidian plugin** | In-vault rendering of Servetus state without leaving the editor |

### Talk Bot (Phase 1 priority)

Voice interface to Servetus. Input: Wispr Flow or direct mic. Output:
ElevenLabs or Rox TTS. Side effect: auto-capture to daily logs.
Full spec deferred — see memory entry `project_traffic_controller.md` for
the paragraph-level topic detection layer that sits on top of Talk Bot input.

---

## 3. Shared Concerns

### 3.1 LLM adapter layer

Each LLM has a different session format. A normalization layer converts
per-LLM session data into a standard Servetus session JSON before any
renderer touches it.

```
Claude Code JSONL  ──┐
Ollama logs        ──┤──→  Servetus session JSON  ──→  any renderer
OpenAI API logs    ──┘
```

`session-close.py` is the current implementation for Claude. It needs to
become an adapter dispatcher as new LLMs are added.

### 3.2 LLM mascot art registry

Each LLM gets a 30-char-wide ASCII art block (brain inner width) for the
terminal animation. Stored in `10-System/launch-brief.py` as `LLM_MASCOTS`.

| Key | Art status | Notes |
|-----|-----------|-------|
| `claude` | **pending** | Pixel-art robot matching Claude Code footer |
| `ollama` | not started | Llama silhouette? Flame? TBD |
| `openai` | not started | Placeholder until needed |
| `default` | not started | Generic `[LLM]` box for unknowns |

### 3.3 Session artifact as the connective tissue

Every session — regardless of renderer or LLM — produces one artifact in
`00-Artifacts/`. That artifact is the authoritative record. All renderers
can link back to it. The artifact format must be stable across LLMs.

---

## 4. Files Affected

| File | Status | Change |
|------|--------|--------|
| `10-System/launch-brief.py` | exists | `funnel_animation(llm_key)` — brain art dict |
| `10-System/launch-menu.py` | exists | Add LLM section above context |
| `config/llm-roster.json` | new | LLM roster definition |
| `~/bin/servetus` | canonical file | Execs correct LLM command; `sv` symlink for short access |
| `10-System/session-close.py` | exists | Record `llm_key` in frontmatter |
| `10-System/web/` | new (future) | Local web server + frontend |
| `10-System/voice/` | exists (stub) | Talk Bot implementation |
