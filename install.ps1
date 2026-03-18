# =============================================================================
# Servetus One-Line Installer (Windows PowerShell)
# =============================================================================
# Usage (PowerShell, run as normal user):
#   irm https://raw.githubusercontent.com/christiansass/Servetus/main/install.ps1 | iex
#
# Or after cloning:
#   .\Servetus\install.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

$REPO = "https://github.com/christiansass/Servetus.git"

Write-Host ""
Write-Host "  +===============================+"
Write-Host "  |      SERVETUS  INSTALLER      |"
Write-Host "  +===============================+"
Write-Host ""

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------
foreach ($cmd in @("python", "git")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Error "'$cmd' is required but not found. Install it and re-run."
        exit 1
    }
}

# ---------------------------------------------------------------------------
# Obsidian root
# ---------------------------------------------------------------------------
$ObsidianRoot = Read-Host "Path to your Obsidian root folder (e.g. C:\Users\You\Obsidian)"
$ObsidianRoot = $ObsidianRoot.Trim('"').Trim("'")

if (-not (Test-Path $ObsidianRoot -PathType Container)) {
    Write-Error "Directory not found: $ObsidianRoot"
    exit 1
}

$VaultPath  = Join-Path $ObsidianRoot "Servetus"
$InboxPath  = Join-Path $ObsidianRoot "Inbox\Claude"

# ---------------------------------------------------------------------------
# Clone or update vault
# ---------------------------------------------------------------------------
if (Test-Path (Join-Path $VaultPath ".git") -PathType Container) {
    Write-Host ""
    Write-Host "Updating existing Servetus vault at $VaultPath..."
    git -C "$VaultPath" pull
} else {
    Write-Host ""
    Write-Host "Cloning Servetus into $VaultPath..."
    git clone $REPO "$VaultPath"
}

# ---------------------------------------------------------------------------
# Ensure sibling Inbox/Claude/ exists
# ---------------------------------------------------------------------------
New-Item -ItemType Directory -Force -Path $InboxPath | Out-Null
Write-Host "Inbox ready: $InboxPath"

# ---------------------------------------------------------------------------
# Install ~/bin equivalent (WindowsApps or user Scripts folder)
# ---------------------------------------------------------------------------
$BinDir = "$env:USERPROFILE\bin"
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

# Write sc.bat launcher
$ScBat = Join-Path $BinDir "sc.bat"
$SessionClose = Join-Path $VaultPath "10-System\session-close.py"
$ScContent = @"
@echo off
cd /d "$VaultPath"
claude %*
echo.
echo [servetus] Session ended. Capturing artifact...
python "$SessionClose"
"@
Set-Content -Path $ScBat -Value $ScContent -Encoding UTF8

# Write servetus-claude.bat (named alias)
$SvcBat = Join-Path $BinDir "servetus-claude.bat"
Copy-Item $ScBat $SvcBat -Force

Write-Host "  claude launcher  -> $ScBat"
Write-Host "  claude (named)   -> $SvcBat"

# ---------------------------------------------------------------------------
# Add ~/bin to PATH for current user (if not already present)
# ---------------------------------------------------------------------------
$CurrentPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
if ($CurrentPath -notlike "*$BinDir*") {
    [System.Environment]::SetEnvironmentVariable("PATH", "$BinDir;$CurrentPath", "User")
    Write-Host "Added $BinDir to user PATH. Restart your terminal to use 'sc'."
} else {
    Write-Host "$BinDir is already on PATH."
}

# ---------------------------------------------------------------------------
# Copy statusline script
# ---------------------------------------------------------------------------
$StatuslineSrc  = Join-Path $VaultPath "10-System\statusline.sh"
$ClaudeDir      = "$env:USERPROFILE\.claude"
$StatuslineDest = Join-Path $ClaudeDir "statusline.sh"

New-Item -ItemType Directory -Force -Path $ClaudeDir | Out-Null

if (Test-Path $StatuslineSrc) {
    Copy-Item $StatuslineSrc $StatuslineDest -Force
    Write-Host "  statusline -> $StatuslineDest"
    Write-Host "  Note: statusCommand in Claude Code on Windows is not yet supported."
    Write-Host "        The script is installed for when support is added."
} else {
    Write-Host "  statusline.sh not found at $StatuslineSrc -- skipping"
}

# ---------------------------------------------------------------------------
# Add PowerShell profile functions
# ---------------------------------------------------------------------------
$ProfileDir = Split-Path $PROFILE -Parent
New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

$ProfileBlock = @"

# Servetus
function sc { & "$ScBat" `$args }
function servetus-claude { & "$SvcBat" `$args }
"@

if (Test-Path $PROFILE) {
    $existing = Get-Content $PROFILE -Raw
    if ($existing -notlike "*# Servetus*") {
        Add-Content -Path $PROFILE -Value $ProfileBlock
        Write-Host "  Added sc / servetus-claude to PowerShell profile: $PROFILE"
    } else {
        Write-Host "  PowerShell profile already has Servetus entries."
    }
} else {
    Set-Content -Path $PROFILE -Value $ProfileBlock -Encoding UTF8
    Write-Host "  Created PowerShell profile with sc / servetus-claude: $PROFILE"
}

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "Installation complete."
Write-Host ""
Write-Host "  Claude Code     : sc   (launches Claude Code with auto-capture)"
Write-Host "  Claude (named)  : servetus-claude"
Write-Host ""
Write-Host "Restart your terminal to apply PATH changes."
Write-Host ""
