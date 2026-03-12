---
servitus:
  schema_version: 1
  system_version: 0.2.1
  record_type: event
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Servetus — Voice-to-Storymap Loop Explained to Ken"
  slug: "2026-02-28-servetus-voice-to-storymap-loop"
  record_id: "SV-20260228-1952-CST-VSL1"

time:
  created_at: "2026-02-28"
  timezone: "America/Chicago"
  source_range: "session"

keywords:
  - servetus
  - voice input
  - story maps
  - Obsidian
  - Miro
  - atomization
  - project management
  - AI
  - excalidraw
  - data organization
  - LLM
  - index cards

tags:
  - servitus
  - servetus-vision
  - voice-input
  - storymap
  - obsidian
  - atomization
  - project-management

provenance:
  source_file: "01-witnesses/2026/02-February/2026-02-28/2026-02-28-recording-evening-session.md"
  timestamp: "19:47:36"
  extracted: "2026-03-01"
---

# Servetus — Voice-to-Storymap Loop Explained to Ken

## Summary

During a screen-share session on February 28, 2026, Christian Sass explained to Ken Daniels the full architecture of how Servetus converts voice conversations into structured visual story maps — using Grok (AI) to articulate the concept, and a live Obsidian demo to show it.

The core insight: Servetus reverses the normal workflow. Instead of building structure first and filling it with ideas (the way Miro/Mural boards are built by hand), voice conversations create raw atoms of thought, and the structure emerges from the data itself.

## The "Wood Chipper" Framing

Christian's clearest articulation of the process:

> "I actually build these massive Miro boards... they are hand crafted, bespoke, manually designed collection scrap boards. Of me trying to put things in a chronological order. And what I'm trying to do is feed all of this into the service wood chipper and have Servetus arrange those boards automatically."

Grok's confirmation of the concept:

> "You're taking those massive, handcrafted Miro boards that you've been manually arranging, chronologically, feeding all that raw material into service like a wood chipper, and then having it automatically generate and organize those same types of visual story maps for you."

## The Full Loop (as described)

1. Voice conversation with an LLM is transcribed
2. The transcript is atomized — broken into discrete tagged markdown notes inside Obsidian
3. Each note captures one specific idea, decision, or insight with temporal markers and contextual links
4. Obsidian's graph view and linking structure creates visual connections between ideas — the same way a Mural board works, but dynamic and organic
5. At the story map level, an LLM uses Excalidraw to arrange the atomic notes into a visual layout

## The Index Card Metaphor

> "So this is one idea on an index card... I want only that idea in a stack of cards, and only this idea. Everything we said about this idea in its stack of cards... we atomize it, we split it up into its atomic structure. Here's all the plutonium, here's all the uranium. Anytime I'm talking about this topic, it's in one bucket... and it can link back to the original conversation it was pulled from, so you understand the context."

Conversation topics weave in and out — A, B, C, back to A, back to C. Atomization untangles this and sorts everything into thematic buckets, each with a link back to the source witness.

## Excalidraw + Canvas as the Story Map Surface

Christian demonstrated installing Excalidraw and Card Note as the first-ever plugins on the Servetus Obsidian instance (previously zero plugins, as of February 26 at 7:12 PM). The goal:

> "I want an LLM to use Excalidraw and line up all of my atomic notes."

The Canvas plugin (already enabled as default) allows atomic notes to be dragged into a visual workspace, interlinked, and ordered by the `created_at` timestamp extracted from frontmatter.

## Taxonomy: The Hierarchy

As explained live:

| Level | Description |
|-------|-------------|
| Story Map | 30,000-foot view — the entire canvas of a life or project |
| Arc | A section of the timeline (the "radar" is the current viewport) |
| Project | A named initiative (e.g., First Century Fellowship, Seven Talents, learning Linux) |
| Event | A specific occurrence within a project |
| Daily Log | Atomic notes — the index cards |
| Witness | Evidence files — audio, video, photo, screenshot |

## Jarvis / Iron Man Frame

> "I'm just trying to build a tool that makes me the most efficient person that I can be in these next two years. I've been working handicapped my entire life. This is me building my own robotic exo-skeleton. This is my Jarvis. This is my Iron Man suit."

Ken's response: "Which is exactly what I thought of — Tony Stark, flying through the air, talking to Jarvis."

## Related

- [[2026-02-28-recording-evening-session]] — source witness
- [[2026-02-28-mural-calendar-templates]] — Mural template workflow discussed in same session
- [[2026-02-28-audio-first-witness-philosophy]]
- [[2026-02-28-verbal-processor-memory-system]]
