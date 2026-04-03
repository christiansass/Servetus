#!/usr/bin/env python3
"""
persona-loader.py — Servetus Persona Loader

Loads a named persona from Toolkit/personas/<name>/ and returns
its content as a system-prompt injection string.

A persona is a voice and character overlay on top of the default behavioral
contract (default_persona/00-persona-brief.md). It does not replace core
guardrails — it gives them a face.

Spec: Toolkit/personas/default_persona/00-persona-brief.md
      "To install: read the persona's 00-index.md from Toolkit/personas/<name>/"
      "To uninstall: stop reading it. Return to default_persona as baseline."

Usage (CLI):
    python3 10-System/persona-loader.py                       # list available
    python3 10-System/persona-loader.py cs-lewis_persona      # load named persona
    python3 10-System/persona-loader.py default               # load default only

Usage (import):
    from persona_loader import load_persona, list_personas
    injection = load_persona("cs-lewis_persona")
    # → string to prepend/append to Claude system prompt
"""

import sys
from pathlib import Path

VAULT_ROOT    = Path(__file__).parent.parent
PERSONAS_DIR  = VAULT_ROOT / "Toolkit" / "personas"

# Files to concatenate, in order, when building the persona injection
PERSONA_FILES = [
    "00-index.md",
    "00-persona-brief.md",   # default_persona uses this name
    "01-voice.md",
    "02-values.md",
    "03-phonetics.md",
    "04-apologetics.md",
]

# Always loaded first — the behavioral floor
DEFAULT_PERSONA = "default_persona"


def list_personas() -> list[dict]:
    """Return all available persona directories with their status."""
    personas = []
    if not PERSONAS_DIR.exists():
        return personas
    for d in sorted(PERSONAS_DIR.iterdir()):
        if not d.is_dir():
            continue
        meta = {
            "slug": d.name,
            "path": str(d),
            "files": [f.name for f in d.iterdir() if f.suffix == ".md"],
            "is_default": d.name == DEFAULT_PERSONA,
        }
        # Try to read title from first md file
        for fname in PERSONA_FILES:
            candidate = d / fname
            if candidate.exists():
                first_lines = candidate.read_text()[:200]
                for line in first_lines.splitlines():
                    if line.startswith("title:"):
                        meta["title"] = line.split(":", 1)[1].strip().strip('"')
                        break
                break
        personas.append(meta)
    return personas


def _read_file_strip_frontmatter(path: Path) -> str:
    """Read a markdown file, stripping YAML frontmatter."""
    text = path.read_text(errors="replace")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


def load_persona(name: str, include_default: bool = True) -> str:
    """
    Load a persona by directory name and return the injection string.

    Always prepends the default_persona behavioral floor unless
    include_default=False (not recommended).

    name: persona directory name, e.g. "cs-lewis_persona"
          Pass "default" or "default_persona" to load only the floor.
    """
    sections = []

    # ── Default floor (always first) ─────────────────────────────────────────
    if include_default:
        default_dir = PERSONAS_DIR / DEFAULT_PERSONA
        if default_dir.exists():
            default_parts = []
            for fname in PERSONA_FILES:
                f = default_dir / fname
                if f.exists():
                    default_parts.append(_read_file_strip_frontmatter(f))
            if default_parts:
                sections.append(
                    "=== DEFAULT BEHAVIORAL CONTRACT ===\n\n"
                    + "\n\n---\n\n".join(default_parts)
                )

    # ── Named persona overlay ─────────────────────────────────────────────────
    if name and name not in ("default", DEFAULT_PERSONA):
        persona_dir = PERSONAS_DIR / name
        if not persona_dir.exists():
            # Try partial match
            candidates = [d for d in PERSONAS_DIR.iterdir()
                          if d.is_dir() and name.lower() in d.name.lower()]
            if candidates:
                persona_dir = candidates[0]
                print(f"[persona] Resolved '{name}' → {persona_dir.name}", file=sys.stderr)
            else:
                print(f"[persona] Not found: {name}", file=sys.stderr)
                print(f"[persona] Available: {[d.name for d in PERSONAS_DIR.iterdir() if d.is_dir()]}",
                      file=sys.stderr)
                return "\n\n".join(sections) if sections else ""

        persona_parts = []
        for fname in PERSONA_FILES:
            f = persona_dir / fname
            if f.exists():
                persona_parts.append(_read_file_strip_frontmatter(f))

        if persona_parts:
            sections.append(
                f"=== PERSONA OVERLAY: {persona_dir.name} ===\n\n"
                + "\n\n---\n\n".join(persona_parts)
                + "\n\n[The above persona overlays the default contract. "
                  "Core guardrails and data sovereignty rules remain active underneath. "
                  "Voice and character follow the persona; ethics follow the contract.]"
            )
        else:
            print(f"[persona] No readable files in: {persona_dir}", file=sys.stderr)

    return "\n\n".join(sections)


def active_persona_from_config() -> str:
    """
    Read the active persona from config/router_config.json or return 'default'.
    Allows runtime persona switching without code changes.
    """
    config_file = VAULT_ROOT / "config" / "router_config.json"
    if config_file.exists():
        try:
            import json
            config = json.loads(config_file.read_text())
            return config.get("active_persona", "default")
        except Exception:
            pass
    return "default"


def set_active_persona(name: str) -> None:
    """Persist the active persona choice to router_config.json."""
    import json
    config_file = VAULT_ROOT / "config" / "router_config.json"
    config = {}
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text())
        except Exception:
            pass
    config["active_persona"] = name
    config_file.write_text(json.dumps(config, indent=2))
    print(f"[persona] Active persona set to: {name}", file=sys.stderr)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Servetus persona loader")
    parser.add_argument("persona", nargs="?", default=None,
                        help="Persona name to load (e.g. cs-lewis_persona)")
    parser.add_argument("--list",    action="store_true", help="List available personas")
    parser.add_argument("--set",     metavar="NAME",      help="Set active persona in config")
    parser.add_argument("--current", action="store_true", help="Show currently active persona")
    parser.add_argument("--no-default", action="store_true",
                        help="Skip default floor (not recommended)")
    args = parser.parse_args()

    if args.list:
        personas = list_personas()
        for p in personas:
            marker = " [DEFAULT]" if p["is_default"] else ""
            title  = p.get("title", p["slug"])
            files  = ", ".join(p["files"])
            print(f"{p['slug']}{marker}: {title}")
            print(f"  files: {files}")
        sys.exit(0)

    if args.set:
        set_active_persona(args.set)
        sys.exit(0)

    if args.current:
        print(active_persona_from_config())
        sys.exit(0)

    name = args.persona or active_persona_from_config()
    injection = load_persona(name, include_default=not args.no_default)
    print(injection)
