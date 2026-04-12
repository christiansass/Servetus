#!/usr/bin/env bash
# migrate-binaryranch.sh
# Direct clone of BinaryRanch R420 to a destination server.
#
# Usage:
#   bash migrate-binaryranch.sh <destination_ip>
#
# What it does:
#   1. Stops all Docker containers on destination (safe — destination is fresh)
#   2. rsyncs Docker volumes, images, and configs from R420 to destination
#   3. Copies system configs (Docker daemon, Caddy)
#   4. Starts containers on destination
#   5. Prints cutover instructions
#
# What it does NOT do:
#   - Touch Tailscale (re-auth manually on destination after migration)
#   - Modify DNS/domains (do that manually once verified)
#   - Touch the source R420 at all
#
# Run from your Mac over Tailscale. Both machines must be reachable.
#
# Source:  R420 at 100.106.228.6 (christian@binaryranch)
# Dest:    provided as $1

set -euo pipefail

SRC="christian@100.106.228.6"
DST_IP="${1:?Usage: $0 <destination_ip>}"
DST="root@${DST_IP}"

DOCKER_ROOT="/media/docker/volumes"
NCDATA="/mnt/ncdata"
CADDY_CONF="/opt/nextcloud-aio"
DOCKER_DAEMON="/etc/docker/daemon.json"

GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"
BOLD="\033[1m"

log()  { echo -e "${GREEN}▶${RESET} $*"; }
warn() { echo -e "${YELLOW}⚠${RESET} $*"; }
die()  { echo -e "${RED}✗${RESET} $*"; exit 1; }
step() { echo -e "\n${BOLD}── $* ──${RESET}"; }


# ── Pre-flight ─────────────────────────────────────────────────────────────────

step "Pre-flight checks"

log "Checking source R420..."
ssh -o ConnectTimeout=10 "$SRC" "docker info > /dev/null" \
    || die "Cannot reach source R420 at $SRC"

log "Checking destination $DST_IP..."
ssh -o ConnectTimeout=10 "$DST" "uname -a" \
    || die "Cannot reach destination at $DST — is it provisioned and reachable?"

log "Checking destination OS..."
DST_OS=$(ssh "$DST" "cat /etc/os-release | grep PRETTY_NAME" 2>/dev/null)
echo "  $DST_OS"
[[ "$DST_OS" == *"Debian"* ]] || warn "Destination is not Debian — continue with caution"

log "Source Docker footprint:"
ssh "$SRC" "docker system df 2>/dev/null | tail -n +2"


# ── Stop destination containers ────────────────────────────────────────────────

step "Stopping any containers on destination"
ssh "$DST" "docker stop \$(docker ps -q) 2>/dev/null || true"
log "Destination containers stopped (or none were running)"


# ── Ensure destination paths exist ────────────────────────────────────────────

step "Preparing destination paths"
ssh "$DST" "
    mkdir -p ${DOCKER_ROOT}
    mkdir -p ${NCDATA}
    mkdir -p ${CADDY_CONF}
    mkdir -p /etc/docker
"
log "Paths ready"


# ── rsync Docker root (images + volumes) ──────────────────────────────────────

step "Syncing Docker root — ${DOCKER_ROOT}"
warn "This is the bulk of the data (~17GB). May take several minutes."

# We rsync from source to local then to dest, OR direct source→dest via jump
# Direct: rsync -az --delete src:path/ dst:path/
rsync -az --delete --progress \
    -e "ssh -o StrictHostKeyChecking=no" \
    "${SRC}:${DOCKER_ROOT}/" \
    "${DST}:${DOCKER_ROOT}/"

log "Docker root synced"


# ── rsync Nextcloud data dir ───────────────────────────────────────────────────

step "Syncing Nextcloud data — ${NCDATA}"
rsync -az --delete --progress \
    -e "ssh -o StrictHostKeyChecking=no" \
    "${SRC}:${NCDATA}/" \
    "${DST}:${NCDATA}/"

log "Nextcloud data synced"


# ── rsync Caddy config ────────────────────────────────────────────────────────

step "Syncing Caddy config — ${CADDY_CONF}"
rsync -az --delete \
    -e "ssh -o StrictHostKeyChecking=no" \
    "${SRC}:${CADDY_CONF}/" \
    "${DST}:${CADDY_CONF}/"

log "Caddy config synced"


# ── Copy Docker daemon config ─────────────────────────────────────────────────

step "Copying Docker daemon config"
rsync -az \
    -e "ssh -o StrictHostKeyChecking=no" \
    "${SRC}:${DOCKER_DAEMON}" \
    "${DST}:${DOCKER_DAEMON}"

log "Docker daemon config copied"


# ── Restart Docker on destination ────────────────────────────────────────────

step "Restarting Docker on destination"
ssh "$DST" "systemctl restart docker && sleep 3 && docker info > /dev/null"
log "Docker running on destination"


# ── Start Caddy on destination ────────────────────────────────────────────────

step "Starting Caddy"
ssh "$DST" "
    docker run -d \
        --name caddy \
        --network host \
        --restart unless-stopped \
        -v ${CADDY_CONF}/Caddyfile:/etc/caddy/Caddyfile:ro \
        -v caddy_data:/data \
        -v caddy_config:/config \
        -v /var/log/caddy:/var/log/caddy \
        caddy:2.7-alpine 2>/dev/null || docker start caddy
"
log "Caddy started"


# ── Start Nextcloud AIO mastercontainer ───────────────────────────────────────

step "Starting Nextcloud AIO mastercontainer"
ssh "$DST" "
    docker run -d \
        --name nextcloud-aio-mastercontainer \
        --restart unless-stopped \
        --publish 8080:8080 \
        -e NEXTCLOUD_DATADIR=/mnt/ncdata \
        -e APACHE_PORT=11000 \
        -e APACHE_IP_BINDING=127.0.0.1 \
        -e TALK_PORT=3478 \
        -e TRUSTED_PROXIES=127.0.0.1 \
        -e NEXTCLOUD_UPLOAD_LIMIT=10G \
        -e NEXTCLOUD_MAX_TIME=3600 \
        -e NEXTCLOUD_MEMORY_LIMIT=1024M \
        -e COLLABORA_SECCOMP_DISABLED=false \
        -e SKIP_DOMAIN_VALIDATION=false \
        -v nextcloud_aio_mastercontainer:/mnt/docker-aio-config \
        -v /var/run/docker.sock:/var/run/docker.sock \
        nextcloud/all-in-one:latest 2>/dev/null || docker start nextcloud-aio-mastercontainer
"
log "Nextcloud AIO mastercontainer started"


# ── Verify ────────────────────────────────────────────────────────────────────

step "Verifying destination"
sleep 5
ssh "$DST" "docker ps --format 'table {{.Names}}\t{{.Status}}'"


# ── Cutover instructions ──────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${GREEN}  Clone complete.${RESET}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo "  Before cutting over DNS, verify on destination:"
echo "    https://${DST_IP}:8080  — Nextcloud AIO panel"
echo ""
echo "  Tailscale — re-auth manually on destination:"
echo "    ssh ${DST} 'tailscale up --authkey=<your-key>'"
echo ""
echo "  DNS cutover — point cloud.binaryranch.com to: ${DST_IP}"
echo "  Once verified, update open-loops.md and proceed with R420 reprovision."
echo ""
