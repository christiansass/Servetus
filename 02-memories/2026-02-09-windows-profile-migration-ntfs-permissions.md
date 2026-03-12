---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Windows Profile Migration — NTFS Permissions and FreeFileSync Pre-Wipe"
  slug: "windows-profile-migration-ntfs-permissions"
  record_id: "SV-20260209-NOW-CST-NTFS"

time:
  created_at: "2026-02-09"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - windows
  - ntfs
  - permissions
  - freefile-sync
  - robocopy
  - dropbox
  - profile-migration
  - drive-wipe

tags:
  - chatgpt-import
  - troubleshooting
  - infrastructure
  - windows

origin:
  source_file: "2026-02-09-Dropbox_folder_permissions_fix.md"
  source_url: "https://chatgpt.com/c/698a663b-c468-8325-906a-a95a5d01ca3e"
---

# Windows Profile Migration — NTFS Permissions and FreeFileSync Pre-Wipe

**Source:** 2026-02-09-Dropbox_folder_permissions_fix.md
**Date:** 2026-02-09

## Summary

Troubleshooting session for migrating a Windows user profile (Timothy Olaska, drive G:) before wiping the drive. FreeFileSync kept failing with `ERROR_CANT_ACCESS_FILE [CreateFile]` on Dropbox and other profile files. Root cause: overlapping Windows systems that cannot be cleanly unwound — orphaned AppContainer SIDs, OneDrive cloud placeholders, and intentionally protected Windows namespaces. Solution: abandon GUI sync tools; use robocopy with backup mode flag (`/ZB`), or Linux live USB.

## Root Causes (Three Overlapping Systems)

1. **Orphaned AppContainer SIDs** (`S-1-15-3-…`) — dead Microsoft Store / UWP account identities that still enforce ACLs; `CreateFile` fails even when file appears readable in Explorer
2. **Cloud reparse points** — OneDrive placeholder files that don't exist locally until OneDrive is running; `ERROR_CLOUD_FILE_PROVIDER_NOT_RUNNING`
3. **Windows protected namespaces** — `AppData\`, `WindowsApps\`, UWP folders; intentionally unreadable even by SYSTEM

## What Doesn't Work (and Why)

- `takeown /R` — touches every file one at a time; hours for a Dropbox profile; does not help cloud placeholders
- GUI inheritance removal — SIDs marked inherited cannot be removed without first converting inheritance to explicit, then re-enabling; even then some SIDs resist
- FreeFileSync — respects Windows APIs and therefore fails on all three root causes

## The Fix

### Option A — Robocopy (fast, Windows-native)
```cmd
robocopy "G:\Users\Timothy Olaska" "D:\Timothy Olaska" /E /R:0 /W:0 /COPY:DAT /DCOPY:T /XJ /ZB /LOG:C:\robocopy.log
```
- `/ZB` = backup mode, bypasses ACL enforcement
- `/COPY:DAT` = data, attributes, timestamps only (skips ownership/SID nonsense)
- `/XJ` = exclude junction points (prevents loops)
- `/R:0` = no retries on failed files

### Option B — Linux live USB
- Linux ignores Windows ACLs entirely; reads NTFS blocks directly
- Boot Ubuntu/Mint USB, mount G: and D:, copy folder, done

## What to Exclude (FreeFileSync or any sync tool)
```
\AppData\
\OneDrive\
\WindowsApps\
*.tmp
*.lnk
```

## Key Insight

> A modern Windows profile is not a folder. It's a composite of filesystem objects, cloud hooks, app sandboxes, and security identities. Windows is designed to keep that system intact while running, not to let it be cleanly copied or dismantled.

## Links / References

- Placement unconfirmed.
