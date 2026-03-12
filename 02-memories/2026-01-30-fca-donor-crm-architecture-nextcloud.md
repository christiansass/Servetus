---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "FCA Venice — Donor CRM Architecture and Nextcloud as CRM Option"
  slug: "fca-donor-crm-architecture-nextcloud"
  record_id: "SV-20260130-NOW-CST-FCAC"

time:
  created_at: "2026-01-30"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - fca
  - crm
  - bloomerang
  - blackbaud
  - nextcloud
  - nonprofit
  - donor-management
  - seven-talents
  - binary-ranch

tags:
  - chatgpt-import
  - infrastructure
  - business
  - nextcloud

origin:
  source_file: "2026-01-30-FCA_Digital_Support_CRM.md"
  source_url: "https://chatgpt.com/c/697bf26e-dd24-8326-8295-8031b6b04105"
---

# FCA Venice — Donor CRM Architecture and Nextcloud as CRM Option

**Source:** 2026-01-30-FCA_Digital_Support_CRM.md
**Date:** 2026-01-30

## Summary

A friend reached out asking if Christian would help FCA (Fellowship of Christian Athletes, Venice, Florida) with digital/social support and a CRM overhaul. They're using Bloomerang + Blackbaud + Waypoint, and the integration glue is costing $1,500. Session explored CRM architecture options and whether Nextcloud could serve as a viable donor CRM.

## FCA Context

- Fellowship of Christian Athletes — international nonprofit sports ministry, founded 1954, Kansas City HQ
- Structured regionally and locally; local ministries have autonomy
- Gulf Coast FCA (Sarasota/Manatee/Charlotte counties): 1,000+ students involved
- Florida FCA: 52,358 faith decisions, 19,431 certified huddles, 196,024 Bibles distributed
- The specific request appears to be from a local/regional entity — scope TBD

## CRM Architecture Options (Evaluated)

**Option A** — Keep Bloomerang as donor system of record; replace Blackbaud glue with Make.com/n8n automation → recommended starting point; likely eliminates the $1,500 line item

**Option B** — WayPoint as operational hub, giving platform handles payments, donor CRM handles history; works only if WayPoint is truly central

**Option C** — HubSpot + Stripe + automation (modern rebuild); clean segmentation, donor journeys, no nonprofit stack tax

**Option D** — "Giving platform does it all" (leanest for small orgs; vendor lock-in risk)

## Nextcloud as a CRM — Verdict

Workable in specific, disciplined scenarios:
- Use Contacts (with custom fields) + Deck (donor pipeline stages) + Files + Forms
- Payments stay in Stripe (never in Nextcloud)
- Automation: Stripe webhook → Make.com/n8n → Nextcloud Contact + activity log
- Best for: ministry orgs, membership-based nonprofits, relational fundraising
- NOT suitable for: heavy grant accounting, complex pledge schedules, large multi-campus audits

| Capability | Nextcloud CRM | Bloomerang/Blackbaud |
|---|---|---|
| Donor records | Strong | Strong |
| Relationship notes | Excellent | OK |
| File context | Native | Clunky |
| Payments | External (by design) | Often bundled |
| Cost | Low/predictable | Escalates |
| Data ownership | Full | Vendor-locked |

## Recommended Approach for FCA

Phase 1: Keep Bloomerang for official records + receipts; introduce Nextcloud as relationship workspace (notes, files, collaboration); eliminate Blackbaud glue
Phase 2: Move first-time/relational donor workflows to Nextcloud
Phase 3 (optional): Fully transition CRM if org outgrows Bloomerang's value

## Exploratory Email Written

Clean, non-committal, competence-signaling. Offers a short discovery call to understand current setup and offer honest take on whether to simplify or reconnect the stack. No commitments.

## Open Items

- Which FCA entity specifically (local Gulf Coast? statewide Florida?) — determines scope
- Exploratory call not yet scheduled
- This could become a Seven Talents or Binary Ranch advisory/pilot case

## Links / References

- Placement unconfirmed.
