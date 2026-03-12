---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Cloudflare Error 600010 — CAFCU Login Fix"
  slug: "cloudflare-error-600010-cafcu"
  record_id: "SV-20260128-NOW-CST-CF60"

time:
  created_at: "2026-01-28"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - cloudflare
  - error-600010
  - cafcu
  - browser
  - login

tags:
  - chatgpt-import
  - troubleshooting
  - infrastructure

origin:
  source_file: "2026-01-28-Cloudflare_Error_Troubleshooting.md"
  source_url: "https://chatgpt.com/c/697a8682-fd40-8326-a0d9-417fbda1d655"
---

# Cloudflare Error 600010 — CAFCU Login Fix

**Source:** 2026-01-28-Cloudflare_Error_Troubleshooting.md
**Date:** 2026-01-28

## Summary

Cloudflare reference code 600010 blocked login to CAFCU (credit union). This is a Cloudflare access denial — not a username/password error — triggered by suspicious request signals (VPN, proxy, extensions, network reputation).

## Fix Steps (in order)

1. **Open Incognito window** and try login directly (skip saved bookmarks)
2. **Disable VPN / proxy / privacy relay** — this is the most common trigger
3. **Disable browser extensions** — uBlock, Brave Shields, Ghostery, NoScript
4. **Ensure cookies allowed** (including third-party if the login flow uses them)
5. **Try Chrome or Edge** if on Brave/Safari
6. **Clear only CAFCU site data** (not all cookies — targeted)
7. **Check device time/timezone** — auto-set required for secure sessions
8. **If still failing**: contact CAFCU with Cloudflare reference code 600010, time of error, public IP, and browser/device info

## Links / References

- Placement unconfirmed.
