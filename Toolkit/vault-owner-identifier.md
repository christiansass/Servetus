---
type: toolkit-spec
title: "Vault Owner Identifier (VOI)"
slug: "servetus-vault-owner-identifier"
date: 2026-03-12T00:00:00-06:00
status: draft
version: "0.1"
tags: [toolkit, identity, provenance, sovereignty]
---

## Purpose

Every artifact, memory, and record produced by a Servetus instance must be stamped
with a **Vault Owner Identifier (VOI)** — a unique, stable, sovereign identity
anchor that makes the record defensible as testimony-level evidence.

The VOI is not a username. It is a chain of custody signature.

---

## Why This Exists

Servetus is not just a personal knowledge manager. At its core, it is a **witness** —
a neutral, verifiable, sovereign party to every conversation and event it records.

For a Servetus record to be forensically useful — potentially admissible as evidence —
the provenance must be unambiguous:

- Who created this record
- Which Servetus installation produced it
- When it was created
- What pipeline processed it
- Whether the record has been altered since creation

The VOI is the anchor that makes all of this traceable.

---

## VOI Components

A fully qualified Servetus provenance stamp consists of:

| Field | Description |
|-------|-------------|
| `vault_owner_uid` | Unique identifier for the human owner of this vault |
| `instance_id` | Unique identifier for this Servetus installation |
| `created_at` | ISO 8601 timestamp with timezone |
| `pipeline` | Ordered list of tools that processed the artifact |
| `pipeline_score` | Trust score (starts at 0, -1 per external tool in pipeline) |
| `install_hash` | Hash of the Servetus installation at time of record creation |
| `artifact_hash` | Hash of the source artifact (file, audio, transcript) |

---

## Chain of Custody Signature

The combination of these fields forms a **chain of custody signature**:

```
VOI = vault_owner_uid + instance_id + created_at + artifact_hash
```

If any field is altered after creation, the signature breaks. This is verifiable
independently of the record's content.

---

## Tamper Evidence

- The `artifact_hash` is computed at ingestion time, before any processing
- The `install_hash` ties the record to a specific, verified Servetus installation
- Any post-creation modification to the record must be logged as a versioned amendment,
  not a silent overwrite
- Redactions are documented operations, not mutations of the original

---

## Frontmatter Fields

Records produced by Servetus should include:

```yaml
vault_owner_uid: ""        # assigned at vault initialization, never changes
instance_id: ""            # assigned at installation, stable per machine
install_hash: ""           # hash of Servetus install at time of record creation
artifact_hash: ""          # hash of source file at ingestion
pipeline: []               # ordered list of processing tools
pipeline_score: 0          # trust score
```

---

## Design Principles

1. **The identifier is sovereign.** It is assigned by the vault owner at
   initialization, not by any external service.

2. **The identifier is stable.** It never changes, even if the vault owner's
   name, email, or other identifying information changes.

3. **The identifier is local.** It does not require network verification.
   It is meaningful within the vault and portable with it.

4. **Testimony-level intent.** Every record is created as if it may one day
   need to stand as evidence. This is not paranoia — it is discipline.

---

## Origin Note

Design decision captured 2026-03-12, [location] IL, during processing of the first
artifact destined for the Josh Matrisciana witness record. The insight: Servetus
becomes a party to every conversation it records — not a tool, but a witness.
A trustworthy transcriptionist with its own verifiable identity.

"The identifier isn't just a username — it's a chain of custody signature."
