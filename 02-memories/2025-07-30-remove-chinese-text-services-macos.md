---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Remove Chinese Text Services from macOS Context Menu"
  slug: "remove-chinese-text-services-macos"
  record_id: "SV-20250730-NOW-CST-CHN0"

time:
  created_at: "2025-07-30"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - macos
  - services-menu
  - chinese
  - simplified-chinese
  - traditional-chinese
  - input-sources
  - system-settings

tags:
  - chatgpt-import
  - macos
  - reference

origin:
  source_file: "2025-07-30-Remove_Chinese_text_services.md"
  source_url: "https://chatgpt.com/c/6889972d-9094-832b-9829-6ee298b0ee93"
---

# Remove Chinese Text Services from macOS Context Menu

**Source:** 2025-07-30-Remove_Chinese_text_services.md
**Date:** 2025-07-30

## Summary

macOS shows "Convert to Simplified/Traditional Chinese" in the right-click Services menu. How to understand and remove these entries.

## Why They Appear

- macOS includes Chinese input methods/dictionaries by default for multilingual inclusivity
- Appear if Chinese (Simplified/Traditional) was ever enabled as a language or input source
- Harmless but clutters the context menu

## How to Remove

### Option 1: Remove from Input Sources
1. System Settings → Keyboard → Input Sources
2. Remove Chinese – Simplified / Chinese – Traditional (hit "–" button)

### Option 2: Services Menu Customization
1. System Settings → Privacy & Security → Extensions → All Extensions
2. Scroll to "Services"
3. Uncheck "Convert Text to Simplified Chinese" and "Convert Text to Traditional Chinese"

### Option 3: Language & Region
1. System Settings → General → Language & Region
2. Remove Chinese from preferred languages list if present

## Links / References

- Placement unconfirmed.
