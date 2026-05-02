---
type: backlog
title: "Ansible — Servetus Standalone Node Provisioning"
slug: "ansible-servetus-node"
status: future
priority: high
created: "2026-04-15"
circle: inner
---

# Ansible: Servetus Standalone Node

## Goal

A single Ansible playbook that provisions a minimal Linux installation into a
fully operational Servetus node — no desktop, no user session dependency, no
manual steps. Runs headlessly from boot.

## Target Environment

- Minimal Ubuntu/Debian server (no desktop environment)
- Eventually: container alongside Nextcloud AIO on BinaryRanch R420
- Near-term: testable on WordInFilm or a VM

## What the Playbook Must Provision

### Base System
- Xvfb (virtual framebuffer — required for Obsidian/Electron)
- Flatpak + Obsidian (or AppImage alternative)
- Python 3 + pip dependencies (talk-webhook.py requirements)
- Bun runtime
- `davidpp/obsidian-cli` (clone, build, install)
- Git

### Obsidian Plugins (pre-configured, no GUI interaction)
- Local REST API plugin — install + `data.json` with API key from vault
- Omnisearch plugin — install + enable HTTP server on port 51361

### Vault Access
- Mount or sync vault from Nextcloud (rclone or bind mount)
- Config files written from env vars or Ansible vault secrets

### Systemd User Services (with lingering enabled)
- `servetus-display.service` — Xvfb on `:1`
- `servetus-obsidian.service` — Obsidian headless on DISPLAY=:1
- `servetus-chromium.service` — Chromium headless, remote debug port 9222, logged into Nextcloud
- `servetus-vnc.service` — x11vnc mirroring display `:1` on port 5901
- `servetus-novnc.service` — websockify + noVNC web UI on port 6080 (browser VNC, no client needed)
- `servetus-talk-webhook.service` — talk-webhook.py HTTP listener
- `servetus-talk-listener.service` — notification poller (interim, pre-webhook)

### Oversight / VNC Access
- x11vnc mirrors Servetus' display `:1` (Obsidian, Chromium, everything)
- noVNC exposes it at `http://<host>:6080/vnc.html` — browser accessible over Tailscale
- No VNC client required — full visual oversight from anywhere on the Tailnet

### Linger
- `loginctl enable-linger <user>` — services survive logout, start on boot

### Credentials
- `config/nextcloud.env` — written from Ansible vault (never hardcoded)
- Obsidian Local REST API key — injected into plugin data.json
- Webhook secret — injected into talk-webhook.py environment

## Chromium "Eyes" Capability
- Chromium runs headless on `:1`, logged into Nextcloud
- Remote debugging on port 9222 allows screenshot capture, DOM inspection
- Enables Servetus to read notification bell visually if API falls short
- Playwright or Puppeteer for programmatic interaction

## Design Constraints
- No dependency on a logged-in desktop session (linger + headless only)
- Secrets never in playbook — all in Ansible vault or env
- Idempotent — safe to re-run for updates
- Some one-time authorizations require human-in-the-loop — playbook pauses and prompts

## One-Time Manual Steps (Installer Wizard)

These cannot be automated — playbook pauses and collects them interactively:

| Step | What the user does |
|---|---|
| Nextcloud bot account | Admin creates `servetus` user, sets password |
| Gmail app password | User generates in Google account settings, pastes in |
| Nextcloud Mail setup | User adds Gmail account in Nextcloud Mail app (IMAP + app password) |
| Browser notification permission | One-time Allow click after first browser launch |
| Webhook secret | Generated during `occ talk:bot:install`, captured automatically |
| Tailscale auth key | User provides ephemeral key for network enrollment |
| Domain whitelist | Admin reviews and approves default allowed domains |

Playbook prints a pre-flight checklist before starting:
"Have these ready before you run the installer."
After completion, prints any remaining manual steps with instructions.

## Related
- `10-System/dev-backlog/binaryranch-container-architecture.md`
- `10-System/dev-backlog/talk-bot-webhook.md`
- `~/.config/systemd/user/servetus-*.service` (WordInFilm — working reference)
