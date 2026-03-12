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
