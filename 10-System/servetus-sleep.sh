#!/usr/bin/env bash
# servetus-sleep.sh
# Clean shutdown of all Servetus processes on WordInFilm.
# Stops services, kills orphans, clears logs and temp audio.
# Run locally: bash 10-System/servetus-sleep.sh
# Run on WIF:  servetus-sleep  (alias in ~/.zshrc)

set -uo pipefail

VAULT="/mnt/Cloud/Nextcloud/Obsidian/Servetus"
LOG_DIR="$VAULT/10-System"
TALK_AUDIO_DIR="/mnt/Cloud/Nextcloud/Talk/Audio"

echo ""
echo "=== Servetus Sleep ==="
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# --- 1. Stop services (reverse dependency order) ---
echo "--- Stopping services ---"
for svc in servetus-transcription-queue servetus-talk-listener servetus-chromium servetus-display; do
    if systemctl --user is-active --quiet "$svc" 2>/dev/null; then
        systemctl --user stop "$svc"
        echo "  stopped: $svc"
    else
        echo "  already stopped: $svc"
    fi
done
echo ""

# --- 2. Kill orphaned processes ---
echo "--- Killing orphans ---"

# Whisper (can outlive the service if mid-transcription)
WHISPER_PIDS=$(pgrep -f "whisper" 2>/dev/null || true)
if [ -n "$WHISPER_PIDS" ]; then
    echo "  killing whisper pids: $WHISPER_PIDS"
    kill $WHISPER_PIDS 2>/dev/null || true
    sleep 2
    # Force if still alive
    kill -9 $WHISPER_PIDS 2>/dev/null || true
else
    echo "  no orphaned whisper processes"
fi

# Talk listener
TALK_PIDS=$(pgrep -f "talk-listener.py" 2>/dev/null || true)
if [ -n "$TALK_PIDS" ]; then
    echo "  killing talk-listener pids: $TALK_PIDS"
    kill $TALK_PIDS 2>/dev/null || true
else
    echo "  no orphaned talk-listener processes"
fi

# Xvfb virtual display
XVFB_PIDS=$(pgrep -f "Xvfb :1" 2>/dev/null || true)
if [ -n "$XVFB_PIDS" ]; then
    echo "  killing Xvfb :1 pids: $XVFB_PIDS"
    kill $XVFB_PIDS 2>/dev/null || true
else
    echo "  no orphaned Xvfb processes"
fi

# Zombie reap: log them (can't kill directly — parent must collect)
ZOMBIES=$(ps aux | awk '$8 == "Z" {print $2, $11}' 2>/dev/null || true)
if [ -n "$ZOMBIES" ]; then
    echo "  zombie processes (parent must reap — logged only):"
    echo "$ZOMBIES" | sed 's/^/    /'
else
    echo "  no zombie processes"
fi
echo ""

# --- 3. Clear log files ---
echo "--- Clearing logs ---"
for logfile in \
    "$LOG_DIR/transcription-queue.log" \
    "$LOG_DIR/talk-listener.log" \
    "$LOG_DIR/secretary.log" \
    "$LOG_DIR/approval.log"; do
    if [ -f "$logfile" ]; then
        SIZE=$(du -sh "$logfile" | cut -f1)
        > "$logfile"
        echo "  cleared: $(basename $logfile) (was $SIZE)"
    fi
done
echo ""

# --- 4. Clear temp audio recordings ---
echo "--- Clearing temp audio ---"

# /tmp audio files
TMP_AUDIO=$(find /tmp -maxdepth 1 \( -name "*.wav" -o -name "*.mp3" -o -name "*.webm" -o -name "*.m4a" \) 2>/dev/null || true)
if [ -n "$TMP_AUDIO" ]; then
    echo "$TMP_AUDIO" | while read f; do
        SIZE=$(du -sh "$f" | cut -f1)
        rm -f "$f"
        echo "  removed: $f ($SIZE)"
    done
else
    echo "  no temp audio in /tmp"
fi

# Talk audio recordings older than 24h (keep recent in case still processing)
if [ -d "$TALK_AUDIO_DIR" ]; then
    OLD_AUDIO=$(find "$TALK_AUDIO_DIR" -name "*.webm" -o -name "*.wav" -mmin +1440 2>/dev/null || true)
    if [ -n "$OLD_AUDIO" ]; then
        echo "$OLD_AUDIO" | while read f; do
            SIZE=$(du -sh "$f" | cut -f1)
            rm -f "$f"
            echo "  removed: $(basename $f) ($SIZE)"
        done
    else
        echo "  no stale Talk audio (>24h)"
    fi
fi
echo ""

# --- 5. Final status ---
echo "--- Final service status ---"
for svc in servetus-transcription-queue servetus-talk-listener servetus-chromium servetus-display; do
    STATUS=$(systemctl --user is-active "$svc" 2>/dev/null || echo "inactive")
    echo "  $svc: $STATUS"
done
echo ""
echo "=== Servetus is asleep. ==="
echo ""
