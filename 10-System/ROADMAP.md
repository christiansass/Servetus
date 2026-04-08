---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: spec
  pipeline_stage: canon
  status: active
  intent: plan

identity:
  title: "Servetus Roadmap"
  slug: "servetus-roadmap"
  record_id: "SV-20260406-NOW-CST-ROAD"

time:
  created_at: "2026-04-06T18:00:00-05:00"
  timezone: "America/Chicago"
  source_range: "ongoing"

keywords:
  - roadmap
  - versioning
  - milestones
  - sovereignty

tags:
  - servitus
  - roadmap
  - architecture
---

# Servetus Roadmap

> "The LLM is a tool Servetus uses, not a foundation Servetus depends on."
> — Named April 6, 2026

---

## Current: v0.2.1 — The Pile

Where we are. 31 scripts, 25 specs, 3 nodes, no unified runtime. Grew
organically to solve the next problem. It works, but it doesn't hold together
as a system. The human is the bus.

---

## v0.3 — The System Knows What It Is

**Theme:** Self-awareness. The system can describe itself, survive a provider
change, and maintain its own knowledge graph.

| Deliverable | Status | Notes |
|-------------|--------|-------|
| System map (`system-map.md`) | Done | 82 components inventoried |
| Architecture canvas (Obsidian) | Done | `servetus-architecture.canvas` |
| CalDAV library (`nextcloud_cal.py`) | Done | 7 calendars, LLM-agnostic |
| Talk dedup fix | Done | Content-based, 10s window |
| Talk listener → systemd | Done | Enabled for boot, auto-restart |
| SOC for today | Done | `2026-04-06_SOC.md` |
| Radar regenerated | Done | Was 18 days stale |
| LLM abstraction layer | **Not started** | Gating item — Anthropic is a provider, not the platform |
| Backlink repair (303 broken) | **Not started** | 34% link rot in vault |
| Version bump + push | Blocked on above | |

**Exit criteria:** Servetus can run its Talk bot against Ollama when Anthropic
is unavailable. Backlinks are under 5% breakage. System map is current.

---

## v0.4 — Sovereign Orchestrator

**Theme:** One daemon. One process. Every instance aware of every other.

| Deliverable | Notes |
|-------------|-------|
| `servetus-core/` package | nc_client, config, services/, tools/ |
| Unified daemon (`daemon.py`) | All services as managed threads in one process |
| Shared Nextcloud client | One auth, one HTTP client, all services use it |
| Cross-instance awareness | Heartbeats, shared ledger, no siloed sessions |
| Session brief that works | Auto-assembled from ledger, not from closing exchange |
| SOC auto-generation | Generated from all surfaces without manual trigger |
| Radar auto-regeneration | Scheduled, never stale |
| Service manifest | Which services on which node, how to restart |
| Talk bot → calendar integration | Bot can create/read events via nextcloud_cal |

**Exit criteria:** `systemctl --user start servetus` starts everything.
Any CLI session can see what every other surface is doing. SOC and radar
are always current.

---

## v0.5 — The Control Room

**Theme:** Visibility. The human stops being the MCP.

| Deliverable | Notes |
|-------------|-------|
| Control room Phase 2 (read-only) | Textual terminal UI or web dashboard |
| Node cards with live status | Heartbeat, CPU, RAM, GPU, services |
| Pipeline view | Hopper → Triage → Vault → Memory → Arc |
| Hopper gate control | Open/close the pipeline from the dashboard |
| Priority mode toggle | Personal ⟷ Cluster per node |
| Open loops sidebar | From SOC + cluster queue |

**Exit criteria:** Christian can glance at one screen and know the state of
the entire system. No SSH. No log tailing.

---

## v0.6 — The Control Room Goes Live

**Theme:** The gauges are also buttons.

| Deliverable | Notes |
|-------------|-------|
| Control room Phase 3 (interactive) | Service restart, queue management, rerouting |
| Credential rotation from dashboard | One click, all nodes updated |
| Cluster task management | Retry, skip, escalate from UI |
| Mobile-accessible | Nextcloud External App or responsive web |
| Presence layer (Track B) | notify_push WebSocket — true server-push |

**Exit criteria:** The dashboard replaces SSH for day-to-day operations.

---

## v0.7 — Multi-Agent

**Theme:** Scoped specialists. The OpenClaw pattern, sovereign.

| Deliverable | Notes |
|-------------|-------|
| Agent provisioning framework | Define agents with scoped permissions (Guardrails Rule 7) |
| Agent runtime enforcement | Agents can only access paths their definition allows |
| First specialist agents | Biblical research, social media, code review |
| Agent audit trail | Every agent action logged, reviewable |
| Client isolation enforced at runtime | Rule 5 — cross-client data never travels |

**Exit criteria:** Christian can say "research X" and a scoped agent handles
it without access to anything it shouldn't see.

---

## v1.0 — Sovereign Stack

**Theme:** No single point of failure. No vendor lock-in. Reproducible.

| Deliverable | Notes |
|-------------|-------|
| Containerized deployment | Docker/Podman, one-command deploy to any node |
| GPU node in colo | 4U AI box beside R420, full MCP authority |
| LLM fleet management | Anthropic, Ollama, LiteRT-LM — routed by capability and cost |
| Nextcloud plugin (control room) | Dashboard lives inside Nextcloud |
| Installable by others | README, install script, config wizard |
| Open source release | MIT, Binary Ranch org |

**Exit criteria:** Someone else can install Servetus on their Nextcloud
instance and have a working sovereign AI assistant.

---

## Principles (Apply to Every Version)

1. **The vault is the source of truth.** Not the LLM, not the config, not the
   cloud. The vault.

2. **The LLM is replaceable.** Today it's Claude. Tomorrow it could be Llama,
   Gemma, or something that doesn't exist yet. The architecture never assumes
   a specific provider.

3. **The human is informed, not involved.** The system handles operations. The
   human makes decisions. The gap between those two must shrink with every
   version.

4. **Sovereignty is non-negotiable.** Self-hosted. Self-owned. No data leaves
   without explicit consent through the trust tiers.

5. **Ship when it's ready.** Not on a schedule. Not when it's perfect. When the
   exit criteria are met.

---

## Related

- [[system-map]] — component inventory
- [[S00.01-19-00-servetus-control-room-spec]] — control room design
- [[servetus-architecture.canvas]] — visual architecture
- [[2026-04-06_SOC]] — current state of operations
