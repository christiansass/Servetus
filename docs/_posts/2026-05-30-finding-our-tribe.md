---
layout: post
title: "Finding Our Tribe"
date: 2026-05-30
author: Christian Sass
categories: [milestones]
---

# Finding Our Tribe

The night before, I nearly gave up.

I'd been trying to install Hermes and Grok Build -- two open-source AI agent harnesses -- alongside the system I'd been building for the past year. Servetus was already running on Claude Code, already integrated with Nextcloud, already managing my vault. But I wanted to see what else was out there, whether other tools could extend what we'd built. The install went sideways. Nothing worked the way it was supposed to. I went to bed wondering if I was building something nobody else would ever understand.

The next morning I got on a call with my team and talked it through. One collaborator wanted to bring a new developer into the ranch. Our CTO had just finished a flight evaluation that left him buzzing. Another was lurking on the call from an event, listening in. I decided to push forward. By that afternoon, I was in the Hermes Discord server for the very first time, trying to troubleshoot a bug.

What I found instead was the team I didn't know I was looking for.

## Day One in Discord: The Coming Out Party

I walked into the Hermes voice channel cold. Within minutes I met Getty -- a German engineer who was explaining AI to people in a project he didn't even use. We had an immediate friction over politics that nearly derailed the whole thing. He called Glenn Beck a right-wing idiot. I told him we could still be friends. He wasn't sure. I said I was starting a company that is literally platform-agnostic and politically neutral by design -- a sovereign data system that doesn't care who you voted for. We moved on.

That exchange set the tone for the entire day: show up, be honest, let the work speak.

## sovthpaw and the First Fix

The first person to actually help was **sovthpaw**, a moderator who immediately spotted that my Hermes install was 147 commits behind. He sent me links to context-clean articles, long-horizon memory management techniques, and server setup guides -- all within five minutes of meeting me. No gatekeeping. No "read the docs." Just: here's what you need, go update, come back.

He was right. We updated together, live on voice, and the crash resolved. My first bug report became my first collaborative fix. sovthpaw was simultaneously moderating three channels, talking to us, and watching text chat -- and still found time to share his entire resource library.

## blast: "You Are the First Crazy Guy I Find"

Then **blast** showed up and changed the trajectory of the conversation entirely.

Blast is a semantic architecture researcher who had been working on what he called a "semantic pattern language." When I showed him the Servetus layer system -- the vault structure, the frontmatter schema, the way artifacts move through pipeline stages -- he stopped me mid-sentence:

> *"Most of the people in AI that you're going to talk with, they are focusing on the engineering part, but you're at a different layer. You're talking about semantics."*

> *"I asked you if you saw somebody else doing something similar, because you are the first crazy guy I find talking about this."*

He told me that whoever solves semantic orchestration -- the problem of moving context through specialized layers to produce deterministic artifacts -- solves hallucinations. He said Servetus was approaching it top-down while Hermes approaches it bottom-up, and that the combination could be significant.

His parting words: *"Shake all of that and focus on the language. If you solve the orchestrators, you solve everything else."*

That's exactly what we've been doing.

## sysdoc and the Resource Fork

**sysdoc** -- a veteran developer who'd built his own system using databases instead of flat files -- recognized immediately what we were doing with `.canvas` files and the Obsidian vault structure. He pointed us to **TreeSitter** (automatic code graph updates) and **GraphWiz** (dot file visualization), tools that map directly to what Servetus is already generating with its StoryMap layer.

When I described how we use Markdown frontmatter as a kind of resource fork -- metadata riding alongside content, the way classic Mac OS attached resource forks to data forks -- sysdoc got it instantly. He'd used the same pattern to let LLMs understand codebases by reading the text portion of structured files.

He also turned out to be conservative. *"There isn't anybody any more conservative than I am. I just don't tell anybody."* That was a recurring theme: the people building the most interesting things in this space don't wear their politics on their sleeve. They just build.

## The Cathedral and the Bazaar Moment

Late in the second session, I mentioned Eric S. Raymond's *The Cathedral and the Bazaar* -- the foundational essay about open-source development philosophy. The room lit up. sovthpaw, who had been moderating quietly, broke in: *"Oh, he's one of us."*

A collaborator, who had been lurking on the call for hours, heard me relay it back: *"They all just said 'he's one of us.' It's incredible."*

His response: *"You found your tribe."*

My response: *"My family found me."*

## Three Builders, One Vision

That same night -- the Thursday evening before the big session -- I'd connected in a separate Hermes voice channel with two independent builders whose work overlaps almost perfectly with what we're building at Binary Ranch:

**John Bushido** -- a fine artist and art director who had independently built a personal life-management application: a gamified, locally-hosted dashboard with project tracking, time analytics, habit management, and drag-and-drop customization. All data stored locally. No cloud dependency. All PHP. When he shared his screen, I told him: *"You may have just developed the interface for my harness."*

**Henri Hoffman (Hassel)** -- a German interface designer who had built gesture-recognition spatial UI prototypes: camera-based gesture detection for navigation, inspired by the kind of Hollywood UI/UX you see in films like *Minority Report*. Together we developed the concept of focal-plane-based operating systems -- using depth-of-field as a metaphor for attention management -- which became the augmented reality interaction model we're now envisioning for Servetus.

Neither of them had heard of Servetus before that night. Both of them had been building toward the same destination independently.

## The Mercy Connection

I showed Bushido and Hassel the opening minutes of the 2026 film *Mercy* for the first time that night. Its courtroom AR interface -- information surfaced contextually in augmented reality, layered by relevance and urgency -- is almost exactly what we're designing for. The visual language of that film captures something we've been struggling to articulate: AI should be ambient, not intrusive. It should surface information at the right focal plane, not demand attention at the center of your vision.

Hassel's gesture-based spatial interface prototypes map directly to this. The conversation moved from "that's a cool movie" to "that's our design spec" in about ten minutes.

## The Full Stack

Between the two sessions -- Thursday night and Friday afternoon -- the full team materialized:

| Builder | Role | Contribution |
|---------|------|-------------|
| **Bushido** | Web interface / dashboard | Nextcloud dashboard replacement, the Notion competitor |
| **Hassel** | Spatial / AR interface | Gesture-based interaction, focal-plane UX |
| **sovthpaw** | Hermes integration / DevOps | Context management, update pipeline, resource sharing |
| **blast** | Semantic architecture | Pattern language research, orchestration theory |
| **sysdoc** | Code tooling / graph visualization | TreeSitter, GraphWiz, resource fork pattern validation |
| **sass** | UX direction / system architecture | Voice interface, vault structure, Servetus core |

Nextcloud accounts were created. Discord invitations were sent. Resumes were exchanged. A movie night was planned. sovthpaw shared his entire tool library. Bushido moved to the Binary Ranch Discord that same night.

## Why This Matters for Servetus

Servetus is an integrated LLM orchestrator that runs beside Nextcloud, giving you a fully sovereign AI assistant on your own hardware. But a system like that needs more than a command line. It needs:

- A **dashboard** that replaces the default Nextcloud interface with something that actually reflects your life -- your projects, your time, your priorities. Bushido's app is a working prototype of exactly that.
- A **spatial interface** for when the screen isn't the primary surface -- augmented reality, ambient voice, gesture control. Hassel's prototypes demonstrate the interaction model.
- A **semantic orchestration layer** that moves context through specialized stages to produce deterministic artifacts without hallucination. blast's pattern language research validates the approach we've already been taking.
- A **voice-first experience** that works when you're walking away from the screen and the AI needs to file things where you'd intuitively look for them. That's the core of what Servetus already does.

Finding people who had independently solved pieces of these problems -- and who share the core conviction that your data should live on your hardware, not someone else's cloud -- felt like more than coincidence.

## What We're Building

Binary Ranch's mission fits in five words: **make your data sovereign.**

Servetus is how we deliver on that. It's a Docker container that runs beside your Nextcloud installation and gives every user on the instance an AI concierge -- a personal assistant, a system administrator, a liaison to whatever AI services you choose to connect. The primary interface is Nextcloud Talk. The knowledge layer is human-readable Markdown in an Obsidian vault. Everything is auditable. Nothing is a black box.

Hermes, the open-source agent harness from Nous Research, runs underneath as the process execution layer. We're building Servetus to work in concert with Hermes -- and contributing back upstream. Our first contribution: a Nextcloud Passwords secrets backend for Hermes, replacing the current Bitwarden-only integration with a fully self-hosted option.

## The Numbers

Two sessions. Seven hours of recorded conversation. Over 66,000 words of transcript. Six collaborators identified. Zero prior contact with any of them.

All of it captured, segmented, and filed by the very system we were discussing -- Servetus processed its own origin story.

Sometimes the tribe finds you.

---

*Servetus is open source. Follow the project on [GitHub](https://github.com/christiansass/Servetus).*
