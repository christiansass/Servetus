---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Video Hero Cover Flow Carousel Component (React + oEmbed)"
  slug: "video-hero-coverflow-carousel-component"
  record_id: "SV-20260223-NOW-CST-VHCC"

time:
  created_at: "2026-02-23"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - react
  - coverflow
  - carousel
  - oembed
  - rumble
  - youtube

tags:
  - chatgpt-import
  - production
  - livestream
  - distribution
  - workflow
  - automation

origin:
  source_file: "2026-02-23-Hero_Section_with_Thumbnails.md"
  source_url: "https://chatgpt.com/c/699cca4e-f898-832c-96cf-d4a7afe3b29e"
---

# Video Hero Cover Flow Carousel Component (React + oEmbed)

**Source:** 2026-02-23-Hero_Section_with_Thumbnails.md
**Date:** 2026-02-23

## Summary

The user requested a hero section component that displays video thumbnails from multiple platforms (YouTube, Rumble, Odysee, PeerTube) in an iTunes-style Cover Flow carousel. Videos can be browsed left/right without scrolling and played inline on click. GPT produced a complete React implementation using oEmbed for thumbnail/embed resolution, with a Next.js server-side proxy to handle CORS. The component is production-ready with keyboard navigation noted as a suggested enhancement.

## Key Points

- **Component:** `VideoHero.tsx` (React) — 3D Cover Flow carousel, prev/next nav, inline player
- **Platform support via oEmbed:**
  - YouTube: `https://www.youtube.com/oembed`
  - Rumble: `https://rumble.com/api/Media/oembed.json`
  - PeerTube: `/services/oembed` (federated — works if instance exposes the endpoint)
  - Odysee: iframe URL transform (`/$/embed/` pattern) — no oEmbed thumbnail support, must supply manually
- **Architecture:** Client React component + `/api/oembed` Next.js proxy route (handles CORS, normalizes response shape)
- **Cover Flow math:** `translateX`, `translateZ`, `rotateY` per card based on distance from active index; max 4 cards visible per side
- **Player:** Renders `embedHtml` (full iframe from oEmbed) or falls back to `embedUrl` iframe
- **Odysee limitation:** Thumbnails not auto-resolvable — recommend supplying `thumbnailUrl` explicitly or adding OG-scraper server-side
- **Stack note:** Component is React/Next.js; a plain HTML version was offered but not generated

## Open Items

- Stack confirmation needed before full production use (React/Next.js assumed)
- Keyboard navigation (←/→ to browse, Enter to play) suggested but not implemented in session
- Odysee thumbnail resolution gap — OG scraper not included

## Links / References

- Source: [[Inbox/ChatGPT/2026-02-23-Hero_Section_with_Thumbnails.md]]
- Placement unconfirmed.
