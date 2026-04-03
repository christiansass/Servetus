#!/usr/bin/env bash
# deploy-services-wordinfilm.sh
# Deploys Servetus systemd services to WordInFilm (100.114.61.2) via Tailscale SSH.
# Run from Mac: bash 10-System/deploy-services-wordinfilm.sh

set -euo pipefail
WIF="100.114.61.2"
VAULT_REMOTE="/mnt/Cloud/Nextcloud/Obsidian/Servetus"
SYSTEMD_REMOTE="/home/sastian/.config/systemd/user"

echo "=== Deploying Servetus services to WordInFilm ==="

echo "--- 1. Ensuring ~/.config/systemd/user exists ---"
ssh sastian@${WIF} "mkdir -p ${SYSTEMD_REMOTE}"

echo "--- 2. Installing service files ---"
for svc in servetus-transcription-queue servetus-talk-listener; do
    scp "${VAULT_REMOTE}/10-System/systemd/${svc}.service" \
        "sastian@${WIF}:${SYSTEMD_REMOTE}/${svc}.service"
    echo "   Installed: ${svc}.service"
done

echo "--- 3. Reloading systemd daemon ---"
ssh sastian@${WIF} "systemctl --user daemon-reload"

echo "--- 4. Enabling and restarting services ---"
ssh sastian@${WIF} "
    systemctl --user enable servetus-transcription-queue servetus-talk-listener
    systemctl --user restart servetus-transcription-queue servetus-talk-listener
    echo 'Service status:'
    systemctl --user status servetus-transcription-queue --no-pager -l | tail -6
    systemctl --user status servetus-talk-listener --no-pager -l | tail -6
"

echo ""
echo "=== Deploy complete ==="
echo "To tail transcription log:"
echo "  ssh sastian@${WIF} 'tail -f ${VAULT_REMOTE}/10-System/transcription-queue.log'"
echo "To tail talk log:"
echo "  ssh sastian@${WIF} 'tail -f ${VAULT_REMOTE}/10-System/talk-listener.log'"
