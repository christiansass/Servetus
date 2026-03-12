---
type: spec
title: "Witnesses Spec"
slug: "witnesses-spec"
date: 2026-03-12

circles: []
published: false
tags: [spec, witnesses]
---

# Witnesses Spec

## Altitude
**Level 08** — People. Sovereign relationship records.

## Purpose

`08-witnesses/` is the people layer of the vault. Each witness record is the private,
sovereign file on a person whose story intersects with yours — everything you know
about them in the context of your life that doesn't belong in a contact card.

A witness record **augments** the CardDAV contact in your address book (Nextcloud
Contacts). It is not the contact. The contact holds portable, shareable information
(name, phone, email). The witness record holds relationship intelligence: how you met,
shared events, corroboration history, trust tier, private notes, things said.

> *"The address book is what you'd give anyone. The witness record is what only you know."*

---

## CardDAV Relationship

| Layer | Lives In | Contains | Shareable? |
|-------|---------|---------|-----------|
| Contact | Nextcloud CardDAV | Name, phone, email, org | Yes |
| Witness record | `08-witnesses/` | Relationship history, trust tier, shared events, private intel | No — sovereign only |

Integration between the two is TBD. Candidate approaches:
- CardDAV `NOTE` field carries a pointer to the witness record
- Certain witness fields (trust tier, last contact) published selectively into CardDAV
- Read-only sync: CardDAV updates pull into witness frontmatter on demand

---

## Trust Tiers

Every witness record carries a trust tier that controls what they can see in
cross-vault sharing and what permission level they sit at in the storymap model:

| Tier | Meaning |
|------|---------|
| `public` | No relationship — corroboration possible but no permissions |
| `acquaintance` | Known person — events + basic metadata |
| `friend` | Trusted individual — selected witnesses/artifacts on request |
| `trusted` | Full witness chain access with explicit permission |
| `sovereign` | Yourself or co-vault holder — full access |

---

## Folder Structure

Flat. One file per person at root of `08-witnesses/`.

```
08-witnesses/
  _witnesses-spec.md
  lastname-firstname.md
  lastname-firstname.md
  ...
```

Last name first — sorts alphabetically by surname, consistent with address book conventions.
No date prefix — witnesses are people, not timestamped events. First contact date belongs
inside the record, not in the filename.

**Naming pattern:** `lastname-firstname-identifier.md`

The identifier is required — it makes the record unique when names collide:

| Preferred identifier | Format | Example |
|---------------------|--------|---------|
| Email domain (custom) | full domain | `smith-john-binaryranch.com.md` |
| Email domain (common provider) | strip TLD | `smith-john-gmail.md`, `smith-john-icloud.md` |
| Context (no email) | how you know them | `smith-john-church.md`, `smith-john-contractor.md` |

The identifier is the domain portion of their email address — non-PII, human-readable,
and unique enough for disambiguation. Full contact details (email, phone) belong in
the frontmatter, not the filename. This file is sovereign — PII is safe here.

---

## Frontmatter Requirements

```yaml
---
type: witness
title: "Full Name"
slug: "lastname-firstname-identifier"
date: YYYY-MM-DD

trust_tier: acquaintance   # public | acquaintance | friend | trusted | sovereign

# Minimum: at least one of email or phone required
email: ""                  # Full email (sovereign file — PII safe here)
phone: ""                  # Full phone number
carddav_uid: ""            # UID from Nextcloud Contacts (optional — links to contact)

linked_events: []
linked_arcs: []

circles: []
published: false
tags: [witness]
---
```

---

## Record Body Convention

```markdown
## How We Met
[context of first contact]

## Relationship Summary
[current relationship status, how often in contact, context]

## Shared Events
- [[03-events/YYYY-MM-DD-event-slug]] — brief note
- [[03-events/YYYY-MM-DD-event-slug]] — brief note

## Corroboration History
- [[01-artifacts/YYYY/...]] — what this person can corroborate

## Private Notes
[anything not for other eyes]
```

---

## Privacy

All files in `08-witnesses/` are Sovereign tier — they never leave the vault.
They are gitignored. They do not sync to public or controlled git repos.
They live on your Nextcloud infrastructure only.

---

## Related Specs
- [[S00.02-00-00-storymap-sharing-model(2026-01-30)]] — trust tiers and sharing model
- [[01-artifacts/_artifacts-spec]] — evidence that witnesses can corroborate
- [[03-events/_events-spec]] — events that link witnesses to moments in time
