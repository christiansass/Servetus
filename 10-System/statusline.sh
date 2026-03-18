#!/usr/bin/env bash
# =============================================================================
# Servetus Statusline — KITT Edition
# =============================================================================
# Called by Claude Code's statusCommand on each poll cycle.
# Animation is driven by date +%s — no daemon required.
#
# States:
#   IDLE     [S] ○
#   WAITING  [S] ●/▮  ████░░░░░░  23%   (ticker, cursor blink)
#            [S] ●/▮  ↑46 ↓59  1h 23m
#   THINKING [S] ◈  ░░░█▓░░░░░░         (KITT scanner)
# =============================================================================

SESSION_FILE="$HOME/.servetus_session.json"
TICK=$(date +%s)

# Room label — prefer env var, fall back to ~/.servetus_session.json
# (Claude Code's statusCommand subprocess does not inherit parent env vars)
ROOM_RAW=""
if [[ -n "$SERVETUS_ROOM" ]]; then
    ROOM_RAW="$SERVETUS_ROOM"
elif [[ -f "$SESSION_FILE" ]]; then
    ROOM_RAW=$(python3 -c "
import json, pathlib
try:
    d = json.loads(pathlib.Path('$SESSION_FILE').read_text())
    print(d.get('room', ''))
except:
    print('')
" 2>/dev/null)
fi

# Truncate to 20 chars for statusline — arc names must stay short
ROOM=""
if [[ -n "$ROOM_RAW" ]]; then
    if (( ${#ROOM_RAW} > 20 )); then
        ROOM_RAW="${ROOM_RAW:0:19}…"
    fi
    ROOM=": ${ROOM_RAW}"
fi

# ---------------------------------------------------------------------------
# IDLE — no active session
# ---------------------------------------------------------------------------
if [[ ! -f "$SESSION_FILE" ]]; then
    echo "[S${ROOM}] ○"
    exit 0
fi

# ---------------------------------------------------------------------------
# Detect THINKING vs WAITING
# Read last ~800 bytes of the most recent JSONL for speed
# ---------------------------------------------------------------------------
THINKING=0
JSONL=""

JSONL=$(python3 -c "
import pathlib
p = pathlib.Path.home() / '.claude' / 'projects'
if not p.exists(): exit()
c = sorted(p.rglob('*.jsonl'), key=lambda x: x.stat().st_mtime, reverse=True)
print(c[0] if c else '')
" 2>/dev/null)

if [[ -n "$JSONL" && -f "$JSONL" ]]; then
    LAST_TYPE=$(tail -c 800 "$JSONL" | python3 -c "
import sys, json
last = ''
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    try:
        t = json.loads(line).get('type','')
        if t in ('user','assistant'): last = t
    except: pass
print(last)
" 2>/dev/null)
    [[ "$LAST_TYPE" == "user" ]] && THINKING=1
fi

# ---------------------------------------------------------------------------
# THINKING — KITT scanner
# ---------------------------------------------------------------------------
if (( THINKING )); then
    WIDTH=12
    PERIOD=$(( WIDTH * 2 - 2 ))
    POS=$(( TICK % PERIOD ))
    (( POS >= WIDTH )) && POS=$(( PERIOD - POS ))

    RED=$'\e[31m'
    RESET=$'\e[0m'
    BAR=""
    for (( i=0; i<WIDTH; i++ )); do
        if   (( i == POS     )); then BAR="${BAR}█"
        elif (( i == POS - 1 || i == POS + 1 )); then BAR="${BAR}▓"
        elif (( i == POS - 2 || i == POS + 2 )); then BAR="${BAR}░"
        else BAR="${BAR} "
        fi
    done

    echo "[S${ROOM}] ◈  ${RED}${BAR}${RESET}"
    exit 0
fi

# ---------------------------------------------------------------------------
# Parse token counts + session age
# ---------------------------------------------------------------------------
TOKEN_DATA=$(python3 - <<'PYEOF'
import pathlib, json, sys

projects = pathlib.Path.home() / ".claude" / "projects"
if not projects.exists():
    print("0 0 0 0")
    sys.exit(0)

candidates = sorted(projects.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
if not candidates:
    print("0 0 0 0")
    sys.exit(0)

jsonl = candidates[0]
input_tokens = output_tokens = cache_tokens = user_turns = assistant_turns = 0

try:
    for raw in jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
        raw = raw.strip()
        if not raw: continue
        try:
            obj = json.loads(raw)
        except: continue
        t = obj.get("type", "")
        if t == "user":
            user_turns += 1
        elif t == "assistant":
            assistant_turns += 1
            usage = obj.get("message", {}).get("usage", {})
            if usage:
                input_tokens  = usage.get("input_tokens", input_tokens)
                output_tokens = usage.get("output_tokens", output_tokens)
                cache_tokens  = usage.get("cache_read_input_tokens", cache_tokens)
except: pass

print(f"{input_tokens} {cache_tokens} {user_turns} {assistant_turns}")
PYEOF
)

INPUT_TOKENS=$(echo "$TOKEN_DATA" | awk '{print $1}')
CACHE_TOKENS=$(echo "$TOKEN_DATA" | awk '{print $2}')
USER_TURNS=$(echo "$TOKEN_DATA"   | awk '{print $3}')
ASST_TURNS=$(echo "$TOKEN_DATA"   | awk '{print $4}')

INPUT_TOKENS=${INPUT_TOKENS:-0}
CACHE_TOKENS=${CACHE_TOKENS:-0}
USER_TURNS=${USER_TURNS:-0}
ASST_TURNS=${ASST_TURNS:-0}

# Token bar
CONTEXT_LIMIT=200000
TOTAL=$(( INPUT_TOKENS + CACHE_TOKENS ))
PCT=$(( TOTAL * 100 / CONTEXT_LIMIT ))
(( PCT > 100 )) && PCT=100

FILLED=$(( PCT * 10 / 100 ))
EMPTY=$(( 10 - FILLED ))
TOKEN_BAR=""
for (( i=0; i<FILLED; i++ )); do TOKEN_BAR="${TOKEN_BAR}█"; done
for (( i=0; i<EMPTY;  i++ )); do TOKEN_BAR="${TOKEN_BAR}░"; done

# Session age from ~/.servetus_session.json
AGE=$(python3 -c "
import json, pathlib
from datetime import datetime, timezone
try:
    d = json.loads(pathlib.Path.home().joinpath('.servetus_session.json').read_text())
    s = d.get('started','')
    if not s: raise ValueError
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
    diff = int((datetime.now(timezone.utc) - dt).total_seconds())
    h, rem = divmod(diff, 3600)
    m = rem // 60
    print(f'{h}h {m:02d}m' if h else f'{m}m')
except:
    print('')
" 2>/dev/null)

# ---------------------------------------------------------------------------
# ACTIVE ticker — 2 panels, 4s each, cursor blink each second
# ---------------------------------------------------------------------------
DOT="●"
(( TICK % 2 == 1 )) && DOT="▮"

PANEL=$(( (TICK / 4) % 2 ))

if (( PANEL == 0 )); then
    echo "[S${ROOM}] ${DOT}  ${TOKEN_BAR}  ${PCT}%"
else
    AGE_PART=""
    [[ -n "$AGE" ]] && AGE_PART="  ${AGE}"
    echo "[S${ROOM}] ${DOT}  ↑${USER_TURNS} ↓${ASST_TURNS}${AGE_PART}"
fi
