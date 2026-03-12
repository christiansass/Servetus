---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: witness
  pipeline_stage: inbox
  status: parked
  intent: capture

identity:
  title: "Pantheon Files Installed on Linux Mint — Miller Columns Working"
  slug: "pantheon-files-miller-columns-linux-mint"
  record_id: "SV-20260228-NOW-CST-PNTF"

time:
  created_at: "2026-02-28"
  timezone: "America/Chicago"
  source_range: "today"

keywords:
  - pantheon-files
  - miller-columns
  - linux-mint
  - elementary-os
  - add-apt-repository

tags:
  - linux
  - troubleshooting
  - hardware

origin:
  machine: "WordInFilm"
  os: "Linux Mint 22.3"
---

# Pantheon Files Installed on Linux Mint — Miller Columns Working

## What Happened

Found a forum post with instructions for installing Pantheon Files (elementary OS's file manager) on Linux Mint. The post was on a locked/closed forum — could not comment or correct it. The commands were wrong: the author had written `add apt-repository` (with a space, treating `add` as the command) when the correct command is `add-apt-repository` (hyphenated — a single utility from `software-properties-common`).

Diagnosed the error independently, ran the corrected commands, and succeeded.

## The Error (forum as published)

```bash
add apt-repository ppa:elementary-os/stable
add apt-repository ppa:elementary-os/os-patches
apt update
apt install pantheon-files
```

## The Fix (correct commands)

```bash
apt add-repository ppa:elementary-os/stable
apt add-repository ppa:elementary-os/os-patches
apt update
apt install pantheon-files
```

`apt` is the package manager. `add-apt-repository` is a separate utility (from `software-properties-common`) that manages PPAs. They are not the same command — `add apt-repository` (spaced) is not a valid command on any standard system.

## Outcome

- Pantheon Files is now installed and running on WordInFilm (Linux Mint 22.3)
- Miller columns view is functional — first time having this on this machine
- Set Pantheon Files as the default file manager

## Links / References

- Placement unconfirmed.
