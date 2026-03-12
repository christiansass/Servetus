---
servitus:
  schema_version: 1
  system_version: "0.2.1"
  record_type: thread_export
  pipeline_stage: distilled
  status: active
  intent: capture

identity:
  title: "Debian 12 NetINST on Dell PowerEdge R420"
  slug: "debian-12-netinst-dell-poweredge-r420"
  record_id: "SV-20250613-NOW-CST-DEB0"

time:
  created_at: "2025-06-13"
  timezone: "America/Chicago"
  source_range: "thread"

keywords:
  - debian
  - debian-12
  - bookworm
  - dell-poweredge
  - r420
  - netinst
  - server-setup
  - binary-ranch

tags:
  - chatgpt-import
  - binary-ranch
  - linux
  - server
  - infrastructure

origin:
  source_file: "2025-06-13-Debian_12_NetINST_Installation.md"
  source_url: "https://chatgpt.com/c/684cae40-9444-8007-a988-6a1d81e9da6e"
  project: "Binary Ranch"
---

# Debian 12 NetINST on Dell PowerEdge R420

**Source:** 2025-06-13-Debian_12_NetINST_Installation.md
**Date:** 2025-06-13
**Project:** Binary Ranch

## Summary

Step-by-step Debian 12 (Bookworm) Netinst installation instructions for a Dell PowerEdge R420 server.

## Installation Steps

### 1. Download ISO
- File: `debian-12.11.0-amd64-netinst.iso` from debian.org

### 2. Create Bootable USB
- **Linux/macOS:** `sudo dd if=debian-12.x-amd64-netinst.iso of=/dev/sdX bs=4M status=progress && sync`
- **Windows:** Use Rufus

### 3. Prepare Dell PowerEdge R420
- **Enter BIOS:** Press `F2` during POST
- **Boot mode:** Set to UEFI
- **Boot order:** Set USB as first boot device
- **Disable Secure Boot** if needed for driver compatibility

### 4. Boot and Install
- Select "Install" or "Graphical Install"
- Configure network (DHCP or static IP)
- Partition: LVM recommended for server flexibility
- Set hostname, user accounts

### 5. Post-Install
- Update: `apt update && apt upgrade`
- Install SSH: `apt install openssh-server`
- Configure firewall, remote access, monitoring

## Notes

- Hardware: Dell PowerEdge R420 — enterprise rack server
- Context: Binary Ranch infrastructure build-out

## Links / References

- Debian: https://www.debian.org/distrib/
- Related: Binary Ranch server setup
