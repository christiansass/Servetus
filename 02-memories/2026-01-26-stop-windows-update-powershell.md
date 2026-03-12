---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Stop Windows 10 Update via PowerShell"
  slug: "stop-windows-update-powershell"
  record_id: "SV-20260126-NOW-CST-WUPD"

time:
  created_at: "2026-01-26"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - windows-10
  - windows-update
  - powershell
  - wuauserv
  - sfc
  - dism

tags:
  - chatgpt-import
  - troubleshooting
  - windows

origin:
  source_file: "2026-01-26-Stop_Windows_Update_PowerShell.md"
  source_url: "https://chatgpt.com/c/697785ac-e008-832d-bd9d-ba100f6a2a04"
---

# Stop Windows 10 Update via PowerShell

**Source:** 2026-01-26-Stop_Windows_Update_PowerShell.md
**Date:** 2026-01-26

## Summary

PowerShell commands to stop a Windows 10 automatic update in progress when the GUI provides no options.

## Commands (Run PowerShell as Administrator)

### 1. Stop the Windows Update service immediately
```powershell
Stop-Service -Name wuauserv -Force
```
Also stop related services if it restarts itself:
```powershell
Stop-Service -Name bits -Force
Stop-Service -Name cryptsvc -Force
Stop-Service -Name msiserver -Force
```

### 2. Prevent Windows Update from restarting
```powershell
Set-Service -Name wuauserv -StartupType Disabled
Set-Service -Name bits -StartupType Disabled
```

### 3. Clear staged update files (if update already queued)
Delete contents of `C:\Windows\SoftwareDistribution\Download\` — this removes queued update files so Windows must re-download before re-attempting.

### 4. To re-enable Windows Update later
```powershell
Set-Service -Name wuauserv -StartupType Automatic
Start-Service -Name wuauserv
```

## Links / References

- Placement unconfirmed.
