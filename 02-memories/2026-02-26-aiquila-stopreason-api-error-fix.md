---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "AIquila stopReason API Error — Diagnosis and Fix"
  slug: "aiquila-stopreason-api-error-fix"
  record_id: "SV-20260226-NOW-CST-AQLA"

time:
  created_at: "2026-02-26"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - aiquila
  - nextcloud
  - claude-api
  - stopreason
  - bug-fix

tags:
  - chatgpt-import
  - infrastructure
  - nextcloud
  - ai
  - troubleshooting

origin:
  source_file: "2026-02-26-Aquila_API_Key_Error.md"
  source_url: "https://chatgpt.com/c/699fc3f8-9d54-8331-b478-c96d62245574"
---

# AIquila stopReason API Error — Diagnosis and Fix

**Source:** 2026-02-26-Aquila_API_Key_Error.md
**Date:** 2026-02-26

## Summary

While configuring AIquila (Nextcloud Claude integration plugin, labeled "Early Release" in the App Store), the user encountered a JavaScript error after successfully reaching the Anthropic API. The error was a field name mismatch — the plugin expected `stopReason` (camelCase) but the Anthropic Messages API returns `stop_reason` (snake_case). The API call itself succeeded; only the response parsing failed. Three fix paths were identified, with an update as the simplest.

## Key Points

- **Error:** `Property 'stopReason' does not exist in { "stop_reason": "end_turn", ... }`
- **Root cause:** AIquila's adapter layer reads `message.stopReason` but Claude Messages API returns `message.stop_reason`
- **Confirmation the API worked:** The response shape (`type: "message"`, `role: "assistant"`, content `"OK"`) was a valid successful API response
- **Plugin status:** AIquila is explicitly labeled "Early Release" — this type of breaking bug is expected
- **Fix Option 1 (easiest):** Update AIquila to latest version from Nextcloud App Store — maintainer may have already fixed the field name
- **Fix Option 2:** Verify provider mode — if pointing at Anthropic direct, must use native Anthropic handler (not OpenAI-compatible mode)
- **Fix Option 3 (workaround patch):** In the adapter JS/TS, change `message.stopReason` to `(message as any).stopReason ?? (message as any).stop_reason`
- **After fix:** The plugin connected but was underwhelming — see companion note on AIquila capabilities

## Open Items

- Whether the plugin was updated or patched was not confirmed in the session
- User gave it "a day" before deciding whether to uninstall

## Links / References

- Companion: [[2026-02-26--nextcloud-ai-stack-aiquila-capabilities--thread_export]]
- Source: [[Inbox/ChatGPT/2026-02-26-Aquila_API_Key_Error.md]]
- Placement unconfirmed.
