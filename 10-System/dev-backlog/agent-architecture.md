---
type: backlog
title: "Agent Architecture — Specialists + Defaults"
slug: "agent-architecture"
status: open
priority: high
created: "2026-03-25"
circle: inner
---

# Agent Architecture

## Design Principle

The XO (Servetus) handles 50-75% of ops via script. Haiku for synthesis.
Sonnet/frontier model only for reasoning. Specialists invoked only when the
plan requires it — not by default.

## Agent Folder

`~/.claude/agents/`

## Planned Agents

| Agent | Domain | Notes |
|-------|--------|-------|
| `_defaults.md` | Security, guardrails, trust tiers | Inherited by ALL agents |
| `secretary.md` | Registers, calendar, radar, GTD | Calls secretary.py, Haiku synthesis |
| `biblical-research.md` | Bullinger rules, VPW corpus, Greek/Hebrew | No code context |
| `code.md` | Python, system architecture, scripts | No theology |
| `social-media.md` | Platform APIs, metrics, content calendar | Template + client profile |
| `nextcloud.md` | AIO, containers, Talk API, upgrade paths | Infrastructure SME |

## Template + Profile Pattern

Agents that serve multiple clients (social-media, biblical-research for ministry
deployments) use a template + profile pattern:

```
agents/social-media/AGENT.md     ← the engine
config/clients/binary-ranch/social-media.json   ← the profile
config/clients/first-century/social-media.json
```

Profile lives with the client, not with the agent.

## Defaults Layer

`_defaults.md` is inherited by every agent before its own context loads:
- Security posture
- Destination trust tiers
- No credential persistence
- No cross-client data
- Prompt injection awareness
- Agent boundary enforcement

## Routing

XO decides which agent to invoke based on the plan.
Planning step determines: handle directly or delegate to specialist.
Specialists report back to XO — they don't operate independently.

## Related

- `10-System/dev-backlog/context-packaging-spec.md`
- `10-System/dev-backlog/secretary-script.md`
- [[S00.01-05-00-servetus-guardrails]]
