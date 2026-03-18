# Changelog

All notable changes to Servetus will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] - 2026-03-18

### Added
- **`10-System/launch-brief.py`** — session-opening intelligence dashboard: last session, open sessions, memory load, radar, arcs, projects, write path, system health, orphan warnings
- **`10-System/statusline.sh`** — KITT edition running clock: local timecode ticking every second, session age counter, room label (`$SERVETUS_ROOM`), KITT red bouncing scanner on THINKING state
- **`10-System/inbox-triage.py`** — intelligent Hopper triage: scans `Inbox/Claude/`, presents numbered list, arc-match suggestions, action options
- **`10-System/inbox-watcher.py`** — background Hopper daemon: watches `Inbox/` for new files, announces to terminal with yellow `[HOPPER]` banner, wired into sc launcher so LLM is no longer doing Hopper checks
- **`10-System/inbox-file.py`** — two-stage filing pipeline: `process` (creates record, file stays in Hopper) → `finalize` (moves to `00-Artifacts/`, marks `distilled: true`)
- **`10-System/inbox-scan.py`** — standalone Hopper scanner
- **`10-System/list-active-arcs.py`** — active arc listing utility
- **`10-System/launch-menu.py`** — interactive session launch menu
- **`10-System/claude-web-export.js`** — Claude.ai web export bookmarklet
- **`Toolkit/servetus-ui-spec.md`** — formal specification for all UI components
- **`Toolkit/test-checklist.md`** — acceptance criteria for launch-brief, session-close, session registry, statusline timecode (includes Lewis's three criteria: rollover stability, sync with saved records, interruption/restart behavior)
- **`install.sh`** / **`install.ps1`** — cross-platform installers
- **Orphan session scanner** in `session-close.py` — detects real sessions without artifacts at close time, writes `10-System/orphan-sessions.json`, surfaced in launch-brief on next open
- **File Naming Convention** section in `Toolkit/frontmatter-schema.md` — `subject_type.md` underscore-separator pattern, slug contains subject only

### Changed
- **`10-System/session-close.py`** — major overhaul:
  - Full-fidelity capture: JSONL raw witness co-located with artifact in session folder
  - Per-turn timestamps on every message in transcript
  - Millisecond precision throughout
  - Hardcoded `America/Chicago` → `local_timezone_name()` (reads `/etc/localtime` symlink)
  - Removed `_fallback_claude` (was pointing to retired `00-inbox/claude/`); exits cleanly with error if sibling Inbox not found
- **`Toolkit/local/install.sh`** — `sc` launcher wires `inbox-watcher.py` as background daemon (killed on exit), runs `session-close.py` at close
- **`05-Arcs/_arc-template.md`** — `slug` now contains subject only, no type suffix
- **`Toolkit/sorting-and-placement.md`** — updated placement rules
- **`Philosophy.md`** — additions

### Fixed
- Timezone hardcoding in session artifact frontmatter
- Fallback path pointing to retired `00-inbox/claude/` directory
- Orphan sessions from prior development work retroactively archived (`2bba5ce2`, Feb 26, 302 lines)

---

## [0.2.2] - 2026-03-11

### Changed
- **Folder rename: `01-witnesses/` → `01-artifacts/`** — files are artifacts (the tape), not witnesses (people)
- **Folder rename: `02-daily-logs/` → `02-memories/`** — atomized thoughts, not time-bound logs
- **`servetus_cli.py`** — LOG_DIR updated to `02-memories/`
- **README** — fully rewritten to v0.2.1 architecture: artifact chain, corroboration scores, v0.2 folder structure, flat frontmatter examples, Map vs Engine, LLMs as Prototyping Environment, watch folder principle
- **Philosophy.md** — merged v0.1, v0.2 session, and 2026-03-11 additions into single authoritative document

### Added
- **Philosophy: The Personal Origin** — verbal processor framing, prosthetic origin story
- **Philosophy: Audio-First** — witness format hierarchy (audio > video > photo > text)
- **Philosophy: Witness Consensus and Corroboration Score** — privacy-preserving numeric scoring, discovery angle
- **Philosophy: The Sacred Space** — boundary between machine processing and human thought
- **Philosophy: Map vs. Engine** — Servetus as memory map independent of AI vendor
- **Philosophy: LLMs as Prototyping Environment** — spec-to-code pipeline
- **Philosophy: The Framework Trap** — LLM-dependent frameworks are not software (landing page source)
- **Philosophy: A Safety Net Around AI** — AI governance for individuals (landing page source)
- **README: Corroboration Score** — numeric scoring model documented publicly
- **README: Architecture Principle 7** — Every Folder Is a Watch Folder
- **Toolkit: Migration path updated** — folder renames marked complete

### Fixed
- All Toolkit specs, SETUP.md, CHANGELOG, system-info updated to remove `01-witnesses` and `02-daily-logs` references

---

## [0.2.1] - 2026-01-31

### Changed
- **Toolkit filename convention** - Removed date suffixes from spec filenames
  - Before: `S00.01-00-00-servetus-bootloader(2026-01-16).md`
  - After: `S00.01-00-00-servetus-bootloader.md`
- **Version tracking** - Added `system_version` field to frontmatter schema
  - Version alignment now tracked in frontmatter, not filenames
  - All specs updated to `system_version: 0.2.0`
- **Cleaned up specs** - Removed errant FILENAME headers and code block wrappers from several spec files
- **Updated internal links** - All wikilinks now use clean filenames without date suffixes

---

## [0.2.0] - 2026-01-30

### Added
- **Altitude-based folder structure** - Folders now numbered by zoom level:
  - `01-artifacts` (ground level, most zoomed in)
  - `02-memories`
  - `03-events`
  - `04-projects`
  - `05-arcs`
  - `06-radar` (current viewport)
  - `07-storymap` (30,000ft view, most zoomed out)
- **Radar concept** - Situational awareness system. Tag any note with `radar: active: true` to track it without moving it. View all radar items in `06-radar/`.
- **Witness exhibits model** - Witnesses are now time-bound text representations of artifacts:
  - Time envelope defined by largest artifact
  - Multiple artifacts per witness with individual timecodes
  - Device tracking for independent corroboration
  - Validity scoring (artifact count, device count, coverage overlap)
  - Coverage visualization (full vs partial)
- **Sharing model spec** - Future architecture for StoryMap.me social layer:
  - Privacy pyramid (witnesses private → storymap public surface)
  - Granular per-relationship permissions
  - Serendipitous discovery without exposure
- **CLAUDE.md preload script** - Lean bootloader for AI assistants (local only, gitignored)
- **config/ folder** - Separated user settings from system specs:
  - `projects.md` - Active projects
  - `tags.md` - Tag taxonomy
  - `overrides.md` - User preferences

### Changed
- **Frontmatter schema** - Added optional `radar:` block with `active`, `added`, `reason` fields
- **CLI path fix** - `servetus_cli.py` now correctly writes to `01-daily-logs/` at vault root
- **Witness template** - Complete overhaul for time-bound exhibits with multi-artifact support

### Architecture
- Toolkit contains system specs (public, versioned)
- config/ contains user settings (private, gitignored)
- Multi-user witness validation feeds event credibility
- Altitude model reflects privacy gradient (ground = private, high = shareable)

---

## [0.1.0] - 2026-01-16

### Added
- Initial Toolkit with 12 spec files
- Core specs: bootloader, export rules, frontmatter schema, time rules, spelling rules
- Topic segmentation and sorting/placement protocols
- Session start template
- Basic folder structure
- CLI prototype (`servetus_cli.py`)
- Templates for daily-log, event, arc, project, witness, storymap

### Established
- Servetus naming (Miguel Servetus, 16th-century polymath)
- Core principle: "There is no trust without truth, and there is no assistant without trust"
- Witness Chain concept: Reality → Witnesses → Structured Memory → AI Processing → Human Review → Reality Check
