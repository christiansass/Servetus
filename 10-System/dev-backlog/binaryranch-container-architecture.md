---
type: backlog
title: "BinaryRanch Container Architecture — Servetus Production Target"
slug: "binaryranch-container-architecture"
status: future
priority: medium
blocked-by: "BinaryRanch Tailnet access, Nick compensation conversation"
created: "2026-04-15"
circle: inner
---

# BinaryRanch Container Architecture

## Context

WordInFilm (homelab, GTX 1080 Ti) is the current proving ground for Servetus tooling.
Production target is BinaryRanch R420 (colo), running containers alongside Nextcloud AIO.

## Target Layout

Three containers on BinaryRanch:

| Container | Contents | Notes |
|---|---|---|
| `nextcloud-aio` | Nextcloud (existing) | Already running |
| `servetus-bot` | `talk-webhook.py` | Lightweight — Python only, no display needed |
| `servetus-vault` | Headless Obsidian + Xvfb + Local REST API + Omnisearch | Electron app requires virtual display |

## Key Constraint

Obsidian is an Electron app — requires a display even headless.
`servetus-vault` must include Xvfb. Vault directory bind-mounted from Nextcloud storage.

## servetus-vault Container Requirements

- Xvfb (virtual framebuffer)
- Obsidian (Flatpak or AppImage)
- Local REST API plugin (pre-configured, API key in env)
- Omnisearch plugin (HTTP server enabled, port 51361)
- `davidpp/obsidian-cli` binary
- Vault bind-mounted from Nextcloud data path
- Internal network reachable by servetus-bot

## servetus-bot Container Requirements

- Python 3
- `talk-webhook.py`
- Access to vault (via bind mount or servetus-vault API)
- Webhook registered via `occ talk:bot:install` pointing to container internal address
- Env: `NEXTCLOUD_URL`, `NEXTCLOUD_USER`, `NEXTCLOUD_APP_PASSWORD`, `ANTHROPIC_API_KEY`, `WEBHOOK_SECRET`

## Current State on WordInFilm

- Obsidian running with Xvfb on display `:1`
- Local REST API plugin live on port 27124 (HTTPS)
- Omnisearch plugin live on port 51361 (HTTP)
- `davidpp/obsidian-cli` installed at `~/bin/obsidian`, fully operational
- talk-webhook.py registered but not yet deployed as service (BinaryRanch unreachable via Tailnet)

## Blocked By

- BinaryRanch not on same Tailnet as WordInFilm
- Nick compensation conversation (before assigning critical infrastructure deliverables)

## Related

- `10-System/dev-backlog/talk-bot-webhook.md`
- `10-System/talk-webhook.py`
- `02-Memories/2026-03-23-talk-bot-webhook-architecture.md`
