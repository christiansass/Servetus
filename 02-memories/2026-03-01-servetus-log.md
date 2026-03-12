---
servitus:
  schema_version: 1
  record_type: daily_log
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Daily Log — March 1, 2026"
  slug: "daily-log-2026-03-01"
  record_id: "SV-20260301-NOW-CST-LOG"

time:
  created_at: "2026-03-01"
  timezone: "America/Chicago"
  source_range: "today"

origin:
  machine: "WordInFilm"
  mac: "30:9c:23:8c:6e:04"
  ip: "10.0.0.109"

tags:
  - servitus
  - daily-log
---

# Daily Log — March 1, 2026

## 1) Raw Input

[cinnamon/panels — parked]
<!-- origin: WordInFilm | 30:9c:23:8c:6e:04 | 10.0.0.109 | Linux Mint 22.3 -->
Continued panel and dock exploration. Installed Plank dock — cool but missing
systray support and per-monitor window control granularity. Jury still out on
the right dock/panel approach. Parking customization work for now.

## 2) Summary

A long session spanning late Feb 28 into March 1, and continuing into the evening of March 1. Three distinct phases:

**Phase 1 (carried from Feb 26):** Linux panel/dock work — Plank installed, tested, rejected.

**Phase 2 (primary):** Full Otter.ai ingestion run — all 4 February 28 voice recordings processed into witnesses + atoms by parallel Claude subagents. 17 files created.

**Phase 3 (March 1 evening):** Arc work, vault cleanup, spec updates, and architecture decisions. Word in Film arc created. 70 previously-parked atoms moved from Inbox to `02-daily-logs/`. Both specs rewritten and committed to git. MVP plan drafted for frontmatter migration and Canvas storymap test.

**Session interface note:** As of March 1, interaction with Servetus is happening via Claude Code CLI — not directly inside Obsidian. This is a new working pattern and affects how session logging is triggered.

## 3) Key Points

### Cinnamon panels / dock (carried from Feb 26 work)
- **Plank:** Installed and tested. Visually clean but no systray, no per-monitor
  window list control. Not sufficient on its own for this 3-monitor setup.
- **Cinnamon panels:** Still running 3 panels (one per monitor). The
  `window-display-settings: 1` bug (windows not isolated per monitor) is
  identified but not yet fixed — intentionally parked.
- **hwmonitor:** Metadata version fix + instance ID settings fix applied
  (see [[linux-cinnamon-applet-version-mismatch]]). Still needs verification
  after next Cinnamon restart.
- **Desired end state** (documented, not yet implemented):
  - Bottom taskbar per monitor, each showing only that monitor's windows
  - Top panel on Cintiq only, with hwmonitor
  - Clock/tray staying on Cintiq bottom panel

### Otter.ai ingestion — February 28, 2026 (4 recordings)
All four DOCX exports from Otter.ai were extracted (Python zipfile + xml.etree, no pandoc) and processed by parallel Claude subagents.

**Witnesses created** (all in `01-witnesses/2026/02-February/2026-02-28/`):
- `2026-02-28-robotics-drive-home.md` — solo drive-home voice memo after FIRST Robotics
- `2026-02-28-talk-with-ken-daniels.md` — planning call with Ken Daniels (~48K)
- `2026-02-28-recording-evening-session.md` — evening session with Ken; Obsidian demo, Mural walkthrough (1h 9m)
- `2026-02-28-1st-century-video-planning.md` — 3-way call: Christian, Ken, Nick Bates (2h 5m; ends mid-session)

**Atoms created** (all in `02-daily-logs/`):
- `2026-02-28-audio-first-witness-philosophy.md`
- `2026-02-28-verbal-processor-memory-system.md`
- `2026-02-28-mother-in-law-brain-tumor-context.md`
- `2026-02-28-tithing-tool-concept.md`
- `2026-02-28-binary-ranch-servetus-sovereignty.md`
- `2026-02-28-biblical-research-wall-apologetics.md`
- `2026-02-28-mural-calendar-templates.md`
- `2026-02-28-servetus-voice-to-storymap-loop.md`
- `2026-02-28-tribulation-storymap-and-7000-year-timeline.md`
- `2026-02-28-two-years-film-concept.md`
- `2026-02-28-streaming-setup-and-production-goals.md`
- `2026-02-28-tithing-tool-saas-concept.md`
- `2026-02-28-research-night-structure-and-calendar.md`
- `2026-02-28-apologetics-course-and-church-history-map.md`
- `2026-02-28-nick-bates-onboarding-to-first-century.md`

### Arc updates (Phase 2)
- **Created:** `arc-first-century-fellowship.md` — new arc, 9 atoms indexed
- **Updated:** `arc-storymap.md` — 4 atoms added
- **Updated:** `arc-binary-ranch.md` — 2 atoms added
- **Updated:** `arc-biography.md` — 2 atoms added

### Phase 3 — March 1 evening

**Word in Film arc:**
- Corrected organization name from "Word and Film" → "Word in Film" across all files
- Created `arc-word-in-film.md` — organization history, server, production pipeline, Miro board infrastructure, 3 atoms indexed
- Updated `arc-first-century-fellowship.md` cross-reference to match

**Inbox cleanup — 70 atoms moved:**
- All atoms from the Feb 27 GPT atomization run (and earlier sessions back to Dec 2025) were parked in `Obsidian/Inbox/YYYY/MM/DD/` with `pipeline_stage: inbox`
- Moved all 70 to `02-daily-logs/` — filenames normalized (double dashes → single, type suffixes stripped), `pipeline_stage` updated to `distilled`
- Empty Inbox date folders pruned

**Spec rewrites — committed to git:**
- `_witnesses-spec.md` — full rewrite: Lightroom hierarchy, audio-first philosophy, witness pair/triple model, Otter.ai ingestion pipeline, naming convention, frontmatter requirements
- `_daily-logs-spec.md` — full rewrite: atomic layer definition, index card model, flat folder structure, naming convention, pipeline stage table, relationship to witnesses/arcs
- Committed to `personal` branch: `509f977`

**Architecture decisions locked:**
- Inbox = drop zone only; processed files move out immediately
- DOCX source files move to witness folder alongside .md (on hold pending full Otter.ai mass download)
- Session interface = Claude Code CLI (not Obsidian-native); new pattern as of March 1
- Servetus as local daemon is the long-term goal — Ollama 70B as primary engine, Claude as escalation layer

**MVP plan drafted:**
1. Write frontmatter flattening migration script (nested → flat top-level keys)
2. Test on 5 files, verify Obsidian Properties
3. Run on full vault
4. Open Canvas, test atom filtering by `record_type` / arc
5. Excalidraw storymap comes after Canvas proof of concept

## 4) Events Detected
- Plank dock installed on WordInFilm (carries from earlier session)
- 4 witness files ingested from Feb 28 Otter.ai recordings
- 15 atoms created from Feb 28 recordings
- First Century Fellowship arc formally created in Servetus
- Nick Bates formally documented as First Century co-founder
- Word in Film arc created; name corrected across vault
- 70 parked atoms migrated from Inbox to `02-daily-logs/`
- Both specs rewritten and committed to git (`personal` branch, commit `509f977`)
- Claude Code CLI established as primary Servetus session interface (new, March 1)
- Otter.ai mass download initiated — includes MP3s; ingestion on hold pending completion

## 5) Next Actions

### Immediate (next session)
- [ ] **Verify Otter mass download** — confirm all recordings and MP3s downloaded completely
- [ ] **Frontmatter migration script** — write Python script to flatten nested YAML to top-level keys across all vault `.md` files
- [ ] **Test in Obsidian Properties** — verify flat frontmatter works with database/properties feature
- [ ] **Canvas test** — drag atoms into Canvas, test filtering by `record_type` and arc tag

### Parked
- [ ] **Linux/panels:** Decide dock approach; apply `window-display-settings: 2` fix; add top panel on Cintiq; verify hwmonitor after restart
- [ ] **Otter audio:** Link retrieved `.m4a` files to witness folders once download complete; move DOCX source files from `Inbox/Otter.ai/` into witness folders
- [ ] **1st Century recording:** Check whether a second recording exists for remainder of Feb 28 evening (session ends mid-sentence at 21:44)
- [ ] **Ollama 70B:** First ingestion test — drop a raw DOCX at the model with only spec files as context
- [ ] **Watch folder design:** inotifywait vs systemd path unit; on-demand vs daemon
- [ ] **Obsidian excluded files:** Configure `.docx`, `.m4a`, `.zip` out of graph view
- [ ] **Git sync investigation:** Changes visible in Obsidian not appearing in git — diagnose cause (likely gitignore scope vs Nextcloud sync)
- [ ] **First Century:** Create agenda for first 4–5 Monday research nights
