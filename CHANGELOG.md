# Changelog

All notable changes to Servetus will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] - 2026-01-30

### Added
- **Altitude-based folder structure** - Folders now numbered by zoom level:
  - `01-witnesses` (ground level, most zoomed in)
  - `02-daily-logs`
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
