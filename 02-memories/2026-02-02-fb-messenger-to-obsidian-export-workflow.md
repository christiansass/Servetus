---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Facebook Messenger to Obsidian — Export Workflow (JSON + Markdown)"
  slug: "fb-messenger-to-obsidian-export-workflow"
  record_id: "SV-20260202-NOW-CST-FBMS"

time:
  created_at: "2026-02-02"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - facebook-messenger
  - obsidian
  - export
  - json
  - markdown
  - archive
  - meta

tags:
  - chatgpt-import
  - infrastructure
  - obsidian
  - data-export

origin:
  source_file: "2026-02-02-FB_Messenger_to_Obsidian.md"
  source_url: "https://chatgpt.com/c/6980bed1-19b4-832f-8cd9-f29aa1999342"
---

# Facebook Messenger to Obsidian — Export Workflow (JSON + Markdown)

**Source:** 2026-02-02-FB_Messenger_to_Obsidian.md
**Date:** 2026-02-02

## Summary

Technical guide for extracting a complete Facebook Messenger history via Meta's data export and converting it to Obsidian-ready Markdown, including timestamps, sender names, and inline images.

## Key Points

- **Prefer JSON over HTML**: Meta's export includes Messages as JSON (most reliable) and sometimes HTML; JSON is the ground truth — HTML structure can change and is harder to parse robustly
- **Export from Meta**: Meta Accounts Center → Your information and permissions → Download your information → Messages, All time, High quality media, JSON format
- **Output target**: per-thread `.md` files with full sender names, human-readable timestamps, inline images (copied to Obsidian attachments folder), other attachments linked
- **Typical extracted paths**: messages in `messages/inbox/<thread>/` with `message_1.json`, images in subfolder
- **Python converter recommended**: script parses JSON, writes one `.md` per thread, copies media to Obsidian vault attachments folder
- **Key data preserved**: sender, timestamp, message body, photo/video links, reactions (as metadata), audio message links

## Workflow Summary

1. Request data download from Meta (takes minutes to hours to generate)
2. Download ZIP, extract
3. Run Python converter on `messages/inbox/` directory
4. Output lands in designated Obsidian folder
5. Review and route per Servetus pipeline

## Open Items

- Full Python script available in source file (59KB)
- Script not yet tested against actual Messenger export

## Links / References

- Placement unconfirmed.
