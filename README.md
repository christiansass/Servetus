# Servetus

**A human-readable operating system for personal knowledge sovereignty.**

> *"There is no trust without truth, and there is no assistant without trust."*

**Current Version: 0.2.0** · [Changelog](CHANGELOG.md)

---

## Independent Validation

Servetus was designed without knowledge of [Fabric](https://github.com/danielmiessler/fabric), Daniel Miessler's open-source framework for augmenting humans with AI. The two projects independently converged on the same structural insight: **plain Markdown as behavior definition, AI as executor, humans in control of the process.**

The overlap is in the plumbing — how you tell an LLM what to do via text files. The divergence is in the thesis. Fabric solved *"how do I reuse good prompts."* Servetus is solving *"how do I trust what an AI tells me about my own life."*

That these projects arrived at the same file format from completely different problems isn't a coincidence — it's confirmation that the pattern is real and the need is wider than any single implementation.

---

## What Is Servetus?

Servetus is an **operating system where Claude is the kernel and the file system is the program.**

- **Kernel:** Claude (or any LLM) — processes instructions, executes operations
- **File system:** Plain Markdown in Obsidian — human-readable, no binaries
- **System libraries:** `Toolkit/` — specs that define behavior
- **User space:** `config/` — personal settings
- **Shell:** Conversation — the command interface

Everything is human-readable. When all systems fail, you open the folder and your entire life is still there.

---

## Why Servetus?

Modern AI tools store your life in opaque databases, process it through black-box models, and return interpretations you cannot verify.

**When the AI says "you discussed X with Y on Z date" — how do you know that's true?**

You don't. You trust the model. And models hallucinate.

Servetus solves this with a simple principle:

### **The Witness Chain**

Every claim traces back to evidence. Every event links to artifacts. Every memory can be verified against reality.

```
Reality (what actually happened)
    ↓
Witnesses (photos, audio, transcripts, screenshots)
    ↓
Structured Memory (human-readable Markdown with metadata)
    ↓
AI Processing (interpretation, assistance, synthesis)
    ↓
Human Review (you see what was captured, you correct what's wrong)
    ↓
Reality Check (you can always go back to the witness)
```

The AI sits in the middle of the stack, not at the top. It serves the system. It doesn't rule it.

---

## File System (Altitude Model)

Folders are numbered by zoom level — ground truth at the bottom, big picture at the top:

```
Servetus/
├── 00-system/            # System files, CLI, VERSION
├── 01-witnesses/         # Ground truth — artifacts, evidence (most zoomed in)
├── 02-daily-logs/        # Daily capture stream
├── 03-events/            # Discrete moments in time
├── 04-projects/          # Work clusters with deliverables
├── 05-arcs/              # Long-running narrative threads
├── 06-radar/             # Current viewport — what you're tracking
├── 07-storymap/          # 30,000ft view (most zoomed out)
├── Toolkit/              # System specs (the instruction set)
├── config/               # User settings (gitignored for privacy)
└── templates/            # Note templates
```

**Altitude principle:** Witnesses anchor reality. Events aggregate witnesses. Arcs thread events. Storymap shows the whole map.

---

## Core Data Model

| Type | Purpose | Altitude |
|------|---------|----------|
| **Witness** | Evidence that grounds events in reality (photo, recording, transcript) | 01 |
| **Daily Log** | Stream-of-consciousness capture, timestamped | 02 |
| **Event** | A discrete moment in time (meeting, conversation, photo cluster) | 03 |
| **Project** | Mid-length goal with deliverables | 04 |
| **Arc** | A long-running storyline (relationship, life chapter) | 05 |
| **Storymap** | The full map of your life | 07 |

All records are **plain Markdown** with **YAML frontmatter** — readable by humans, parseable by machines.

---

## System Queries

Ask the AI:

| Query | What happens |
|-------|--------------|
| "What version?" | Reads `00-system/VERSION`, reports current release |
| "What's new?" | Reads `CHANGELOG.md`, summarizes recent changes |
| "System status" | Reports version, structure health, config state |

---

## Architecture Principles

### 1. Human-Readable Always
No binary blobs. No compiled code. No proprietary formats. Just files.

### 2. File System IS the Program
Structure defines behavior. Move a file, change the system.

### 3. AI as Kernel, Not Authority
Claude executes instructions. You make decisions. The AI is a servant, not a master.

### 4. Sovereignty by Default
Your data lives in YOUR Nextcloud. Your notes live in YOUR vault. Servetus orchestrates — it doesn't own.

### 5. Version Everything
`00-system/VERSION` + `CHANGELOG.md` — know what you're running.

---

## The Name

[Michael Servetus](https://en.wikipedia.org/wiki/Michael_Servetus) (1511–1553) was burned at the stake for heresy — not because he was wrong, but because he challenged the authority's interpretation of truth.

**LLMs are not neutral.** They're prediction engines that confabulate with confidence. Without a witness chain, you're trusting the institution to tell you your own story.

Servetus (the system) keeps any AI accountable to reality.

---

## Current Status: v0.2.0

**Implemented:**
- ✅ Altitude-based folder structure
- ✅ Witness template with time-bound exhibits + validity scoring
- ✅ Radar system for situational awareness
- ✅ VERSION file for system queries
- ✅ Frontmatter schema with radar properties
- ✅ System specs (Toolkit) separated from user config
- ✅ Sharing model spec (future architecture)

**In Progress:**
- ⏳ Voice capture pipeline
- ⏳ StoryMap visualization
- ⏳ Multi-user witness validation
- ⏳ Permission layers for shared storymap

---

## Integration Points

Servetus works with:

- **Nextcloud** — Files, Contacts (CardDAV), Calendar (CalDAV)
- **Obsidian** — Vault storage, graph view, templates
- **Any LLM** — Claude, GPT, local models — all treated as kernels, not authorities
- **StoryMap** (future) — Social layer with granular permissions

---

## Quick Start

1. Clone this repo into your Obsidian vault
2. Open in Obsidian
3. Read `Toolkit/S00.01-00-00-servetus-bootloader*` to understand the system
4. Customize `config/` with your projects and tags
5. Start capturing in `02-daily-logs/`

For AI assistants: Read `CLAUDE.md` first — it contains the full system context, operating rules, and epistemological stance.

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
