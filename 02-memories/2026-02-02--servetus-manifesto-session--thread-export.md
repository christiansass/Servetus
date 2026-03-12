---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: thread_export
  pipeline_stage: distilled
  status: final
  intent: capture

identity:
  title: "Servetus Manifesto Session"
  slug: "servetus-manifesto-session"
  record_id: "SV-20260202-SESSION-CST-MANF"

time:
  created_at: "2026-02-02"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - servetus
  - manifesto
  - architecture
  - sovereignty
  - context
  - artifact-witness
  - interoperability

tags:
  - servetus
  - session
  - manifesto
  - architecture
  - v0.2.1
---

# Servetus Manifesto Session — 2026-02-02

## Session Summary

Major working session that produced:
1. v0.2.1 release (Toolkit filename cleanup)
2. The "Own Your Mind" manifesto (`docs/WHY.md`)
3. Artifact/Witness Architecture spec (`S00.03-00-00`)
4. Clarification of architect/contractor relationship

---

## Part 1: System Boot & Cleanup

### Booted Servetus
- Version: 0.2.0 → 0.2.1
- Loaded Toolkit specs, config files

### Toolkit Filename Convention Change
**Decision:** Remove date suffixes from filenames, track version in frontmatter instead.

Before:
```
S00.01-00-00-servetus-bootloader(2026-01-16).md
```

After:
```
S00.01-00-00-servetus-bootloader.md
```

Frontmatter now includes:
```yaml
servitus:
  system_version: 0.2.1
```

**Rationale:** "Current" matters more than "when touched." Version alignment tracked in frontmatter, not filenames.

**Commit:** `927e3f9` - "Clean up Toolkit filenames and add version tracking (v0.2.1)"

---

## Part 2: The Value Proposition Problem

### Doug's Feedback
Friend Doug doesn't understand the high-level narrative. Why would this be important to him? How does it improve his life?

### Three Initial Framings

**1. The Scattered Life Problem**
> Your life is scattered across 47 apps. Every app is a silo. Every silo forgets. You can't search your own life.

**2. The Goldfish Assistant Problem**
> Every time you talk to ChatGPT, it forgets who you are. You explain your job again. Your projects again. Your preferences again.

**3. The Digital Sovereignty Problem**
> You don't own your digital life. Google owns your email. Apple owns your photos. Notion owns your notes. They can change the rules, raise prices, or disappear.

**Verdict:** All three are valid. Need to weave together.

---

## Part 3: The Deeper Vision

### Context Sovereignty (Core Insight)
> All of these different silos, all of these different locations that are doing capture all have a piece of you.

The real vision:
- Own ALL your context, not scattered across silos
- Local context manager with situational awareness
- Knows all the puzzle pieces and how they connect
- Provides relevant context to LLMs
- Revokes the mandate to store after use
- Clean up after yourself → no footprint

> "If we have no fear of deleting our GPT account then we know that we own the context."

### The Hostage Situation
> If Facebook deleted your account tomorrow, it would be like your house burning down.

Platforms hold your history hostage. You can't leave because leaving means losing yourself.

### The Exile (Key Insight)
> When they ban you, they don't delete your data. They take you away from it.

- Profile still exists, archived
- They could restore it with a keystroke
- But no human will help you
- **It's not deletion. It's separation.**
- You lose access; they keep the intelligence

Friend's experience: Twitter down, Facebook down. Not political. No recourse. Data confiscated, not destroyed.

### The Asymmetry

| You                  | They                |
| -------------------- | ------------------- |
| Lose access          | Keep everything     |
| No recourse          | Full control        |
| Can't export         | Can analyze         |
| Erased from platform | Your shadow remains |

### The Hairdresser Attack
> ChatGPT, Claude, Gemini — they're designed to earn your trust. To get you talking. Like a therapist. Like a hairdresser. That's not a feature. That's an extraction operation.

### The OSINT Inversion
> The ultimate open-source intelligence is the one you contribute to.

You should have more command of your own data than any third party. If you can analyze someone else's patterns, why can't you do that for yourself?

---

## Part 4: The Security Framing

> Technology is only scary when others have more command of it than you do.

Servetus provides:
- Forensic self-awareness
- Ability to analyze your own patterns, conversations, trajectory
- Off-platform, on your own machine
- See yourself the way an analyst would — for your own benefit

---

## Part 5: LLM Independence

### The LLM Is Irrelevant
> If you own the context, the model becomes interchangeable.

Claude isn't the point. The value is in YOUR context. The LLM is just a processing layer.

### Rules Persist Too
Any LLM that enters the scene inherits YOUR rules:
- How exports are formatted
- How time is handled
- What stays private

**The rules govern the model. Not the other way around.**

---

## Part 6: Artifact/Witness Architecture

### Core Insight
The artifact and the meaning are two separate things.

- **Artifact:** The raw file (photo, document, export)
- **Witness:** The metadata wrapper (meaning, relationships, time envelope)

### Resource Fork Model
Like classic Mac OS:
- Artifact = data fork (can be externalized)
- Witness = resource fork (lightweight, shareable, queryable)

### Revised Altitude Model
```
00 — SYSTEM (Toolkit, config)
01 — ARTIFACTS (raw files, externalizable)
02 — WITNESSES (metadata wrappers)
03 — DAILY-LOGS
04 — EVENTS
05 — PROJECTS
06 — ARCS
07 — RADAR
08 — STORYMAP
```

### Interoperability
Standardized schema enables:
- Graph merging where they overlap
- Timeline corroboration across sources
- Relationships traversing independent vaults
- No central platform required

**Not a platform. A protocol.**

### Platform Independence
Because the final data store is just files:
- OS independent (Mac, Windows, Linux)
- Platform independent (Obsidian, VS Code, any editor)
- Hardware independent (local, NAS, cloud)
- LLM independent (Claude, GPT, Llama, future)

> The spec is the contract. Everything else is implementation.

---

## Part 7: Architect/Contractor Clarification

### The Relationship
- **User:** Architect. Has the vision. Has been thinking about this for 1-2 years.
- **Claude:** Contractor. Writes code. Translates intent into function.

### Key Insight
> I'm not asking you to think up anything. I'm asking you to help me execute.

What feels like "new ideas" to Claude are actually refined output of 1-2 years of thinking. Claude is catching up, not building alongside.

The continuity lives in the Obsidian vault, not in any LLM's memory. Claude is just the current processor.

---

## Artifacts Produced

1. **v0.2.1 Release**
   - 10 Toolkit files renamed
   - Frontmatter updated with `system_version`
   - CHANGELOG updated
   - Committed: `927e3f9`

2. **docs/WHY.md**
   - Full "Own Your Mind" manifesto
   - Value proposition narrative

3. **Toolkit/S00.03-00-00-artifact-witness-architecture.md**
   - Artifact/witness separation spec
   - Revised altitude model
   - Interoperability framework

4. **This thread export**

---

## Pending Items

- [ ] Dallas Jenkins / Emmaus script follow-up (accidentally pasted, to revisit)
- [ ] Process historical Obsidian archive (1-2 years of curated context)
- [ ] Turn Claude loose on its own history

---

## Key Quotes

> "There is no trust without truth, and there is no assistant without trust."

> "If you're not afraid to delete your accounts, you're free."

> "They can exile you from the platform. They can't exile you from your own files."

> "Technology is only scary when others have more command of it than you do."

> "The spec is the contract. Everything else is implementation."

> "You own the rules. You own the context. The LLM is a guest."

---

## Links / References

- [[docs/WHY]]
- [[Toolkit/S00.03-00-00-artifact-witness-architecture]]
- [[Toolkit/S00.01-00-00-servetus-bootloader]]
- [[CHANGELOG]]
- [[00-system/VERSION]]
