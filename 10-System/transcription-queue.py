#!/usr/bin/env python3
"""
transcription-queue.py — Servetus server daemon for WordInFilm (GTX 1080 Ti).

Watches the Nextcloud Talk/Audio/ folder for new .mp3 files, runs Whisper
on the GPU, writes artifacts into the vault, and posts completion notices
to Nextcloud Talk.

Design:
  - Pure polling (30-second interval) — no watchdog dependency.
  - State file (.transcription-queue-state.json) prevents reprocessing.
  - Writes artifacts directly into 00-Artifacts/ date hierarchy.
  - Posts to Christian's 1:1 (cufo8jwd) on every completion.
  - Posts to Jim Coler Social (eco9ue5r) if filename contains "jim" or "jcoler".
  - Posts AI standup summary to Binary Ranch Standup (tnft3avs) for Mon/Wed/Fri
    recordings that start between 7–10 AM.

Config (config/nextcloud.env):
  NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_APP_PASSWORD
  TALK_AUDIO_DIR (optional — defaults to ~/Nextcloud/Talk/Audio)

systemd:
  See 10-System/systemd/servetus-transcription-queue.service

Usage:
  python3 10-System/transcription-queue.py          # run foreground
  python3 10-System/transcription-queue.py --once   # process queue, exit
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

VAULT_ROOT   = Path(__file__).parent.parent
ENV_FILE     = VAULT_ROOT / "config" / "nextcloud.env"
ROOMS_FILE   = VAULT_ROOT / "config" / "talk-rooms.json"
STATE_FILE   = Path(__file__).parent / ".transcription-queue-state.json"
ARTIFACTS    = VAULT_ROOT / "00-Artifacts"

MONTH_NAMES = {
    1: "01-Jan",  2: "02-Feb",  3: "03-Mar",  4: "04-Apr",
    5: "05-May",  6: "06-Jun",  7: "07-Jul",  8: "08-Aug",
    9: "09-Sep", 10: "10-Oct", 11: "11-Nov", 12: "12-Dec",
}

POLL_INTERVAL = 30          # seconds between directory scans
SERVETUS_ROOM = "cufo8jwd"  # Christian B Sass (1:1) — internal Servetus notifications only
JIM_ROOM      = "eco9ue5r"  # Jim Coler Social — Jim-specific recordings only
BR_STANDUP    = "tnft3avs"  # Binary Ranch Standup — receives AI summaries on MWF standups
JIM_KEYWORDS  = {"jim", "jcoler", "coler"}

# Standup detection: Mon/Wed/Fri recordings that start between 7–10 AM are assumed
# to be the Binary Ranch standup. Summaries are posted to BR_STANDUP automatically.
STANDUP_DAYS  = {0, 2, 4}  # Monday=0, Wednesday=2, Friday=4
STANDUP_HOUR_START = 7
STANDUP_HOUR_END   = 10


# ── Env / Config ──────────────────────────────────────────────────────────────

def load_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def watch_dir(env: dict) -> Path:
    """Resolve the Talk/Audio directory. Configurable via TALK_AUDIO_DIR."""
    if "TALK_AUDIO_DIR" in env:
        return Path(env["TALK_AUDIO_DIR"])
    # Default: ~/Nextcloud/Talk/Audio (works on both Mac and Linux)
    home = Path.home()
    candidates = [
        home / "Nextcloud" / "Talk" / "Audio",
        Path("/mnt/Cloud/Nextcloud/Talk/Audio"),
    ]
    for c in candidates:
        if c.exists():
            return c
    # Return the most likely and let the loop warn if absent
    return candidates[0]


# ── State ─────────────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"processed": {}}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── Talk API ──────────────────────────────────────────────────────────────────

def make_headers(user: str, password: str) -> dict:
    b64 = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {b64}", "OCS-APIREQUEST": "true",
            "Content-Type": "application/json"}


def send_talk_message(env: dict, room_token: str, message: str):
    """Post a message to a Nextcloud Talk room."""
    url  = f"{env['NEXTCLOUD_URL']}/ocs/v2.php/apps/spreed/api/v1/chat/{room_token}"
    body = json.dumps({"message": message}).encode()
    req  = urllib.request.Request(
        url, data=body, method="POST",
        headers=make_headers(env["NEXTCLOUD_USER"], env["NEXTCLOUD_APP_PASSWORD"]),
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"  [talk] Sent to {room_token}: HTTP {r.status}")
    except urllib.error.HTTPError as e:
        print(f"  [talk] ERROR {e.code} sending to {room_token}: {e.read()[:200]}")
    except Exception as e:
        print(f"  [talk] ERROR sending to {room_token}: {e}")


def claude_summarize(api_key: str, transcript: str) -> str:
    """Call Claude API to summarize a standup transcript."""
    url  = "https://api.anthropic.com/v1/messages"
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 512,
        "messages": [{
            "role": "user",
            "content": (
                "You are summarizing a Binary Ranch standup meeting transcript. "
                "Write a concise standup summary in plain text (no markdown headers, "
                "no bullet symbols — just short paragraphs or a clean list). "
                "Cover: what was discussed, any decisions made, blockers, and next steps. "
                "Keep it under 300 words.\n\n"
                f"TRANSCRIPT:\n{transcript[:12000]}"
            ),
        }],
    }).encode()
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read())
        return resp["content"][0]["text"].strip()
    except Exception as e:
        raise RuntimeError(f"Claude API error: {e}")


def maybe_post_standup_summary(env: dict, mp3_path: Path, transcript: str):
    """
    If this recording looks like a MWF standup (day-of-week + 7–10 AM window),
    generate a Claude summary and post it to Binary Ranch Standup.
    """
    dt = recording_date(mp3_path)
    if dt is None:
        return
    if dt.weekday() not in STANDUP_DAYS:
        return
    if not (STANDUP_HOUR_START <= dt.hour < STANDUP_HOUR_END):
        return

    api_key = env.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  [standup] ANTHROPIC_API_KEY not set — skipping summary")
        return

    day_name = dt.strftime("%A %Y-%m-%d")
    print(f"  [standup] MWF standup detected ({day_name}) — summarizing…")
    try:
        summary = claude_summarize(api_key, transcript)
    except RuntimeError as e:
        print(f"  [standup] Summarization failed: {e}")
        return

    msg = f"Standup summary ({day_name})\n\n{summary}"
    send_talk_message(env, BR_STANDUP, msg)
    print(f"  [standup] Summary posted to Binary Ranch Standup ({BR_STANDUP})")


def notify(env: dict, mp3_name: str, artifact_path: str, duration_s: float,
           text_preview: str):
    """Post completion notices to appropriate Talk rooms."""
    short = text_preview[:200].replace("\n", " ").strip()
    if len(text_preview) > 200:
        short += "…"

    msg = (
        f"🎙️ Whisper transcription complete\n"
        f"**File:** {mp3_name}\n"
        f"**Time:** {duration_s:.0f}s\n"
        f"**Artifact:** {artifact_path}\n"
        f"**Preview:** {short}"
    )
    # Post to Christian's 1:1 only — not to any team room
    send_talk_message(env, SERVETUS_ROOM, msg)

    # Also notify Jim room if this recording involves him
    name_lower = mp3_name.lower()
    if any(kw in name_lower for kw in JIM_KEYWORDS):
        send_talk_message(env, JIM_ROOM,
                          f"🎙️ Transcription ready for a recording that may involve you.\n"
                          f"**File:** {mp3_name}\n**Preview:** {short}")


# ── Whisper ───────────────────────────────────────────────────────────────────

def find_whisper() -> str:
    """Find the whisper executable."""
    candidates = [
        str(Path.home() / ".local" / "bin" / "whisper"),
        "/usr/local/bin/whisper",
        "whisper",
    ]
    for c in candidates:
        try:
            subprocess.run([c, "--help"], capture_output=True, timeout=5)
            return c
        except Exception:
            continue
    return "whisper"   # last resort — let it fail with a clear error


def run_whisper(mp3_path: Path, out_dir: Path) -> str:
    """
    Run Whisper on mp3_path, write .txt output to out_dir.
    Returns transcribed text or raises RuntimeError.
    """
    whisper_bin = find_whisper()
    cmd = [
        whisper_bin,
        str(mp3_path),
        "--model", "small",
        "--language", "en",
        "--output_format", "txt",
        "--output_dir", str(out_dir),
    ]
    print(f"  [whisper] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if result.returncode != 0:
        raise RuntimeError(
            f"Whisper exit {result.returncode}:\n{result.stderr[-500:]}"
        )

    # Whisper writes <stem>.txt into out_dir
    stem   = mp3_path.stem
    txt_path = out_dir / f"{stem}.txt"
    if not txt_path.exists():
        # Sometimes Whisper appends the model suffix — find any .txt
        txts = list(out_dir.glob("*.txt"))
        if not txts:
            raise RuntimeError(f"Whisper produced no .txt file in {out_dir}")
        txt_path = txts[0]

    return txt_path.read_text(encoding="utf-8", errors="replace")


# ── Vault write ───────────────────────────────────────────────────────────────

def slugify(text: str, max_len: int = 50) -> str:
    import re
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len]


def recording_date(mp3_path: Path) -> datetime | None:
    """Extract recording date from filename like 'Recording 2025-09-05 12-15-25.mp3'."""
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})\s+(\d{2})-(\d{2})-(\d{2})", mp3_path.name)
    if m:
        return datetime(int(m[1]), int(m[2]), int(m[3]),
                        int(m[4]), int(m[5]), int(m[6]))
    return None


def write_transcript_artifact(mp3_path: Path, transcript: str,
                               processed_at: datetime) -> Path:
    """
    Write transcript to 00-Artifacts/YYYY/MM-Mon/DD/whisper/<slug>.md
    Files by recording date (from filename), not transcription date.
    Returns the path of the companion .md file.
    """
    dt     = recording_date(mp3_path) or processed_at
    month  = MONTH_NAMES[dt.month]
    day_dir = dt.strftime("%Y-%m-%d")
    art_dir = ARTIFACTS / str(dt.year) / month / day_dir
    art_dir.mkdir(parents=True, exist_ok=True)

    rec_date = dt.strftime("%Y-%m-%d")
    ts     = dt.strftime("%Y-%m-%dT%H:%M:00-05:00")
    slug   = slugify(mp3_path.stem)
    rid    = f"SV-{rec_date.replace('-','')}-{dt.strftime('%H%M')}-CST-WHSP"
    md_path = art_dir / f"{slug}.md"

    # Copy the mp3 reference (we don't move the file — it lives in Nextcloud)
    frontmatter = f"""---
servitus:
  schema_version: 2
  system_version: 0.2.1
  record_type: artifact
  pipeline_stage: raw
  status: active
  intent: capture

identity:
  title: "{mp3_path.name}"
  slug: "{slug}"
  record_id: "{rid}"

time:
  created_at: "{ts}"
  timezone: "America/Chicago"
  source_range: "today"

provenance:
  source_file: "{mp3_path.name}"
  mimetype: "audio/mpeg"
  transcribed_by: "Whisper (small model, WordInFilm GTX 1080 Ti GPU)"
  source_path: "{mp3_path}"
  transcribed_on: "{processed_at.strftime('%Y-%m-%d')}"

tags:
  - servitus
  - artifact
  - whisper
  - transcript
---

# {mp3_path.name}

*Recorded {rec_date} — transcribed {processed_at.strftime('%Y-%m-%d')} by Whisper (small) on WordInFilm GTX 1080 Ti*

---

"""

    md_path.write_text(frontmatter + transcript)
    print(f"  [vault] Artifact: {md_path.relative_to(VAULT_ROOT)}")
    return md_path


# ── Queue processor ───────────────────────────────────────────────────────────

def process_file(mp3_path: Path, env: dict) -> dict:
    """Transcribe one mp3. Returns result dict for state."""
    print(f"\n[queue] Processing: {mp3_path.name}")
    t0 = time.time()

    with tempfile.TemporaryDirectory(prefix="servetus-whisper-") as tmpdir:
        try:
            transcript = run_whisper(mp3_path, Path(tmpdir))
        except RuntimeError as e:
            print(f"  [whisper] FAILED: {e}")
            return {"status": "error", "error": str(e),
                    "processed_at": datetime.now().isoformat()}

    elapsed    = time.time() - t0
    now        = datetime.now()
    md_path    = write_transcript_artifact(mp3_path, transcript, now)
    art_rel    = str(md_path.relative_to(VAULT_ROOT))

    # Only notify for recent recordings (within 7 days). Backlog processing
    # is silent — a bulk run of 100+ old files should not flood the 1:1.
    rec_date = recording_date(mp3_path)
    is_recent = (rec_date is None or
                 (datetime.now() - rec_date).days <= 7)
    if is_recent:
        notify(env, mp3_path.name, art_rel, elapsed, transcript)
        maybe_post_standup_summary(env, mp3_path, transcript)
    else:
        print(f"  [notify] Skipped — backlog file ({rec_date.date() if rec_date else 'unknown date'})")

    result = {
        "status": "ok",
        "processed_at": now.isoformat(),
        "elapsed_s": round(elapsed, 1),
        "artifact": art_rel,
        "size_bytes": mp3_path.stat().st_size,
    }
    print(f"  [queue] Done in {elapsed:.0f}s → {art_rel}")
    return result


def scan_and_process(watch: Path, state: dict, env: dict,
                     recent_first: bool = True) -> bool:
    """
    Scan watch_dir for .mp3 files not yet processed.
    recent_first=True (default) processes newest files first so today's
    recordings don't wait behind years of backlog.
    Returns True if any files were processed.
    """
    if not watch.exists():
        print(f"[queue] Watch dir absent: {watch} — waiting…")
        return False

    processed = state.setdefault("processed", {})
    new_work   = False

    all_mp3s = list(watch.glob("**/*.mp3"))
    if recent_first:
        # Sort by file mtime descending (newest first)
        all_mp3s.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    else:
        all_mp3s.sort()

    for mp3 in all_mp3s:
        key    = str(mp3)
        status = processed.get(key, {}).get("status")

        # Skip completed or in-progress files (in-progress = guard against restart races)
        if status in ("ok", "in-progress"):
            continue
        # Debounce: skip files modified in last 10s (still being written)
        if time.time() - mp3.stat().st_mtime < 10:
            print(f"[queue] Skipping (too fresh): {mp3.name}")
            continue

        # Mark in-progress BEFORE launching — prevents duplicate on restart
        processed[key] = {"status": "in-progress", "started_at": datetime.now().isoformat()}
        save_state(state)

        result = process_file(mp3, env)
        processed[key] = result
        save_state(state)
        new_work = True

    return new_work


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Servetus transcription queue daemon")
    parser.add_argument("--once", action="store_true",
                        help="Process queue once and exit (no daemon loop)")
    parser.add_argument("--dir", metavar="PATH",
                        help="Override watch directory")
    parser.add_argument("--oldest-first", action="store_true",
                        help="Process oldest recordings first (default: newest first)")
    args = parser.parse_args()

    print(f"[queue] Starting — vault: {VAULT_ROOT}")
    env   = load_env()
    state = load_state()

    # On startup: reset any in-progress entries that have no active Whisper process.
    # These are orphaned from a previous run — reset to error so they get retried.
    import subprocess as _sp
    try:
        result = _sp.run(["pgrep", "-f", "whisper"], capture_output=True, text=True)
        active_pids = set(result.stdout.split())
        if not active_pids:
            # No Whisper running — all in-progress entries are orphaned
            processed = state.setdefault("processed", {})
            reset_count = 0
            for k, v in processed.items():
                if v.get("status") == "in-progress":
                    v["status"] = "error"
                    v["error"] = "orphaned in-progress on startup — retrying"
                    reset_count += 1
            if reset_count:
                save_state(state)
                print(f"[queue] Reset {reset_count} orphaned in-progress entries to error")
    except Exception:
        pass  # pgrep not available — skip orphan reset

    watch = Path(args.dir) if args.dir else watch_dir(env)
    print(f"[queue] Watching: {watch}")
    print(f"[queue] State: {STATE_FILE}")

    recent_first = not getattr(args, "oldest_first", False)

    if args.once:
        scan_and_process(watch, state, env, recent_first=recent_first)
        return

    print(f"[queue] Poll interval: {POLL_INTERVAL}s — recent-first={recent_first} — Ctrl-C to stop")
    try:
        while True:
            env = load_env()   # reload credentials on each cycle
            scan_and_process(watch, state, env, recent_first=recent_first)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n[queue] Stopped.")


if __name__ == "__main__":
    main()
