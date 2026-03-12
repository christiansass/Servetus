---
type: spec
title: "Shared Spec"
slug: "shared-spec"
date: 2026-03-12

circles: []
published: false
tags: [spec, shared]
---

# Shared Spec

## Altitude
**Level 09** — Publication layer. Deliberate release only.

## Purpose

`09-shared/` is the deliberate publication layer of the vault. Nothing lands here
passively. Every file in this folder is something you have explicitly chosen to
release — to a specific person, a defined group, or the public.

This is the outermost boundary of your sovereign vault. What crosses this boundary
is your decision, not the system's.

---

## Core Principle

> *"Inclusion is an act of preservation. Exclusion is an act of discretion.
> Publication is an act of authority."*

The presence of a file in `09-shared/` means the owner has made a deliberate
sovereignty decision: this goes out.

---

## What Goes Here

- Redacted versions of artifacts (original stays in `01-artifacts/`, redacted
  derivative goes in `09-shared/`)
- Published storymap exports
- Shared arc summaries
- Evidence packages for a specific purpose (legal, journalistic, personal)
- Anything released to a specific permission tier in the storymap sharing model

## What Does NOT Go Here

- Raw artifacts (those stay in `01-artifacts/` — ground truth never moves)
- Unreviewed memories or notes
- Anything intended only for internal use

---

## Folder Structure

Organized by destination or purpose:

```
09-shared/
  _shared-spec.md
  public/           ← Available to anyone
  trusted/          ← Specific trusted individuals
  redacted/         ← Redacted derivatives of artifacts
  exports/          ← Packaged exports for specific purposes
```

---

## Frontmatter Requirements

```yaml
---
type: shared
title: "Description of what this is"
slug: "YYYY-MM-DD-description"
date: YYYY-MM-DD

source: "path/to/original"     # Original file this derives from (if applicable)
audience: public                # public | trusted | named-individual | group
purpose: ""                     # Why this was released

redacted: false                 # true if this is a redacted derivative
redactions: []                  # List of redacted fields/sections (if redacted: true)

circles: []
published: true
tags: [shared]
---
```

---

## Redaction Protocol

When producing a shared version of a private record:

1. **Never modify the original** — the source file stays in its folder untouched
2. **Create a derivative** in `09-shared/redacted/` with the redacted content
3. **Document every redaction** — field, reason, authority, date
4. **The redaction record is itself evidence** — it proves intentional, documented exclusion

```yaml
redacted: true
redactions:
  - field: "participants[2]"
    reason: "client-confidentiality"
    authority: "attorney-client privilege"
    redacted_by: "vault-owner"
    date: YYYY-MM-DD
  - field: "transcript_lines[45-62]"
    reason: "privileged-communication"
    authority: "HIPAA"
    redacted_by: "vault-owner"
    date: YYYY-MM-DD
```

---

## Git Tracking

`09-shared/` is gitignored by default — shared files may contain personal data
or sensitive material. If you want to publish something to the public GitHub repo,
that is a separate, explicit decision and belongs in the project's `09-shared/public/`
with a deliberate git add.

---

## Related Specs
- [[S00.02-00-00-storymap-sharing-model(2026-01-30)]] — full sharing model and permission tiers
- [[07-storymap/_storymap-spec]] — the surface that feeds into shared exports
- [[01-artifacts/_artifacts-spec]] — originals that may produce shared derivatives
