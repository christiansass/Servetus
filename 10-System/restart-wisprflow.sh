#!/bin/bash
# Restart Wispr Flow — run when hotkey stops responding after 6-minute dictation limit
# Usage: bash restart-wisprflow.sh
# Or bind via Automator Quick Action / Raycast / Hammerspoon

pkill -x "Wispr Flow" 2>/dev/null
sleep 2
open "/Applications/Wispr Flow.app"
sleep 4
osascript -e 'tell application "System Events" to tell process "Wispr Flow" to click button 1 of window 2'
