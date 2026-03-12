---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Canon PRO-100 Printer — Linux Mint 22.3 Driver Fix (TurboPrint)"
  slug: "canon-pro100-linux-mint-driver-fix"
  record_id: "SV-20260227-NOW-CST-PRNT"

time:
  created_at: "2026-02-27"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - canon-pro-100
  - cups
  - linux-mint
  - turboprint
  - driver

tags:
  - chatgpt-import
  - hardware
  - linux
  - troubleshooting
  - infrastructure

origin:
  source_file: "2026-02-27-Canon_Pro_100_Printer_Help.md"
  source_url: "https://chatgpt.com/c/69a13589-0b8c-832f-9032-82c1211c4264"
---

# Canon PRO-100 Printer — Linux Mint 22.3 Driver Fix (TurboPrint)

**Source:** 2026-02-27-Canon_Pro_100_Printer_Help.md
**Date:** 2026-02-27

## Summary

The Canon PIXMA PRO-100 (8-ink dye photo printer, serial 2130ED) was not printing on Linux Mint 22.3 (Ubuntu 24.04 base) on machine WordInFilm. The root cause was a driver mismatch: the installed driver was Gutenprint S100, which is wrong for the PRO-100. Canon's official Linux driver (`cnijfilter2`) was built for Ubuntu 16.04/18.04 and breaks on Ubuntu 22.04+ due to missing 32-bit libraries. The session concluded with a decision to install TurboPrint (~$30–40), the professional paid driver that fully supports the PRO-100 on modern Linux with no compatibility hacks. The session ran in parallel with Claude Code and also via Ollama (which was unhelpful — user canceled that session).

## Key Points

- **Machine:** WordInFilm — Linux Mint 22.3 (codename "zena"), Ubuntu 24.04 base
- **Printer:** Canon PIXMA PRO-100 series, USB, serial 2130ED — detected correctly by CUPS
- **Wrong driver in use:** Canon S100 – CUPS+Gutenprint v5.3.4 — not correct for PRO-100
- **Two orphaned CUPS queues found:** `PRO-100-series` and `PRO_100_series_WordInFilm`
- **Root cause of breakage:** Canon's official `cnijfilter2` driver was built for Ubuntu 16.04/18.04; CUPS 2.4+ and Ubuntu 24.04 removed the 32-bit library compatibility it requires
- **Why it worked before:** `cnijfilter2` was previously installed; a Mint/CUPS upgrade removed it or orphaned the PPD
- **Gutenprint symptoms for PRO-100:** Job shows "Completed" with no output, blank pages, or silent failure — not a detection problem, a filter problem
- **Options evaluated:**
  - Gutenprint (free): poor / incomplete for PRO-100
  - Canon `cnijfilter2` with 32-bit hack (`dpkg --add-architecture i386`, install `libc6:i386`): messy, often still fails on 24.04
  - **TurboPrint (~$30–40): chosen** — fully supports PRO-100 on Mint 22, proper color management, no hacks
- **TurboPrint install steps:**
  1. Download `.deb` from turboprint.info (use newest Ubuntu package for Mint 22)
  2. `sudo dpkg -i turboprint_*.deb && sudo apt -f install`
  3. Run `turboprint` → Add Printer → select Canon PRO-100 series (USB)
  4. Delete old queues: `sudo lpadmin -x PRO-100-series && sudo lpadmin -x PRO_100_series_WordInFilm`
  5. Print test page from TurboPrint control panel
- **Demo mode:** TurboPrint adds watermark until license purchased — full functionality available for testing first
- **Color management note:** For photo work, match paper type, disable app-level color correction if using ICC profiles, let TurboPrint manage color pipeline

## Open Items

- TurboPrint installation not confirmed complete in session — user was directed to proceed
- License purchase pending
- Ollama session was also attempted in parallel but was unhelpful and canceled

## Links / References

- Source: [[Inbox/ChatGPT/2026-02-27-Canon_Pro_100_Printer_Help.md]]
- Related: Claude Code session also attempted printer troubleshooting prior to this
- Placement unconfirmed.
