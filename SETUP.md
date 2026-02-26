# Servetus Setup Guide

How to install and configure Servetus across different operating systems.

---

## Prerequisites

1. **Claude Code CLI** — [Install instructions](https://docs.anthropic.com/claude-code)
2. **Obsidian** — [Download](https://obsidian.md)
3. **Nextcloud** (or other sync) — For multi-machine access
4. **Ollama** — Local AI kernel for the Servetus router (see [Local AI Router](#local-ai-router) below)

### Hardware Requirements for Ollama

| Tier | RAM | GPU VRAM | Recommended Model | Notes |
|------|-----|----------|-------------------|-------|
| Minimum | 8 GB | 6 GB | llama3.2:3b | Slower, less capable |
| Recommended | 16 GB | 8–11 GB | llama3.1:8b | Good balance of speed and quality |
| Full | 64 GB | 24+ GB | llama3.1:70b | Full capability, slower on CPU |

> Ollama runs models on GPU if available, spilling to RAM for larger models. The router defaults to `llama3.1:8b` which runs well on 8B+ VRAM.

---

## Installation

### 1. Clone the Repository

Clone Servetus into your Obsidian vault location:

```bash
# Linux/macOS/WSL
cd ~/path/to/your/obsidian/vaults
git clone git@github.com:christiansass/Servetus.git

# Or with HTTPS
git clone https://github.com/christiansass/Servetus.git
```

### 2. Open in Obsidian

1. Open Obsidian
2. Click "Open folder as vault"
3. Select the `Servetus` folder
4. Trust the vault when prompted

### 3. Create Local Config

The `config/` folder is gitignored for privacy. Create your local copy:

```bash
cd Servetus
mkdir -p config
```

Create these files in `config/`:

**config/projects.md**
```markdown
# Active Projects
- Project1: Description
- Project2: Description
```

**config/tags.md**
```markdown
# Tag Taxonomy
- work: Work-related items
- personal: Personal items
```

**config/overrides.md**
```markdown
# User Overrides
timezone: America/Chicago
```

### 4. Create CLAUDE.md

CLAUDE.md is gitignored (contains local paths). Create it from the template:

```bash
cp templates/CLAUDE.md.example CLAUDE.md
# Or copy from 00-system/system-info.md and customize
```

Or create manually — see [CLAUDE.md Structure](#claudemd-structure) below.

---

## Shell Alias (Recommended)

Always launch Claude Code from the Servetus vault so CLAUDE.md auto-loads.

### Linux / WSL

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Servetus - launch Claude Code in the vault
alias servetus='cd /path/to/your/Servetus && claude'

# Example with Nextcloud sync:
alias servetus='cd /mnt/f/Nextcloud/Obsidian/Servetus && claude'
```

Then reload:
```bash
source ~/.bashrc
```

### macOS

Add to `~/.zshrc` (or `~/.bashrc` if using bash):

```bash
alias servetus='cd ~/Nextcloud/Obsidian/Servetus && claude'
```

Then reload:
```bash
source ~/.zshrc
```

### Windows (PowerShell)

Add to your PowerShell profile (`$PROFILE`):

```powershell
function servetus {
    Set-Location "F:\Nextcloud\Obsidian\Servetus"
    claude
}
```

Or create a batch file `servetus.bat` in your PATH:

```batch
@echo off
cd /d F:\Nextcloud\Obsidian\Servetus
claude
```

### Windows (Git Bash / MINGW)

Add to `~/.bashrc`:

```bash
alias servetus='cd /f/Nextcloud/Obsidian/Servetus && claude'
```

---

## Local AI Router

The Servetus router (`servetus` command) uses Ollama as a local AI kernel. It loads your Toolkit on boot, maintains session context, and auto-escalates complex queries to Claude or other external LLMs with PII scrubbed.

### 1. Install Ollama

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
# or download from https://ollama.com/download
```

**Windows:** Download the installer from [ollama.com/download](https://ollama.com/download)

Verify Ollama is running:
```bash
ollama --version
```

### 2. Pull the Kernel Model

```bash
ollama pull llama3.1:8b
```

This downloads ~4.9 GB. For a lighter install use `llama3.2:3b` (~2 GB), or for more capability use `llama3.1:70b` (~40 GB, requires 40+ GB RAM).

To use a different model, update `config/router_config.json` after installation:
```json
{
  "local_model": "llama3.2:3b"
}
```

### 3. Run the Installer

From inside your Servetus vault:
```bash
bash Toolkit/local/install.sh
```

The installer will:
- Ask if you're using Nextcloud (required for WebDAV/CalDAV features)
- Find your Nextcloud root automatically, or ask you to confirm
- Deploy the router to `~/bin/servetus`
- Add `~/bin` to your PATH (see shell notes below)
- Copy config templates to `config/`

**Shell and PATH notes:**

| OS | Shell | Config file written |
|----|-------|-------------------|
| Linux | bash | `~/.bashrc` |
| Linux | zsh | `~/.zshrc` |
| macOS | zsh (default) | `~/.zprofile` |
| macOS | bash | `~/.bash_profile` |

> **macOS note:** Terminal.app and iTerm2 open login shells by default. Login shells source `.zprofile`, not `.zshrc`. The installer handles this automatically — but if you see `command not found: servetus` after install, run `source ~/.zprofile` or open a new terminal window.

### 4. Configure PII Map

Edit `config/pii_map.json` to add entities you want anonymized before sending to external LLMs:

```json
{
  "entities": {
    "Your Name":      "user1",
    "YourCity":       "city1",
    "yourserver.com": "host1"
  }
}
```

Real values are restored on responses. Order matters — put full phrases before their components (e.g. "John Smith" before "John").

### 5. Launch

Open a new terminal (or `source ~/.bashrc`) and run:

```bash
servetus
```

The router boots with your Toolkit loaded and Ollama as the local kernel. Queries that exceed local capability automatically escalate to Claude (or the configured `escalation_target`) with session context packaged as a handoff.

**Routing prefixes in session:**
```
@claude <query>    → explicit Claude route (PII scrubbed)
@local <query>     → force local Ollama, no escalation
@grok <query>      → Grok (requires grok_api_key in router_config.json)
@gemini <query>    → Gemini (requires gemini_api_key in router_config.json)
/status            → show current config and session state
/exit              → quit
```

---

## Multi-Machine Sync

Servetus is designed to sync via Nextcloud (or Dropbox, Syncthing, etc.):

```
Machine A                    Cloud                    Machine B
    │                          │                          │
    └── Servetus/ ──sync──► Nextcloud ◄──sync── Servetus/
```

**What syncs:**
- Toolkit/ (system specs)
- templates/
- 00-system/ through 07-storymap/
- CHANGELOG.md, README.md, etc.

**What stays local (gitignored):**
- .obsidian/ (Obsidian config)
- config/ (your private settings)
- CLAUDE.md (local paths may differ)

### Per-Machine CLAUDE.md

If your vault path differs across machines, each machine needs its own CLAUDE.md. The content is the same — only paths might change.

Example for different machines:

**Linux workstation:**
```markdown
Vault path: /home/user/Nextcloud/Obsidian/Servetus
```

**macOS laptop:**
```markdown
Vault path: /Users/user/Nextcloud/Obsidian/Servetus
```

**Windows desktop:**
```markdown
Vault path: F:\Nextcloud\Obsidian\Servetus
```

---

## CLAUDE.md Structure

CLAUDE.md tells Claude how to operate. Minimal required content:

```markdown
# Servetus — Human-Readable Operating System

> *"There is no trust without truth, and there is no assistant without trust."*

## What Is This?

Servetus is an operating system. Claude is the kernel. The file system is the program.

## Boot Sequence

1. Read `00-system/VERSION` — Know what you're running
2. Read `Toolkit/` — Load system specs (start with bootloader)
3. Read `config/` — Load user settings
4. Ready for operations

## System Queries

| Query | Action |
|-------|--------|
| "What version?" | Read `00-system/VERSION` |
| "What's new?" | Read `CHANGELOG.md` |
| "System status" | Report version + structure |

## File System

```
Servetus/
├── 00-system/            # System files, VERSION
├── 01-witnesses/         # Ground truth (most zoomed in)
├── 02-daily-logs/        # Daily capture stream
├── 03-events/            # Discrete moments
├── 04-projects/          # Work clusters
├── 05-arcs/              # Narrative threads
├── 06-radar/             # Current viewport
├── 07-storymap/          # 30,000ft view (most zoomed out)
├── Toolkit/              # System specs
├── config/               # User settings
└── templates/            # Note templates
```
```

---

## Verification

After setup, test that everything works:

```bash
servetus
```

You should see the boot banner with context files loaded. Then test:

1. **"What version am I running?"** — Should report the current version from `00-system/VERSION`
2. **"What's new?"** — Should summarize `CHANGELOG.md`
3. **"System status"** — Should report healthy structure
4. **`/status`** — Shows kernel model, escalation target, and PII entity count

For a quick non-interactive test:
```bash
servetus "what is Servetus?"
```

---

## Troubleshooting

### CLAUDE.md not loading

- Make sure you're IN the Servetus directory when launching `claude`
- Check that CLAUDE.md exists in the vault root
- Use the alias to ensure correct directory

### Sync conflicts

- .obsidian/ conflicts are normal (each machine has its own Obsidian config)
- Add `.obsidian/` to .gitignore if using git
- For Nextcloud, consider excluding .obsidian/ from sync

### `command not found: servetus` on macOS

macOS terminals open login shells which source `.zprofile`, not `.zshrc`. If the installer ran correctly but the command isn't found:

```zsh
source ~/.zprofile
```

Or open a new terminal window — login shells re-source `.zprofile` on open.

If that doesn't work, confirm the launcher exists and `~/bin` is in PATH:
```zsh
ls ~/bin/servetus
echo $PATH | tr ':' '\n' | grep bin
```

### Permission errors on Linux/WSL

If the vault is on an NTFS drive (like /mnt/f/):

```bash
# Files may show as executable — this is normal for NTFS on WSL
# Git might see permission changes — fix with:
git config core.fileMode false
```

---

## Updating

Pull updates from GitHub:

```bash
cd /path/to/Servetus
git pull origin main
```

Check the CHANGELOG.md for what's new, then ask Claude "What's new?" to verify.

---

## Uninstalling

1. Delete the Servetus folder
2. Remove the shell alias from your rc file
3. Remove the router if installed:
   ```bash
   rm ~/bin/servetus ~/bin/servetus_router.py
   ```
4. That's it — no system files, no registry entries, no databases
