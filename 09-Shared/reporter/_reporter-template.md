---
sv_schema: 2
sv_type: reporter_draft
sv_stage: inbox                          # inbox → distilled → canon → published
sv_status: draft                         # draft | approved | published | killed
sv_intent: capture

sv_created: "YYYY-MM-DD"
sv_timezone: "America/Chicago"
sv_id: "SV-YYYYMMDD-CST-RPTR-XXXX"
sv_slug: "YYYY-MM-DD-platform-short-title"
title: "Human-readable title for this draft"

# Reporter fields
reporter:
  destination: ""                        # key from config/reporter-destinations.json
  platform: ""                           # github | wordpress | static | nextcloud-collectives
  format: markdown                       # markdown | html | markdown_with_frontmatter
  session_source: ""                     # path to session log this was derived from
  version: 1                             # incremented on revision

# Sanitization audit trail
sanitization:
  pass_date: ""                          # ISO-8601 timestamp of sanitization pass
  pii_map_version: ""                    # date of pii_map.json used
  redactions: []
  # redactions example:
  #   - type: person_name
  #     original_context: "discussed with [redacted] about deployment"
  #     replacement: "discussed with a collaborator about deployment"
  #   - type: internal_path
  #     original_context: "filed in 02-Memories/"
  #     replacement: "[removed]"
  clean: true                            # false = uncertain redactions, needs human review

# Approval
approval:
  approved_by: ""                        # vault owner or named approver
  approved_at: ""                        # ISO-8601 timestamp
  approval_method: "manual"              # manual | talk-protocol
  notes: ""                              # any conditions or modifications requested

# Publication
publication:
  published_at: ""                       # ISO-8601 timestamp
  published_url: ""                      # final URL where this was published
  published_hash: ""                     # SHA-256 of published content for integrity

circles:
  read: public
tags: [reporter, draft]
---

<!-- TITLE: Replace with the post/release/update title -->

<!-- BODY: Write the publication content below this line.
     Everything above the fold is metadata. Everything below is what gets published. -->


