---
type: backlog
title: "Context Packaging Spec"
slug: "context-packaging-spec"
status: in-progress
priority: high
created: "2026-03-25"
circle: inner
---

# Context Packaging Spec

## What It Is

A formal spec defining how context is assembled, filtered, and packaged before
being sent to any LLM endpoint. The LLM receives a pre-resolved, minimal context
object — not raw vault data.

## Why It Matters

- Sensitive data never leaves sovereign infrastructure in raw form
- Prompt injection from Talk messages cannot reach data it was never given
- Cross-client data cannot leak — it was never packaged for that context
- Token cost drops — package is minimal by design
- Audit trail is clean — log exactly what was sent for any query
- Vendor-agnostic — package delivered to a configurable endpoint

## Design Principles

**Orientation is infrastructure. Reasoning is LLM.**
The packaging layer orients the LLM. The LLM does not orient itself.

**Send only what the query requires.**
Default package is minimal. Sensitive layers (witness data, sovereign context)
only enter the package if the query explicitly requires them AND the circle permits.

**Trusted vs. untrusted endpoints.**
- Trusted (self-hosted) → full natural language witness data, full context
- Untrusted (third-party API) → identifiers anonymized, relational weight abstracted

**Modular endpoint.**
The package is delivered to a configurable endpoint. Model and provider are
swappable via config. Architecture does not care if the endpoint is Claude,
GPT, Grok, or a local Ollama instance.

## The Four Layers

```
1. Script layer      → collect raw data from registers (no LLM)
2. Orient layer      → filter by context, apply disclosure rules
3. Package layer     → assemble minimal context object for this query
4. LLM layer         → receives package, reasons, responds
```

## What Goes Into a Package

| Data type | Included when | Notes |
|-----------|--------------|-------|
| Room/channel identity | Always | Determines circle |
| Requester identity | Always | Witness lookup, circle assignment |
| Effective circle | Always | Most restrictive of room + requester |
| Query text | Always | The actual question |
| Relevant arc summaries | When query touches an arc | Summary only, not full file |
| Witness parameters | When person is relevant to query | Natural language for trusted endpoint; abstracted for untrusted |
| Open loops | When query is operational/planning | Filtered to circle |
| Hopper items | When query is about new arrivals | |
| Radar items | When query is situational | |

## What Never Enters a Package

- Sovereign-tier personal assessments (your private take on a person/situation)
- Cross-client data (Binary Ranch data never in a First Century package)
- Raw credentials or tokens
- Full vault dumps
- Another person's witness file unless directly relevant and circle permits

## Endpoint Config

```json
{
  "reasoning_endpoint": "https://api.anthropic.com",
  "synthesis_endpoint": "http://localhost:11434",
  "model_reasoning": "claude-sonnet-4-6",
  "model_synthesis": "llama3.2",
  "trusted": true
}
```

`trusted: true` → send full natural language context
`trusted: false` → anonymize identifiers, abstract relational weight

## Audit Trail

Every package sent must be logged:
- Timestamp
- Requester
- Room/channel
- Effective circle
- Which data layers were included
- Which were excluded and why
- Model/endpoint used

Log lives at: `10-System/package-audit.log` (sovereign tier, never committed to Git)

## Related

- [[S00.01-06-00-servetus-disclosure-spec]] — circle rules enforced here
- [[S00.01-05-00-servetus-guardrails]] — destination trust tiers
- `10-System/dev-backlog/agent-architecture.md`
- `10-System/dev-backlog/secretary-script.md`
