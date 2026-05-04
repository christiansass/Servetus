# Changelog

All notable changes to Servetus will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.5] - 2026-04-07

### Added

**Server infrastructure (gpu-node node)**
- `10-System/transcription-queue.py` — GPU Whisper daemon; watches `Talk/Audio/` for recordings, runs Whisper on GTX 1080 Ti, writes `.md` transcripts, notifies Talk. Processes newest recordings first (`--oldest-first` flag available). Race-condition guard marks files in-progress before launching Whisper.
- `10-System/secretary.py` — deterministic context assembly (hopper, radar, witnesses, rooms, artifacts, services). `--daemon` mode refreshes `last-session-brief.md` every 5 minutes.
- `10-System/deploy-services-gpu-node.sh` — SSH deployment script for systemd user services on gpu-node.
- `systemd/` — service unit files for `servetus-talk-listener` and `servetus-transcription-queue`.

**Docker deployment**
- `docker-compose.yml` — one-command Servetus node deployment. Six containers: `display` (Xvfb), `chromium` (persistent browser), `whisper` (GPU transcription), `ollama` (local LLM), `talk` (listener), `secretary` (context assembly, `network_mode: none` — fully air-gapped).
- `docker-compose.colo-node.yml` — CPU-only stack for R420 (no CUDA).
- `Dockerfile.colo-node` — colo-node node image.
- `.env.example` — `VAULT_PATH`, `ANTHROPIC_API_KEY`, `SMTP` config.

**Talk bot enhancements**
- `expand_rich_message()` — expands `{object}/{file}` Nextcloud placeholders to readable text.
- `get_cached_talk_state()` — 60s TTL cache eliminates per-message 429 storms.
- `_handled_ids` dedup set — prevents double-response on restart races.
- Content dedup: MD5 hash + 10-second window blocks duplicate posts from NC client double-send.
- `handle_command()` — intercepts `!status`, `APPROVE:`, `REJECT:` before LLM; deterministic, no @mention gate.
- System prompt updated — bot knows it can dispatch via cluster queue.
- Per-room threads (`watch_room`), automatic room discovery (`refresh_rooms`, every 120s), emoji reaction detection (`watch_reactions`, every 15s).
- Auto-create/update witness files in `08-Witnesses/` for every Talk participant.
- Priority tiers: high/normal/low rooms with tiered 429 backoff.

**Talk Bot API (Servetus XO)**
- `10-System/talk-webhook.py` — push-based alternative to polling. NC pushes POST per message; no 429s. Setup instructions in module docstring.
- `config/nextcloud.env.example` — added `WEBHOOK_SECRET`.

**colo-node cluster**
- `10-System/cluster-router.py` — vault-native task daemon; polls `cluster/queue/`, claims and executes tasks.
- `10-System/cluster-dispatch.py` — dispatch helper for cross-node task queuing.
- `10-System/cluster/README.md` — bus schema, task types, node capability registry.
- `ansible/deploy-colo-node.yml` + `ansible/deploy-gpu-node.yml` — Ansible playbooks for both nodes.

**Tools and libraries**
- `10-System/nextcloud_cal.py` — CalDAV calendar read/write. 7 calendars. LLM-agnostic, importable by any component.
- `10-System/approval.py` — two-factor approval engine via Talk. Token generation, 24hr TTL, quorum models (unanimous/majority/any-one/named), SMTP delivery.
- `10-System/persona-loader.py` — loads `Toolkit/personas/<name>/` into system-prompt injection. Named personas overlay voice; guardrails remain underneath. Active persona persisted to `config/router_config.json`.
- `10-System/shopping-agent.py` — eBay/Amazon price monitor. Daemon + `--once` + `--list` modes.
- `10-System/rotate-credentials.py` — autonomous Nextcloud app password rotation.
- `10-System/nc-task.py` — create Nextcloud Tasks via CalDAV.
- `10-System/otter-import.py` — import Otter.ai transcripts.
- `10-System/standup-summary-today.py` — one-shot watcher for standup recording.
- `10-System/talk-room-map.py` — queries NC Talk API, builds `config/talk-rooms.json`.
- `10-System/bootloader-hook.py` — self-locating path injection for session start.
- `10-System/vault_writer.py`, `attachment_handler.py`, `conversation_logger.py` — vault write-back stack.
- `10-System/lunar-calendar.py` — biblical/lunar calendar calculations.

**Persistent display and browser agent**
- `10-System/browser.py` — `ServetusBrowser` agent with vision loop, full screenshot audit trail, named sessions (persistent login state), Ollama or Claude vision backend.
- `systemd/servetus-display.service` — Xvfb 1920×1080 on `:1`, starts at boot.
- `systemd/servetus-chromium.service` — persistent Chromium, remote debugging port 9222.

**System documentation**
- `10-System/system-map.md` — full component inventory: 82 components, 3 nodes, all data flows.
- `10-System/ROADMAP.md` — versioned roadmap v0.3 → v1.0 with exit criteria per milestone.
- `10-System/servetus-architecture.canvas` — Obsidian canvas visual architecture diagram.

**New Toolkit specs**
- `S00.01-11-00` — Server-Bot Parity: MCP tool access for Talk bot.
- `S00.01-12-00` — Telegram Integration: sovereign identity stack, MTProto, GrapheneOS+SIM model.
- `S00.01-13-00` — Persistent Display: 1080p Xvfb, screen share via Talk. Rule 8: human screen privacy is absolute.
- `S00.01-14-00` — Talk Approval Protocol: two-factor approval via Talk + out-of-band token.
- `S00.01-15-00` — Container Architecture: one `docker-compose.yml` brings full node up. Ansible required (Rule 0).
- `S00.01-16-00` — Collective Maintenance: approval flow, gap register.
- `S00.01-17-00` — Talk Room Posting Protocol: five-check pre-post protocol for all Talk rooms.
- `S00.01-18-00` — Interface Continuity: single Servetus identity across web, physical, Android. actorId as ground truth.
- `S00.01-19-00` — Control Room: pipeline visibility dashboard spec.
- `Toolkit/context-card-spec.md` — portable situational awareness card, generated at session close.
- `Toolkit/security-scrub-protocol.md` — device fingerprint scrub procedure + pre-commit hook.
- `Toolkit/voice-performance-format.md` — SVP spec: two-stave transcript + prosody notation.

**GitHub Pages**
- `docs/index.html` — dark terminal landing page.
- `docs/philosophy.html` — renders `Philosophy.md` via `fetch()` + `marked.js`.
- `docs/changelog.html` — renders `CHANGELOG.md`.
- `docs/capture-tool.html` — WebDAV bookmarklet generator with sovereign credential model.

### Changed
- `10-System/session-close.py` — generates `10-System/context-card.md` on every close; credential scrub on both markdown and JSONL artifacts.
- `Philosophy.md` — added: "The Patient With Amnesia", presence layer, session continuity.
- Vault folder casing normalized: `06-Radar` (uppercase), legacy lowercase duplicates removed.
- `10-System/pre-commit-check.sh` — pre-commit hook blocks real MAC/IP/hostname.
- `S00.01-05-00` (Guardrails) — Rule 8 added: human screen privacy absolute.
- `S00.01-10-90` (Session Start) — Step 0: cluster check-in; MCP placement rule added.
- `S00.01-10-91` (Session Close) — collective review pass, updated notification routing table.
- `S00.01-15-00` (Container Architecture) — Ansible required added as Rule 0.

### Fixed
- Transcription notifications routed to Christian's 1:1 only (not colo-node Standup).
- Orphaned in-progress queue entries reset on daemon startup.
- `[HOPPER]` announcements redirected from stdout to `hopper-events.log` (was freezing terminal).
- Stale lowercase folder duplicates removed from Git index.
- Credentials scrubbed from JSONL witness artifacts at session close.
- Backlog transcription notifications suppressed for recordings older than 7 days.

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
