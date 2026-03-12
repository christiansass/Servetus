---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Binary Ranch Server Security Checklist — David Weekly Review"
  slug: "binary-ranch-server-security-checklist-david-weekly"
  record_id: "SV-20250621-NOW-CST-SEC0"

time:
  created_at: "2025-06-21"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - binary-ranch
  - security
  - checklist
  - david-weekly
  - nick-bates
  - ryan-ritgarden
  - infosec
  - passkeys

tags:
  - chatgpt-import
  - binary-ranch
  - security
  - infrastructure

origin:
  source_file: "2025-06-21-Server_Security_Checklist.md"
  source_url: "https://chatgpt.com/c/6855fab2-7710-8007-99d8-198369ef54b7"
  project: "Binary Ranch"
---

# Binary Ranch Server Security Checklist — David Weekly Review

**Source:** 2025-06-21-Server_Security_Checklist.md
**Date:** 2025-06-21
**Project:** Binary Ranch

## Summary

Christian extracted all security concerns raised by David Weekly (also spelled "Weakley" in thread) and had them compiled into a report/checklist for delivery to three team members: Nick Bates (sysadmin), Raul (infosec), and Ryan Ritgarden (CTO).

## Note: "BinaryWrench" in thread — likely "Binary Ranch"

## Security Checklist (from David Weekly)

### Endpoint & Credential Security
- Use **phishing-resistant passkeys** (not just passwords)
- Enable 2FA/passkeys for Google accounts; avoid compromised login pages (e.g. google.hehe.cn example)
- **Hardware attestation required**: devices accessing sensitive data must be full-stack attested

### Preferred Hardware Platforms
- **Apple devices (preferred)**: Purchase directly from Apple; latest macOS/iOS; any device <8 years old if updated
- **Google Pixel (Android)**: Acceptable if regularly updated and directly sourced
- **⚠️ Windows**: Use with caution (details in full report)

### Additional Areas Covered
- Server hardening
- Network segmentation
- Access control policies
- (Full details in the source conversation transcript, not fully captured here)

## Report Audience

| Person | Role |
|--------|------|
| Nick Bates | System Administrator |
| Raul | InfoSec |
| Ryan Ritgarden | CTO / Primary Sysadmin |

## Notes

- Source: Conversation between Christian and David Weekly (June 20, 2025)
- Christian compiled this the following day
- David Weekly = external security advisor/reviewer

## Links / References

- See also: `2025-06-05--binary-ranch-team-role-alignment-strategy--thread_export.md`
