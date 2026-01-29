# Servetus Vault Starter Kit

This vault is the starting point for the Servetus Phase 0 (CLI + Obsidian + Nextcloud) setup.

## Folder Structure

- `00-system/`       – system files, CLI script, config
- `01-daily-logs/`   – generated daily logs
- `02-events/`       – individual event notes
- `03-arcs/`         – long-running arcs/eras
- `04-projects/`     – projects with deliverables
- `05-witnesses/`    – photos/videos/transcript metadata notes
- `06-storymap/`     – StoryMap lane definitions and higher-level views
- `templates/`       – Obsidian templates used by Servetus

## How to Use (Phase 0)

1. Open this folder as an Obsidian vault.
2. Use the templates in `templates/` with the Templater plugin or manually.
3. Use `servetus_cli.py` to generate daily logs from the command line.

This structure is designed so Servetus can later:
- ingest transcripts and assets
- infer events and arcs
- populate StoryMap
- provide accountability and forecasting
