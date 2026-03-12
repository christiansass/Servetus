---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Sync Apple Reminders with Nextcloud Tasks via CalDAV"
  slug: "sync-apple-reminders-nextcloud-caldav"
  record_id: "SV-20250909-NOW-CST-RMD0"

time:
  created_at: "2025-09-09"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - nextcloud
  - apple-reminders
  - caldav
  - ios
  - macos
  - tasks
  - sync

tags:
  - chatgpt-import
  - infrastructure
  - binary-ranch
  - reference

origin:
  source_file: "2025-09-09-Sync_Apple_Reminders_Nextcloud.md"
  source_url: "https://chatgpt.com/c/68c097c7-46b8-832a-9198-8d27b255d80a"
---

# Sync Apple Reminders with Nextcloud Tasks via CalDAV

**Source:** 2025-09-09-Sync_Apple_Reminders_Nextcloud.md
**Date:** 2025-09-09

## Summary

Research session on syncing Apple Reminders with Nextcloud Tasks. Primary method: native iOS/macOS CalDAV integration. Works but has known caveats.

## Method 1: Native CalDAV (Recommended)

**Setup on iOS:**
1. Ensure Nextcloud Calendar + Tasks apps are enabled
2. **Requires valid SSL cert** (Let's Encrypt) — iOS strictly rejects non-SSL or IP-based CalDAV
3. Settings → Calendar → Accounts → Add Account → Other → Add CalDAV Account
4. Enter Nextcloud domain, username, password (or app password)
5. Enable Calendars AND Reminders
6. In Settings → Reminders, set Nextcloud list as default (instead of iCloud)

## Known Caveats

- **Sub-tasks**: Appear as regular reminders (no hierarchy support)
- **Sync reliability**: Changes via web may not always sync back without re-adding account
- **macOS quirks**: Some versions (Big Sur/Catalina) had sync issues; mostly resolved in updates
- **iOS version quirks**: Early iOS 13 reports claimed CalDAV dropped; testing shows it still works
- **Domain cert matching**: Must use domain that matches SSL cert — local IP access will fail

## Links / References

- Placement unconfirmed.
