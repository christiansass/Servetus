# Servetus

**A human-readable memory map for personal knowledge sovereignty.**

> *"There is no trust without truth, and there is no assistant without trust."*

**Current Version: 0.2.2** · [Changelog](CHANGELOG.md) · [Philosophy](Philosophy.md)

---

## What Is Servetus?

Servetus is a **memory map** — not a skill bolted onto an AI, but the sovereign architecture that any AI can read.

- **The map:** Your artifacts, memories, events, projects, arcs — in plain Markdown files you own
- **The engine:** Any LLM (Claude, GPT, local models) — borrows the map, doesn't own it
- **The floor:** Deterministic code replacing LLM behavior as each function is proven
- **The shell:** Conversation — the command interface for now, hardened code over time

When you switch AI vendors, the map remains. When the model hallucinates, the artifacts correct it. When the software fails, you open the folder and your life is still there.

**Servetus is not anti-AI. It is the safety net that makes AI usable without being dangerous.**

---

## Independent Validation

Servetus was designed without knowledge of [Fabric](https://github.com/danielmiessler/fabric), Daniel Miessler's open-source framework for augmenting humans with AI. The two projects independently converged on the same structural insight: **plain Markdown as behavior definition, AI as executor, humans in control of the process.**

The overlap is in the plumbing — how you tell an LLM what to do via text files. The divergence is in the thesis. Fabric solved *"how do I reuse good prompts."* Servetus is solving *"how do I trust what an AI tells me about my own life."*

That these projects arrived at the same file format from completely different problems isn't a coincidence — it's confirmation that the pattern is real and the need is wider than any single implementation.

---

## Why Servetus?

Modern AI tools store your life in opaque databases, process it through black-box models, and return interpretations you cannot verify.

**When the AI says "you discussed X with Y on Z date" — how do you know that's true?**

You don't. You trust the model. And models hallucinate.

Servetus solves this with a simple principle: every claim traces back to an artifact.

### The Artifact Chain

```
Reality (what actually happened)
    ↓
Artifacts (photos, audio, transcripts, screenshots — the tape)
    ↓
Memories (atomized thoughts extracted from artifacts)
    ↓
Events / Projects / Arcs (structured, organized, linked)
    ↓
AI Processing (interpretation, assistance, synthesis)
    ↓
Human Review (you see what was captured, you correct what's wrong)
    ↓
Reality Check (you can always go back to the artifact)
```

The AI sits in the middle of the stack, not at the top. It serves the system. It doesn't rule it.

### Corroboration Scores

Every claim carries a score — the number of independent witnesses and artifacts that point to the same conclusion. The score is a number. It does not reveal identities.

- **Score 1** — Testimony. One account. Handle with care.
- **Score 2** — Established. Two independent sources align.
- **Score 3+** — Confirmed. Geometrically solid.
- **Score 572** — 572 corroborating sources, sources private.

External verification (journalism, court records) gets a separate badge. Three witnesses with aligned artifacts outweigh one newspaper article.

---

## File System (Altitude Model)

Folders are numbered by zoom level — ground truth at the bottom, big picture at the top:

```
Servetus/
├── 00-inbox/             # Unsorted input — drop zone only
├── 01-artifacts/         # Raw proof — the tape (photos, audio, transcripts)
├── 02-memories/          # Atomized thoughts extracted from artifacts
├── 03-events/            # Discrete moments in time
├── 04-projects/          # Work clusters with deliverables
├── 05-arcs/              # Long-running narrative threads
├── 06-radar/             # Current viewport — what you're tracking now
├── 07-storymap/          # 30,000ft view — your full testimony
├── 08-witnesses/         # People whose stories touch yours (private intelligence)
├── 09-shared/            # What you publish, federate, or release
├── 10-system/            # Config, templates, specs, CLI
├── Toolkit/              # System specs (the instruction set)
└── config/               # User settings (gitignored for privacy)
```

**Altitude principle:** Artifacts anchor reality. Memories distill artifacts. Events aggregate memories. Arcs thread events. StoryMap renders everything.

---

## Core Data Model

| Type | Purpose | Folder |
|------|---------|--------|
| **Artifact** | Raw evidence — the tape (audio, photo, transcript, export) | 01 |
| **Memory** | One atomized thought extracted from an artifact | 02 |
| **Event** | A discrete moment in time | 03 |
| **Project** | Mid-length goal with deliverables | 04 |
| **Arc** | A long-running storyline (relationship, chapter, thread) | 05 |
| **Radar** | Your current lens — what you're actively tracking | 06 |
| **StoryMap** | The full map of your life | 07 |
| **Witness** | A person whose story touches yours | 08 |

All records are **plain Markdown** with **YAML frontmatter** — readable by humans, parseable by machines.

### Frontmatter (v0.2 — flat)

**Artifact** — origin fingerprint lives here, on the raw evidence:
```yaml
---
type: artifact
title: "Session — 2026-03-11"
slug: "2026-03-11-session"
date: 2026-03-11T14:30:00-06:00

origin:
  machine: "workstation"
  mac: "30:9c:23:8c:6e:04"
  ip: "10.0.0.109"
  os: "Linux Mint 22.3"

circles: []
published: false
tags: [session, artifact]
---
```

**Memory** — provenance inherited via `source_artifact`, no origin block needed:
```yaml
---
type: memory
title: "One idea, atomized"
slug: "one-idea-atomized"
date: 2026-03-11

source_artifact: "2026-03-11-session.md"
source_offset: "00:12:30"

linked_event: null
linked_project: null
linked_arc: null

circles: []
published: false
tags: [servetus, example]
---
```

---

## LLMs as Prototyping Environment

Servetus uses LLMs for one purpose: **to prototype functions we intend to replace with code.**

```
LLM obeys spec → behavior proven → spec becomes code → code committed to git
```

Every spec in `Toolkit/` is a ticket waiting to become a committed function. The vault is the whiteboard. GitHub is the destination. Code cannot hallucinate. Code does not consume tokens at runtime. Trust shifts from probabilistic to deterministic.

---

## Architecture Principles

### 1. Human-Readable Always
No proprietary formats. No opaque databases. Plain Markdown and YAML — readable by humans, parseable by machines. Where compiled code exists, its behavior is defined by specs you can read and verify. The goal is provable, deterministic code that replaces LLM functions once behavior is proven — code cannot hallucinate, and it runs without LLM processing.

### 2. Map vs. Engine
Servetus is a memory map, not a skill. The map exists independent of whichever AI reads it. Switch engines without losing memory.

### 3. AI as Prototyping Layer, Not Authority
LLMs prototype behavior. Proven behavior becomes code. Code becomes the system. The AI is scaffolding — useful until the structure can stand without it.

### 4. Sovereignty by Default
Your data lives on your infrastructure. Servetus orchestrates — it doesn't own.

### 5. Artifacts Are Memory
A photo, recording, or document is memory without explanation. It stands alone as evidence of a moment. Spoken or written thoughts become memories the moment they're captured. The artifact doesn't validate the memory — it *is* the memory. What changes with corroboration is not the memory's existence but its weight: one witness is testimony, two is established, three or more is confirmed.

### 6. Code Over Prompts
Proven behaviors become scripts. Scripts become the system. Prompts are scaffolding.

### 7. Every Folder Is a Watch Folder
Servetus must be aware of every file modification. Changes made inside Obsidian, on the command line, or by any tool are system events. A future Servetus daemon monitors all vault folders and notifies the system of modifications — so nothing changes silently.

---

## The Name

[Michael Servetus](https://en.wikipedia.org/wiki/Michael_Servetus) (1511–1553) was burned at the stake in Geneva. His crime: reading the biblical text and arriving at conclusions that contradicted the institutional interpretation.

We make no claim about who was right. What we observe: Calvin controlled the interpretation layer. Servetus had evidence and arguments. Calvin had the power.

**When it's one man's word against another, whoever controls the interpretation layer wins.**

Servetus (the system) ensures the interpretation layer is never controlled by a single authority — AI, institution, or otherwise. Artifacts are the check. Corroboration is the standard.

---

## Current Status: v0.2.1

**Implemented:**
- ✅ Altitude-based folder structure
- ✅ Artifact chain (every claim traces to evidence)
- ✅ Machine origin fingerprint on all records (machine/mac/ip/os)
- ✅ Local AI router (Ollama kernel + auto-escalation to Claude)
- ✅ PII scrub/rehydrate on external escalations
- ✅ Session logging (Q&A pairs auto-written to vault)
- ✅ Frontmatter schema (v0.2 flat format)
- ✅ Philosophy.md — fully merged and expanded
- ✅ Toolkit specs (bootloader, export rules, schema, time, spelling, routing)

**In Progress:**
- ⏳ Session-close script (`.jsonl` → artifact markdown, cross-platform)
- ⏳ Frontmatter migration script (v0.1 nested → v0.2 flat)
- ⏳ Corroboration score implementation
- ⏳ Voice capture pipeline
- ⏳ StoryMap visualization

---

## Integration Points

Servetus works with:

- **Nextcloud** — Files, Contacts (CardDAV), Calendar (CalDAV), federation layer
- **Obsidian** — Vault storage, graph view, templates, Canvas
- **Ollama** — Local AI kernel (private, offline-capable)
- **Any LLM** — Claude, GPT, Grok, Gemini — all treated as engines, not authorities
- **StoryMap.me** (future) — Web viewer for federated testimonies

---

## Quick Start

1. Clone this repo into your Obsidian vault location
2. Open in Obsidian
3. Run `bash Toolkit/local/install.sh` to deploy the local router
4. Read `Toolkit/S00.01-00-00-servetus-bootloader*` to understand the system
5. Customize `config/` with your projects and tags
6. Start capturing — drop artifacts in `01-artifacts/`, extract memories to `02-memories/`

For AI assistants: Read `CLAUDE.md` first (create locally from `SETUP.md` — gitignored).

Full setup guide: [SETUP.md](SETUP.md)

---

## Contributing

This is an open standard. We welcome:

- Feedback on the architecture
- Implementation experiments
- Integration proposals
- Philosophy discussions

Open an issue or submit a PR.

---

## License

MIT — because sovereign knowledge should be free.

---

*Servetus: A servant, not a master. A witness, not an authority.*
