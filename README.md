# Servetus

**The sovereign knowledge engine for Nextcloud + Obsidian + the Web.**

> *"There is no trust without truth, and there is no assistant without trust."*

---

## What Is Servetus?

Servetus is a **reality-grounded personal knowledge architecture** — an open standard for capturing, organizing, and preserving your life's context in a way that:

- **Remains human-readable** when all systems fail
- **Chains AI interpretations to verifiable evidence**
- **Keeps you sovereign** over your own memory

Servetus is not an AI assistant. It's the **memory architecture that AI assistants should write to** — and that you can audit, edit, and trust.

---

## Why Servetus?

Modern AI tools promise to remember everything for you. But they store your life in opaque databases, process it through black-box models, and return interpretations you cannot verify.

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

## Core Data Model

Servetus defines six fundamental record types:

| Type | Purpose |
|------|---------|
| **Event** | A discrete moment in time (meeting, photo cluster, conversation) |
| **Arc** | A long-running storyline (project, relationship, life chapter) |
| **Witness** | Evidence that grounds events in reality (photo, recording, transcript) |
| **Person** | Linked to CardDAV/Nextcloud Contacts with temporal relationships |
| **Daily Log** | Stream-of-consciousness capture, timestamped and tagged |
| **Project** | Mid-length goal with deliverables, connected to arcs and events |

All records are stored as **plain Markdown** with **YAML frontmatter** — readable by humans, parseable by machines, editable in any text editor.

---

## Architecture Principles

### 1. Human-Readable Always
If Servetus dies tomorrow, you open the folder in Obsidian (or any text editor) and your entire life is still there. No database exports. No proprietary formats. Just files.

### 2. Sovereignty by Default
Your data lives in **your** Nextcloud. Your notes live in **your** Obsidian vault. Servetus is the orchestration layer — it doesn't own anything.

### 3. AI as Servant, Not Authority
LLMs are useful tools for processing, summarizing, and retrieving. But they don't get to be the final word on what happened. That's above their pay grade.

### 4. Reflection Over Generation
Servetus is not about generating content. It's about **organizing your stream of consciousness** — capturing what you actually said, linking it to evidence, and making it findable.

### 5. Forensic Usability
Every record can be audited. Every AI interpretation can be checked against source material. If the model hallucinates, you have ground truth to compare.

---

## The Name

[Michael Servetus](https://en.wikipedia.org/wiki/Michael_Servetus) (1511–1553) was burned at the stake for heresy — not because he was wrong, but because he challenged the authority's interpretation of truth.

When it's one man's word against another, whoever controls the context window gets to declare heresy.

**LLMs are not neutral.** They're prediction engines that confabulate with confidence. Without a witness chain, you're trusting the institution to tell you your own story.

Servetus (the system) keeps any AI accountable to reality.

In the end, we let God be the judge — not the LLM.

---

## Current Status

**Phase: Specification / Whitepaper**

This repository contains:
- ✅ Data model definitions (Events, Arcs, Witnesses, People)
- ✅ Frontmatter schema (YAML standard for all records)
- ✅ Export rules (Obsidian-compatible Markdown output)
- ✅ Topic segmentation protocol
- ✅ Sorting and placement rules
- ✅ Time and spelling standards
- ✅ Multi-vault architecture design

**Not yet implemented:**
- ⏳ Voice capture pipeline
- ⏳ LLM orchestration layer
- ⏳ StoryMap visualization
- ⏳ Chronology plugin for Nextcloud

We're publishing the architecture now because **the concepts matter more than the code** — and the community needs to see what reality-grounded AI memory should look like.

---

## File Structure

```
/spec
  S00.01-00-00-servetus-bootloader.md
  S00.01-01-00-servetus-export-rules.md
  S00.01-01-10-servetus-topic-segmentation.md
  S00.01-01-20-servetus-sorting-and-placement-protocol.md
  S00.01-02-00-servetus-frontmatter-schema.md
  S00.01-02-10-servetus-time-rules.md
  S00.01-02-20-servetus-spelling-rules.md
  S00.01-10-00-project-index.md
  S00.01-10-10-project-tags.md
  S00.01-20-00-overrides.md

/docs
  architecture.md
  data-model.md
  witness-chain.md
  multi-vault.md
```

---

## Integration Points

Servetus is designed to work with:

- **Nextcloud** — Files, Contacts (CardDAV), Calendar (CalDAV), Tasks
- **Obsidian** — Vault storage, graph view, daily notes, templates
- **Any LLM** — Claude, GPT, Grok, local models — all treated as workers, not authorities
- **StoryMap** (future) — Multi-lane timeline visualization

---

## Contributing

This is an open standard. We welcome:

- Feedback on the data model
- Implementation experiments
- Integration proposals
- Philosophy discussions

Open an issue or submit a PR.

---

## Under Consideration

- **Config onboarding** — Setup guide for initial configuration (timezone, projects, tags, spelling preferences)
- **Split rules from values** — Cleaner separation between system specs (Toolkit) and user settings (config)

---

## License

MIT — because sovereign knowledge should be free.

---

## Links

- [Obsidian](https://obsidian.md) — The recommended knowledge management interface
- [Nextcloud](https://nextcloud.com) — The recommended self-hosted storage layer

---

*Servetus: A servant, not a master. A witness, not an authority.*
