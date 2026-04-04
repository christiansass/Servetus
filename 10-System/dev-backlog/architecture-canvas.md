---
type: backlog
title: "Architecture Canvas — Full System Flowchart"
slug: "architecture-canvas"
status: open
priority: high
created: "2026-04-04"
circle: inner
---

# Architecture Canvas — Full System Flowchart

## Request

Christian wants a visual flowchart of the full current Servetus/BinaryRanch
system — all components, connections, and data flows mapped visually.
Purpose: start mapping how the system works so it can be communicated,
extended, and handed to partners (including NUPC).

## What to Map

### Nodes
- MacBook Pro (Claude Code primary, Tailscale 100.120.83.63)
- WordinFilm (Linux Mint, GPU, Tailscale 100.114.61.2)
  - servetus-whisper (transcription)
  - servetus-ollama (local LLM)
  - servetus-talk / talk-listener.py
  - servetus-secretary
  - servetus-display + chromium
- BinaryRanch R420 (GigeNET colo)
  - Nextcloud (cloud.binaryranch.com)
  - servetus-claude (cluster-router, pending deploy)
  - servetus-talk-br (pending deploy)
- Nextcloud vault (synced across all nodes via Nextcloud client)

### Data Flows
- Vault sync: MacBook ↔ Nextcloud ↔ WordinFilm
- Talk messages: NC Talk → talk-listener → Claude API → Talk reply
- Transcription: NC Talk audio → whisper queue → artifact → Talk notification
- Standup summary: transcription artifact → Claude Haiku → Standup room
- Cluster tasks: any node → cluster/queue/ → target node → cluster/results/
- Approvals: Talk APPROVE:/REJECT: → approval.py → authorized action

### Boundaries
- Tailscale mesh: MacBook + WordinFilm (personal tailnet)
- BinaryRanch: separate tailnet (not yet bridged)
- GigeNET private network: R420 ↔ NC VM (topology TBC with AJ)

## Output Format

Canva diagram (MCP available) or Mermaid flowchart in vault.
Canva preferred for sharing with NUPC and team.

## Related
- `10-System/system-info.md` — node registry
- `Toolkit/S00.01-15-00-servetus-container-architecture.md` — container map
- `10-System/cluster/README.md` — cluster bus design
