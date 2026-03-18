---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: spec
  pipeline_stage: canon
  status: final
  intent: template

identity:
  title: "Servetus Front Matter Schema (MVP)"
  slug: "servetus-frontmatter-schema-mvp"
  record_id: "SV-20260116-NOW-CST-FMTR"

time:
  created_at: "NOW"
  timezone: "America/Chicago"
  source_range: "today"

keywords:
  - yaml
  - frontmatter
  - schema

tags:
  - servitus
  - schema
  - frontmatter
  - yaml
---

# Servetus Front Matter Schema (MVP)

## File Naming Convention

All Servetus content files use a `subject_type.md` underscore-separator pattern:

```
{subject}_{layer-type}.md
```

The layer type is the **full singular word** for the altitude layer:

| Layer | Type word | Example |
|-------|-----------|---------|
| `00-Artifacts/` | `artifact` | `phone-purchase-stream_artifact.md` |
| `01-Records/` | `record` | `tmobile-call-2026-03_record.md` |
| `02-Memories/` | `memory` | `verbal-processor-insight_memory.md` |
| `03-Events/` | `event` | `2026-03-16-vault-launch_event.md` |
| `04-Projects/` | `project` | `muxpilot_project.md` |
| `05-Arcs/` | `arc` | `binary-ranch_arc.md` |
| `06-Radar/` | `radar` | `tmobile-status_radar.md` |
| `07-StoryMap/` | `storymap` | `lifestream-lane_storymap.md` |
| `08-Witnesses/` | `witness` | `christian-sass_witness.md` |
| `09-Shared/` | `shared` | `servetus-overview_shared.md` |
| `10-System/` | `system` | `session-close_system.md` |
| `Toolkit/` | `spec` | `frontmatter-schema_spec.md` |

**Why underscore, not dot:** The folder already encodes the type. The underscore makes the type suffix visible as a label — not an extension — in every tool, script, and file manager. `os.path.splitext("binary-ranch_arc.md")` returns `.md` cleanly. Finder with extensions hidden shows `binary-ranch_arc`, which is unambiguously a name.

**Meta files** (templates, specs within a folder) keep their leading underscore prefixes: `_arc-template.md`, `_arc-spec.md`.

**The `slug` field** contains only the subject portion — no type suffix:
```yaml
identity:
  slug: "binary-ranch"   # ✓ correct
  slug: "arc-binary-ranch"  # ✗ redundant
```

---

## Required keys (minimum viable)
```yaml
---
servitus:
  schema_version: 1
  system_version: "<major.minor.patch>"   # Tracks which Servetus release this spec aligns with
  record_type: <daily_log|event|concept|method|spec|meta_dump|thread_export>
  pipeline_stage: <inbox|distilled|canon|published|archive>
  status: <draft|active|parked|final>
  intent: <capture|export|synthesis|reference|decision|plan|template>

identity:
  title: "<human title>"
  slug: "<kebab-case>"
  record_id: "<SV-YYYYMMDD-NOW-CST-XXXX>"

time:
  created_at: "<ISO-8601 OR NOW OR unknown>"
  timezone: "America/Chicago"
  source_range: "<today|thread|unknown>"

keywords:
  - "<keyword1>"
  - "<keyword2>"

tags:
  - "servitus"
  - "<domain tags...>"

# Optional: Origin (machine fingerprint)
origin:
  machine: "<human name or hostname>"   # from config/overrides.md machine_name, else hostname
  mac: "<aa:bb:cc:dd:ee:ff>"            # primary network interface MAC — hardware identity
  ip: "<outbound IP at session time>"   # IP when record was created — location context
  os: "<Linux Mint 22.3 | macOS 14.x | Windows 11>"  # disambiguates dual-boot sessions

# Optional: Radar (situational awareness)
radar:
  active: <true|false>         # Is this on radar?
  added: "<YYYY-MM-DD>"        # When it hit radar
  reason: "<why tracking>"     # Brief context
---
