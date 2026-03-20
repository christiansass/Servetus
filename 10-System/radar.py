#!/usr/bin/env python3
"""
Servetus Radar
Situational awareness: active threads, past-week ingestion, upcoming events.

Usage:
    python3 radar.py [vault_path] [--back N] [--ahead N] [--obsidian]

Defaults: 7 days back, 14 days ahead.
--obsidian  also writes 06-Radar/radar-view.md (regenerates the data section)
"""

import pathlib, re, sys
from datetime import datetime, date, timedelta

# ── Config ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
VAULT      = SCRIPT_DIR.parent

# Parse args (skip vault path if first arg looks like a path)
raw_args = sys.argv[1:]
if raw_args and not raw_args[0].startswith("--"):
    candidate = pathlib.Path(raw_args[0])
    if candidate.exists() and candidate.is_dir():
        VAULT = candidate.resolve()
    raw_args = raw_args[1:]

BACK_DAYS  = 7
AHEAD_DAYS = 14
OBSIDIAN   = False
i = 0
while i < len(raw_args):
    if raw_args[i] == "--back" and i + 1 < len(raw_args):
        BACK_DAYS = int(raw_args[i + 1]); i += 2
    elif raw_args[i] == "--ahead" and i + 1 < len(raw_args):
        AHEAD_DAYS = int(raw_args[i + 1]); i += 2
    elif raw_args[i] == "--obsidian":
        OBSIDIAN = True; i += 1
    else:
        i += 1

today     = date.today()
WIN_START = today - timedelta(days=BACK_DAYS)
WIN_END   = today + timedelta(days=AHEAD_DAYS)

W = 72          # box width
C = W - 6       # inner content width (border + 2-space pad each side)

# ── ANSI ──────────────────────────────────────────────────────────────────────
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
RESET  = "\033[0m"

# ── Box drawing ───────────────────────────────────────────────────────────────
def _plain(s):
    return re.sub(r"\033\[[0-9;]*m", "", s)

def top(): return "╔" + "═" * (W - 2) + "╗"
def div(): return "╠" + "═" * (W - 2) + "╣"
def bot(): return "╚" + "═" * (W - 2) + "╝"

def row(content):
    plain = _plain(content)
    if len(plain) > C:
        content = plain[: C - 1] + "…"
        plain   = content
    pad = C - len(_plain(content))
    return f"║  {content}{' ' * max(0, pad)}  ║"

def lrow(label, value, lw=10):
    return row(f"{label:<{lw}}{value}")

# ── Frontmatter parser ────────────────────────────────────────────────────────
def read_fm(path):
    try:
        text = path.read_text(errors="replace")
        if not text.startswith("---"):
            return {}
        end = text.find("\n---", 3)
        fm  = text[3:end] if end != -1 else text[3:]
        result = {}
        for key, pat in [
            ("status",     r"^\s*status:\s*(.+)$"),
            ("name",       r"^name:\s*(.+)$"),
            ("type",       r"^type:\s*(.+)$"),
            ("slug",       r"^slug:\s*(.+)$"),
            ("radar",      r"^radar:\s*(.+)$"),
        ]:
            m = re.search(pat, fm, re.M)
            if m:
                result[key] = m.group(1).strip().strip("\"'")

        # title: flat OR nested (identity.title)
        m = re.search(r"^title:\s*(.+)$", fm, re.M)
        if not m:
            m = re.search(r"^\s+title:\s*(.+)$", fm, re.M)
        if m:
            result["title"] = m.group(1).strip().strip("\"'")

        # slug: flat OR nested (identity.slug)
        if "slug" not in result:
            m = re.search(r"^\s+slug:\s*(.+)$", fm, re.M)
            if m:
                result["slug"] = m.group(1).strip().strip("\"'")

        # date / created_at → date object
        for key in ("date", "created_at"):
            m = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
            if m:
                raw = m.group(1).strip().strip("\"'")
                try:
                    result[key] = datetime.fromisoformat(
                        raw.replace("Z", "+00:00")
                    ).date()
                except Exception:
                    try:
                        result[key] = date.fromisoformat(raw[:10])
                    except Exception:
                        pass

        # linked_arcs — handle wikilinks, inline lists, and dash lists
        arc_block = re.search(r"^linked_arcs:\s*(.*?)(?=\n\S|\Z)", fm, re.S | re.M)
        if arc_block:
            raw_arcs = arc_block.group(0)
            slugs = []
            # 1. Wikilinks: [[05-Arcs/the-inklings_arc]] → "the-inklings_arc"
            for wl in re.findall(r"\[\[([^\]]+)\]\]", raw_arcs):
                last = wl.split("/")[-1].strip()
                if last:
                    slugs.append(last)
            # 2. Inline YAML list: [tmobile-breach, other-arc]
            inline = re.search(r"linked_arcs:\s*\[([^\]]+)\]", raw_arcs)
            if inline:
                for tok in inline.group(1).split(","):
                    tok = tok.strip().strip("\"'")
                    if tok:
                        slugs.append(tok.split("/")[-1])
            # 3. Dash list items (fallback)
            if not slugs:
                for item in re.findall(r"^\s*-\s*[\"']?([^\"\'\[\]\n]+)[\"']?", raw_arcs, re.M):
                    item = item.strip()
                    if item and item != "linked_arcs":
                        slugs.append(item.split("/")[-1])
            result["linked_arcs"] = [s for s in slugs if len(s) > 2]

        result["tags"] = re.findall(r"^\s+-\s+(\S+)", fm, re.M)
        return result
    except Exception:
        return {}

# ── Date from filename ────────────────────────────────────────────────────────
_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")

def date_from_name(path):
    m = _DATE_RE.match(path.name)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except Exception:
            pass
    return None

# ── Arc index ─────────────────────────────────────────────────────────────────
def load_arcs():
    """
    Returns:
        arc_names  — dict  slug → display title
        active_arcs — list of dicts {slug, title, mtime, status}
    """
    d = VAULT / "05-Arcs"
    arc_names   = {}
    active_arcs = []
    if not d.exists():
        return arc_names, active_arcs
    for f in sorted(d.glob("*.md")):
        if f.name.startswith("_"):
            continue
        fm    = read_fm(f)
        stem  = f.stem                              # e.g. "tmobile-breach_arc"
        short = re.sub(r"_arc$", "", stem)          # "tmobile-breach"
        title = fm.get("title") or stem
        slug  = fm.get("slug") or short

        for k in (stem, short, slug):
            arc_names[k] = title

        arc_names[stem]  = title
        arc_names[short] = title
        arc_names[slug]  = title

        if fm.get("status", "").lower() == "active":
            active_arcs.append(
                dict(
                    slug=slug,
                    title=title,
                    mtime=date.fromtimestamp(f.stat().st_mtime),
                    status="active",
                )
            )

    active_arcs.sort(key=lambda x: x["mtime"], reverse=True)
    return arc_names, active_arcs

# ── Collect items ─────────────────────────────────────────────────────────────
def collect_memories():
    d     = VAULT / "02-memories"
    items = []
    if not d.exists():
        return items
    for f in d.glob("*.md"):
        if f.name.startswith("_"):
            continue
        fm = read_fm(f)
        dt = date_from_name(f) or fm.get("created_at")
        if dt is None or not (WIN_START <= dt <= WIN_END):
            continue
        arcs = fm.get("linked_arcs") or []
        # Normalise: strip _arc suffix so slugs match arc_names index
        arcs = [re.sub(r"_arc$", "", a) for a in arcs]
        if not arcs:
            arcs = [
                t for t in fm.get("tags", [])
                if t not in ("memory", "record", "event", "arc")
            ]
        items.append(
            dict(
                date=dt,
                kind="memory",
                title=fm.get("name") or fm.get("title") or f.stem,
                arcs=arcs or ["untagged"],
                file=f.name,
            )
        )
    return items

def collect_events():
    d     = VAULT / "03-events"
    items = []
    if not d.exists():
        return items
    for f in d.glob("*.md"):
        if f.name.startswith("_"):
            continue
        fm = read_fm(f)
        dt = fm.get("date") or date_from_name(f)
        if dt is None or not (WIN_START <= dt <= WIN_END):
            continue
        arcs = fm.get("linked_arcs") or []
        arcs = [re.sub(r"_arc$", "", a) for a in arcs]
        if not arcs:
            arcs = [t for t in fm.get("tags", []) if t not in ("event",)]
        items.append(
            dict(
                date=dt,
                kind="event",
                title=fm.get("title") or f.stem,
                arcs=arcs or ["untagged"],
                file=f.name,
            )
        )
    return items

# ── Grouping helpers ──────────────────────────────────────────────────────────
def group_by_date(items):
    result = {}
    for item in items:
        result.setdefault(item["date"], []).append(item)
    return result

def arc_display(slug, arc_names, max_len=22):
    name = arc_names.get(slug, slug)
    if len(name) > max_len:
        name = name[: max_len - 1] + "…"
    return name

def day_summary_cli(items, arc_names):
    """One-line summary of items on a given day, grouped by arc."""
    by_arc = {}
    for item in items:
        for arc in item["arcs"]:
            by_arc.setdefault(arc, []).append(item)

    parts = []
    for arc, its in sorted(by_arc.items()):
        label   = arc_display(arc, arc_names)
        n_ev    = sum(1 for i in its if i["kind"] == "event")
        n_mem   = sum(1 for i in its if i["kind"] == "memory")
        details = []
        if n_ev:  details.append(f"{n_ev} event{'s' if n_ev>1 else ''}")
        if n_mem: details.append(f"{n_mem} memory" if n_mem == 1 else f"{n_mem} memories")
        parts.append(f"{CYAN}{label}{RESET} {' '.join(details)}")
    return "  ·  ".join(parts)

def day_label(d):
    if d == today:
        return f"{BOLD}today{RESET}     "
    if d == today - timedelta(days=1):
        return f"{DIM}yesterday{RESET} "
    return f"{DIM}{d.strftime('%a %b %d')}{RESET}"

# ── CLI render ────────────────────────────────────────────────────────────────
def render_cli(memories, events, active_arcs, arc_names):
    all_items    = memories + events
    past_items   = [i for i in all_items if WIN_START <= i["date"] < today]
    today_items  = [i for i in all_items if i["date"] == today]
    future_items = [i for i in all_items if i["date"] > today]

    now    = datetime.now()
    ts_str = now.strftime("%Y-%m-%d  %H:%M")

    out = []
    out.append(top())

    # Header
    title = f"{BOLD}RADAR{RESET}  ●  Situational Awareness"
    out.append(row(title))
    win   = (
        f"window: {WIN_START.strftime('%b %d')} – {WIN_END.strftime('%b %d')}"
        f"  ·  {BACK_DAYS}d back · {AHEAD_DAYS}d ahead  ·  {ts_str}"
    )
    out.append(row(f"{DIM}{win}{RESET}"))

    # ── THREADS ──────────────────────────────────────────────────────────────
    out.append(div())
    if active_arcs:
        budget = C - 10
        parts  = []
        for a in active_arcs:
            candidate = "  ·  ".join(parts + [a["title"]])
            if len(candidate) > budget - 6:
                parts.append(f"+{len(active_arcs) - len(parts)}")
                break
            parts.append(a["title"])
        arc_str = "  ·  ".join(parts)
        out.append(lrow("THREADS", f"{len(active_arcs)} active  ·  {GREEN}{arc_str}{RESET}"))
        # Stale threads (not touched in > 3 days)
        stale = [a for a in active_arcs if (today - a["mtime"]).days > 3]
        if stale:
            stale_names = "  ·  ".join(a["title"][:20] for a in stale[:3])
            out.append(lrow("", f"{YELLOW}stale (>{3}d): {stale_names}{RESET}"))
    else:
        out.append(lrow("THREADS", f"{DIM}no active arcs{RESET}"))

    # ── PAST WEEK ─────────────────────────────────────────────────────────────
    out.append(div())
    out.append(lrow(
        "PAST",
        f"{BACK_DAYS}d  ·  {len(past_items)} item{'s' if len(past_items)!=1 else ''} ingested"
    ))
    if past_items:
        past_dates = sorted(set(i["date"] for i in past_items), reverse=True)
        for d in past_dates:
            day_items = [i for i in past_items if i["date"] == d]
            summary   = day_summary_cli(day_items, arc_names)
            out.append(row(f"  {day_label(d)}  {summary}"))
    else:
        out.append(row(f"  {DIM}nothing ingested in past {BACK_DAYS} days{RESET}"))

    # ── TODAY ─────────────────────────────────────────────────────────────────
    out.append(div())
    ts_now = now.strftime("%H:%M")
    if today_items:
        summary = day_summary_cli(today_items, arc_names)
        out.append(lrow(
            "TODAY",
            f"{today.strftime('%a %b %d')}  ·  {len(today_items)} item{'s' if len(today_items)!=1 else ''}  ·  {ts_now}"
        ))
        if summary:
            out.append(row(f"  {summary}"))
    else:
        out.append(lrow(
            "TODAY",
            f"{today.strftime('%a %b %d')}  ·  {DIM}nothing ingested yet  ·  {ts_now}{RESET}"
        ))

    # ── AHEAD ─────────────────────────────────────────────────────────────────
    out.append(div())
    out.append(lrow(
        "AHEAD",
        f"{AHEAD_DAYS}d  ·  {len(future_items)} event{'s' if len(future_items)!=1 else ''} scheduled"
    ))
    if future_items:
        future_dates = sorted(set(i["date"] for i in future_items))
        for d in future_dates:
            day_items = [i for i in future_items if i["date"] == d]
            titles    = "  ·  ".join(
                f"{YELLOW}{i['title'][:28]}{RESET}" for i in day_items[:3]
            )
            suffix = f"  +{len(day_items)-3}" if len(day_items) > 3 else ""
            out.append(row(f"  {DIM}{d.strftime('%a %b %d')}{RESET}  {titles}{suffix}"))
    else:
        out.append(row(f"  {DIM}no upcoming events in the next {AHEAD_DAYS} days{RESET}"))

    out.append(bot())
    print("\n".join(out))

# ── Obsidian render ───────────────────────────────────────────────────────────
def render_obsidian(memories, events, active_arcs, arc_names):
    """Write 06-Radar/radar-view.md — regenerates the auto section only."""
    all_items    = memories + events
    past_items   = [i for i in all_items if WIN_START <= i["date"] < today]
    today_items  = [i for i in all_items if i["date"] == today]
    future_items = [i for i in all_items if i["date"] > today]

    now    = datetime.now()
    ts_str = now.strftime("%Y-%m-%dT%H:%M:%S")

    lines = []
    lines.append("---")
    lines.append("type: view")
    lines.append('title: "Radar — Situational Awareness"')
    lines.append(f'generated: "{ts_str}"')
    lines.append(f'window_start: "{WIN_START.isoformat()}"')
    lines.append(f'window_end: "{WIN_END.isoformat()}"')
    lines.append("---")
    lines.append("")
    lines.append("# Radar — Situational Awareness")
    lines.append(f"*Auto-generated by `radar.py` on {now.strftime('%Y-%m-%d %H:%M')} — "
                 f"window: {WIN_START.strftime('%b %d')} – {WIN_END.strftime('%b %d')}*")
    lines.append("")

    # ── Active Threads ────────────────────────────────────────────────────────
    lines.append("## Active Threads")
    lines.append("")
    if active_arcs:
        lines.append("| Arc | Last touched | Status |")
        lines.append("|-----|-------------|--------|")
        for a in active_arcs:
            age  = (today - a["mtime"]).days
            flag = " ⚠️" if age > 3 else ""
            lines.append(f"| {a['title']} | {a['mtime'].strftime('%b %d')} ({age}d ago){flag} | active |")
    else:
        lines.append("*No active arcs.*")
    lines.append("")

    # ── Past Week ─────────────────────────────────────────────────────────────
    lines.append(f"## Past {BACK_DAYS} Days  ({WIN_START.strftime('%b %d')} – {(today - timedelta(days=1)).strftime('%b %d')})")
    lines.append("")
    if past_items:
        by_date = group_by_date(past_items)
        for d in sorted(by_date.keys(), reverse=True):
            day_items = by_date[d]
            day_str   = d.strftime("%A, %B %d")
            lines.append(f"### {day_str}")
            lines.append("")
            # Group by arc
            by_arc = {}
            for item in day_items:
                for arc in item["arcs"]:
                    by_arc.setdefault(arc, []).append(item)
            for arc, its in sorted(by_arc.items()):
                label = arc_names.get(arc, arc)
                lines.append(f"**{label}**")
                for item in its:
                    icon = "📌" if item["kind"] == "event" else "💭"
                    lines.append(f"- {icon} {item['title']}")
                lines.append("")
    else:
        lines.append(f"*Nothing ingested in the past {BACK_DAYS} days.*")
        lines.append("")

    # ── Today ─────────────────────────────────────────────────────────────────
    lines.append(f"## Today — {today.strftime('%A, %B %d')}")
    lines.append("")
    if today_items:
        by_arc = {}
        for item in today_items:
            for arc in item["arcs"]:
                by_arc.setdefault(arc, []).append(item)
        for arc, its in sorted(by_arc.items()):
            label = arc_names.get(arc, arc)
            lines.append(f"**{label}**")
            for item in its:
                icon = "📌" if item["kind"] == "event" else "💭"
                lines.append(f"- {icon} {item['title']}")
            lines.append("")
    else:
        lines.append("*Nothing ingested yet today.*")
        lines.append("")

    # ── Ahead ─────────────────────────────────────────────────────────────────
    lines.append(f"## Ahead — next {AHEAD_DAYS} days  ({(today + timedelta(days=1)).strftime('%b %d')} – {WIN_END.strftime('%b %d')})")
    lines.append("")
    if future_items:
        by_date = group_by_date(future_items)
        for d in sorted(by_date.keys()):
            day_items = by_date[d]
            day_str   = d.strftime("%A, %B %d")
            lines.append(f"### {day_str}")
            lines.append("")
            for item in day_items:
                icon = "📌" if item["kind"] == "event" else "💭"
                lines.append(f"- {icon} {item['title']}")
            lines.append("")
    else:
        lines.append(f"*No upcoming events in the next {AHEAD_DAYS} days.*")
        lines.append("")

    lines.append("---")
    lines.append("*To add items to the ahead section, create an event file in `03-events/` "
                 "with a future `date:` in the frontmatter.*")
    lines.append("")

    out_path = VAULT / "06-Radar" / "radar-view.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    print(f"  → wrote {out_path.relative_to(VAULT)}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    arc_names, active_arcs = load_arcs()
    memories = collect_memories()
    events   = collect_events()

    render_cli(memories, events, active_arcs, arc_names)

    if OBSIDIAN:
        render_obsidian(memories, events, active_arcs, arc_names)

if __name__ == "__main__":
    main()
