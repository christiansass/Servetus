---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Debian 12 NetINST Installation — Dell PowerEdge R420"
  slug: "debian-12-netinst-dell-r420-installation"
  record_id: "SV-20250613-NOW-CST-DEB0"

time:
  created_at: "2025-06-13"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - debian-12
  - netinst
  - dell-poweredge-r420
  - server
  - linux
  - binary-ranch
  - installation

tags:
  - chatgpt-import
  - binary-ranch
  - infrastructure
  - linux
  - server

origin:
  source_file: "2025-06-13-Debian_12_NetINST_Installation.md"
  source_url: "https://chatgpt.com/c/684cae40-9444-8007-a988-6a1d81e9da6e"
  project: "Binary Ranch"
---

# Debian 12 NetINST Installation — Dell PowerEdge R420

**Source:** 2025-06-13-Debian_12_NetINST_Installation.md
**Date:** 2025-06-13
**Project:** Binary Ranch

## Summary

Step-by-step instructions for installing Debian 12 (Bookworm) using the Netinst ISO on a Dell PowerEdge R420 server.

## Installation Steps

### 1. Download ISO
- `debian-12.11.0-amd64-netinst.iso` from debian.org

### 2. Create Bootable USB
- **Linux/macOS:** `sudo dd if=debian-12.11.0-amd64-netinst.iso of=/dev/sdX bs=4M status=progress && sync`
- **Windows:** Use Rufus

### 3. Prepare Dell R420 BIOS
- Press `F2` during POST → BIOS setup
- Set boot mode to **UEFI** in Boot Settings
- Configure RAID if needed (Dell PERC controller)
- Set USB as first boot device

### 4. Boot and Install
- Standard Debian installer; choose guided partitioning or manual
- Set up network during install (NetINST requires internet connection)
- Install SSH server for remote management

### 5. Post-Install
- Update: `apt update && apt upgrade`
- Configure static IP, hostname, SSH keys

## Hardware Notes

- Dell PowerEdge R420: enterprise rack server
- Typical use: Nextcloud host, hypervisor base, or Binary Ranch infrastructure node

## Links / References

- Binary Ranch infrastructure planning
- See also: `2025-06-05--binary-ranch-team-role-alignment-strategy--thread_export.md`
