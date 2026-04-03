---
type: backlog
title: "Talk Bot — Webhook Endpoint"
slug: "talk-bot-webhook"
status: blocked
priority: high
blocking: "429 rate limits on concurrent long-polling"
blocked-by: "Nick to provision servetus.binaryranch.com"
created: "2026-03-25"
circle: inner
---

# Talk Bot Webhook

## Problem

Concurrent long-polling is hitting Nextcloud 429 rate limits.
Webhooks eliminate polling entirely.

## Action

Nick to provision `servetus.binaryranch.com` (or sub-path on existing infra).
Register via `occ talk:bot:install`.
Bot is built and waiting.

## Related

- `10-System/talk-listener.py`
- Open loop: Nick compensation conversation must happen before assigning critical deliverables
