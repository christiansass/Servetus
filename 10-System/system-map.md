---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: spec
  pipeline_stage: canon
  status: active
  intent: reference

identity:
  title: "Servetus System Map"
  slug: "system-map"
  record_id: "SV-20260406-NOW-CST-SMAP"

time:
  created_at: "2026-04-06T17:30:00-05:00"
  timezone: "America/Chicago"
  source_range: "today"

keywords:
  - system-map
  - architecture
  - components
  - inventory

tags:
  - servitus
  - architecture
  - system-map
---

# Servetus System Map

Generated 2026-04-06. Living document — update as components change.

---

## Nodes

| Node | Role | Hardware | Network | OS |
|------|------|----------|---------|-----|
| **WordInFilm** | GPU node, Talk bot, transcription | GTX 1080 Ti, 64 GB RAM | Tailscale 100.114.61.2 | Linux Mint 22 |
| **BinaryRanch R420** | Nextcloud host, colo | Dell R420, GigeNET DC | cloud.binaryranch.com | Ubuntu Server |
| **MacBook Pro** | Primary dev, Claude Code | Apple Silicon | Tailscale 100.120.83.63 | macOS |

---

## Services (Long-Running Daemons)

### WordInFilm

| Service | Script | systemd unit | Status | Purpose |
|---------|--------|-------------|--------|---------|
| Talk Listener | `talk-listener.py` | `servetus-talk-listener` | Running (manual PID) | Polls Talk rooms, calls Claude API, posts replies |
| Transcription Queue | `transcription-queue.py` | `servetus-transcription-queue` | Installed | Watches Talk/Audio for .mp3, runs Whisper, writes .md |
| Virtual Display | — | `servetus-display` | Active | Xvfb 1920x1080 on :1 |
| Persistent Chromium | `browser.py` | `servetus-chromium` | Active | Headless browser for browser agent, port 9222 |
| Cluster Router | `cluster-router.py` | — | Manual | Polls cluster/queue/, claims and executes tasks |
| Inbox Watcher | `inbox-watcher.py` | — | Manual | Watches Inbox/Otter.ai for new .docx |
| Shopping Agent | `shopping-agent.py` | — | Periodic | eBay/Amazon price monitor |

### BinaryRanch R420

| Service | Status | Purpose |
|---------|--------|---------|
| Nextcloud | Active | cloud.binaryranch.com — files, Talk, calendar, contacts |
| servetus-claude | Pending deploy | Cluster router for colo node |
| servetus-talk-br | Pending deploy | Talk listener instance for colo |

---

## Python Libraries (Importable Modules)

| Module | Purpose | Used by |
|--------|---------|---------|
| `nextcloud_cal.py` | CalDAV calendar read/write | Any component (NEW) |
| `cluster-dispatch.py` | Write tasks to cluster queue | talk-listener, CLI |
| `approval.py` | Two-factor approval via Talk | talk-listener |
| `vault_writer.py` | Write processed files into vault structure | inbox-triage, transcription-queue |
| `attachment_handler.py` | Process file attachments from Talk | talk-webhook |
| `persona-loader.py` | Load persona configs from Toolkit/personas/ | talk-listener, CLI |
| `conversation_logger.py` | Log conversations to vault | talk-listener |
| `nc-task.py` | Create Nextcloud Tasks via CalDAV | CLI, cluster tasks |

---

## CLI / One-Shot Tools

| Script | Purpose |
|--------|---------|
| `secretary.py` | Context assembly — reads all registers, outputs structured status |
| `inbox-triage.py` | Numbered triage list for hopper items |
| `inbox-scan.py` | Scan inbox for new files |
| `inbox-file.py` | File an inbox item to its destination |
| `radar.py` | Situational awareness: active threads, recent ingestion, upcoming |
| `standup-summary-today.py` | One-shot: watch for standup transcript, summarize, post |
| `talk-room-map.py` | Discover and map all Talk rooms to config |
| `talk-webhook.py` | Webhook handler for incoming Talk events |
| `list-active-arcs.py` | List all active arcs for context |
| `rotate-credentials.py` | Rotate Nextcloud app password, update env, revoke old |
| `otter-import.py` | Import Otter.ai transcripts |
| `servetus_cli.py` | Direct CLI interface to Servetus |
| `session-close.py` | Session close: write brief, capture metadata |
| `session-status.py` | Current session status |
| `launch-brief.py` | Generate launch brief for session start |
| `launch-menu.py` | Room picker / session resume menu |

---

## Shell / JS Scripts

| Script | Purpose |
|--------|---------|
| `~/bin/servetus` | Launcher: room pick → launch brief → Claude Code → session capture |
| `deploy-services-wordinfilm.sh` | Deploy systemd services to WIF via Tailscale SSH |
| `servetus-sleep.sh` | Clean shutdown of all Servetus processes |
| `restart-wisprflow.sh` | Restart Whisper transcription flow |
| `pre-commit-check.sh` | Git pre-commit hook |
| `statusline.sh` | Claude Code status line display |
| `claude-web-export.js` | Export conversations from Claude web UI |

---

## Ansible Playbooks

| Playbook | Target | Purpose |
|----------|--------|---------|
| `deploy-binaryranch.yml` | R420 | Deploy/update services on colo |
| `deploy-wordinfilm.yml` | WIF | Deploy/update services on homelab |

---

## Data Flows

```
                           ┌─────────────────────────────────┐
                           │     Nextcloud (BinaryRanch)     │
                           │  Talk · Files · Calendar · Tasks│
                           └──────────┬──────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                  │
                    ▼                 ▼                  ▼
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │ Talk Messages │  │ File Uploads │  │  Calendar    │
            │  (long-poll)  │  │  (NC sync)   │  │  (CalDAV)    │
            └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                   │                 │                  │
                   ▼                 ▼                  │
           ┌──────────────┐  ┌──────────────┐          │
           │talk-listener │  │inbox-watcher │          │
           │  (Claude API) │  │ (file watch) │          │
           └──────┬───────┘  └──────┬───────┘          │
                  │                 │                   │
                  ▼                 ▼                   │
           ┌──────────────┐  ┌──────────────┐          │
           │  Talk Reply   │  │   Hopper     │          │
           │  (NC Talk API)│  │ (events.log) │          │
           └──────────────┘  └──────┬───────┘          │
                                    │                   │
                                    ▼                   │
                             ┌──────────────┐          │
                             │ inbox-triage │          │
                             │  (user picks) │          │
                             └──────┬───────┘          │
                                    │                   │
                                    ▼                   ▼
                             ┌──────────────────────────────┐
                             │         Obsidian Vault        │
                             │  00-Artifacts  02-Memories    │
                             │  01-Records    05-Arcs        │
                             │  08-Witnesses  04-Projects    │
                             └──────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
             ┌───────────┐  ┌───────────┐  ┌───────────┐
             │  MacBook   │  │    WIF    │  │   R420    │
             │  (NC sync) │  │ (NC sync) │  │ (origin)  │
             └───────────┘  └───────────┘  └───────────┘
```

### Talk Message Flow (detailed)

```
User sends message in NC Talk
    → talk-listener.py (long-poll receives it)
        → content dedup check (NEW — 10s window)
        → is_addressed_to_me? (1:1 = always, group = @mention or Haiku classifier)
        → fetch thread history (last 12 messages)
        → load system prompt (bootloader specs + witness + talk state)
        → Claude API call (Sonnet 4.6)
        → post reply to Talk room
        → update witness file for speaker
```

### Transcription Flow

```
Talk call ends → recording .mp3 lands in NC Talk/Audio/
    → NC sync to WIF
        → transcription-queue.py (Whisper on GTX 1080 Ti)
            → .md transcript written to vault
                → hopper-events.log updated
                    → talk-listener surfaces to Christian
```

### Cluster Task Flow

```
Any component calls cluster-dispatch.py
    → JSON task written to 10-System/cluster/queue/
        → NC sync propagates to all nodes
            → cluster-router.py on target node claims task
                → executes (claude-code-run / summarize / talk-send)
                    → result written to 10-System/cluster/results/
                        → NC sync propagates result back
```

### Session Lifecycle

```
~/bin/servetus
    → launch-menu.py (room pick or resume)
        → launch-brief.py (context assembly)
            → Claude Code starts (bootloader-hook.py injects specs)
                → interactive session
                    → session-close.py (write brief, capture metadata)
                        → last-session-brief.md updated
```

---

## Cluster Bus

| Path | Purpose |
|------|---------|
| `10-System/cluster/nodes/` | Heartbeat files — presence = active |
| `10-System/cluster/queue/` | Pending tasks (JSON per task) |
| `10-System/cluster/results/` | Completed task results |
| `10-System/cluster/README.md` | Bus design doc |

Task types: `claude-code-run`, `summarize`, `talk-send`

---

## Config Files

| File | Purpose |
|------|---------|
| `config/nextcloud.env` | Credentials (NC URL, user, app password, Anthropic key) |
| `config/talk-rooms.json` | Talk room registry with circle mappings |
| `config/talk-cursor.json` | Per-room message cursor (dedup across restarts) |
| `config/projects.md` | Project routing rules |
| `config/overrides.md` | Local behavior overrides |

---

## Vault Structure

| Folder | Contents | Tier |
|--------|----------|------|
| `00-Artifacts/` | Produced works, exports | Sovereign |
| `01-Records/` | Transcripts, raw records | Sovereign |
| `02-Memories/` | Atomic knowledge notes | Sovereign |
| `03-Events/` | Discrete event records | Sovereign |
| `04-Projects/` | Active project folders | Sovereign |
| `05-Arcs/` | Narrative arcs | Sovereign |
| `06-Radar/` | Situational awareness | Sovereign |
| `07-StoryMap/` | Story mapping | Sovereign |
| `08-Witnesses/` | People files | Sovereign |
| `09-Shared/` | Public-safe exports (disclosure threshold) | Public |
| `10-System/` | All code, config, scripts | Controlled |
| `Toolkit/` | 44 governing specs | Controlled |

---

## Specs (Toolkit — 19 numbered)

| # | Spec | Governs |
|---|------|---------|
| 00 | Bootloader | Session init, spec load order |
| 01-00 | Export Rules | Output format for Obsidian exports |
| 01-10 | Topic Segmentation | Topic switch detection |
| 01-20 | Sorting & Placement | File routing and naming |
| 02-00 | Frontmatter Schema | YAML structure |
| 02-10 | Time Rules | Timestamps, timezone |
| 02-20 | Spelling Rules | Canonical names |
| 03-00 | Vault Search | obsidian CLI research protocol |
| 04-00 | Behavioral Rules | Tone, investigation, time, hopper |
| 05-00 | Guardrails | Destructive ops, trust tiers, memory routing |
| 06-00 | Disclosure Spec | Trust circles, who sees what |
| 07-00 | Migration Spec | Legacy vault migration |
| 07-00 | Witness Architecture | People file structure |
| 08-00 | Event Definition | Event record schema |
| 09-00 | Context Packaging | LLM context assembly |
| 10-90 | Session Start | Auto-triggers, inbox triage |
| 10-91 | Session Close | Close protocol |
| 11-00 | Server-Bot Parity | Feature parity across surfaces |
| 12-00 | Telegram Integration | Telegram bridge spec |
| 13-00 | Persistent Display | Xvfb + Chromium kiosk |
| 14-00 | Talk Approval Protocol | Two-factor approval via Talk |
| 15-00 | Container Architecture | Node deployment model |
| 16-00 | Collective Maintenance | System self-care |
| 17-00 | Talk Room Posting | Pre-post checklist for Talk |
| 18-00 | Interface Continuity | Single identity across surfaces |
| 19-00 | Control Room | Dashboard/cockpit spec |

---

## Component Count

- **3** nodes
- **7** long-running services (4 active, 3 pending/manual)
- **8** importable library modules
- **16** CLI/one-shot tools
- **6** shell/JS scripts
- **2** Ansible playbooks
- **25** governing specs
- **10** vault folders
- **5** config files

**Total tracked components: ~82**

---

## What's Missing / Next

- [ ] Node heartbeat files not being written yet
- [ ] BinaryRanch cluster-router not deployed
- [ ] No health check endpoints for services
- [ ] No service manifest (which services on which node, how to restart)
- [ ] No credential propagation across nodes (manual Ansible)
- [ ] No unified event bus (presence layer — Track B of nextcloud-mcp)
- [ ] Control room UI (Phase 2 of control-room-spec)

---

## Related

- [[S00.01-19-00-servetus-control-room-spec]] — UI spec
- [[S00.01-15-00-servetus-container-architecture]] — deployment model
- `10-System/cluster/README.md` — cluster bus
- `10-System/dev-backlog/architecture-canvas.md` — visual diagram backlog item
