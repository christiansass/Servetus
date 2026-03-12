---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Automator + ffmpeg — Steam Accessibility Popup Fix"
  slug: "automator-ffmpeg-steam-accessibility-fix"
  record_id: "SV-20251110-NOW-CST-AFF0"

time:
  created_at: "2025-11-10"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - automator
  - ffmpeg
  - macos
  - steam
  - accessibility
  - quick-action
  - video-conversion

tags:
  - chatgpt-import
  - troubleshooting
  - macos
  - scripting

origin:
  source_file: "2025-11-10-Script_error_fix.md"
  source_url: "https://chatgpt.com/c/690fac56-5310-8333-80b0-0ae8ab5ec88a"
---

# Automator + ffmpeg — Steam Accessibility Popup Fix

**Source:** 2025-11-10-Script_error_fix.md
**Date:** 2025-11-10

## Summary

Automator Quick Action (ffmpeg video converter) appeared to fail with an error. Root cause: not an ffmpeg error — Steam was throwing an macOS Accessibility permission request popup that interrupted the script execution.

## Root Cause

- Steam requests Accessibility permission when running
- This interrupts Automator Quick Actions and makes them appear to fail
- Actual ffmpeg script was fine

## Fix (Fast)

1. Quit Steam (or click Deny on the popup)
2. Re-run the Quick Action

**Permanent fix**: System Settings → Privacy & Security → Accessibility → disable or remove Steam

## Hardened Shell Script (Recommended for Automator)

```bash
#!/bin/bash

# Prefer Homebrew on Apple Silicon, fall back to Intel path or PATH
FFMPEG="/opt/homebrew/bin/ffmpeg"
[ -x "$FFMPEG" ] || FFMPEG="/usr/local/bin/ffmpeg"
[ -x "$FFMPEG" ] || FFMPEG="$(command -v ffmpeg)"

if [ ! -x "$FFMPEG" ]; then
  echo "ffmpeg not found. Install via: brew install ffmpeg"
  exit 1
fi

for f in "$@"; do
  out="${f%.*}.mp4"
  "$FFMPEG" -y -hide_banner -loglevel error -stats \
    -i "$f" \
    -map 0:v:0 -map 0:a? \
    ...
done
```

- Pass input: as arguments
- Full script in source file

## Links / References

- Placement unconfirmed.
