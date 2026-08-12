# EchoDesk Agent - Windows installer.
#
# Usage (elevated PowerShell, i.e. "Run as Administrator"):
#   .\install.ps1
#
# Expects to be run from inside agent\installer\windows\ of an already-placed
# project copy (copy the whole project - the folder containing run.py and
# agent\ - to its final location, e.g. C:\Program Files\EchoDeskAgent,
# before running this).

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallDir = (Resolve-Path (Join-Path $ScriptDir "..\..\..")).Path
$AgentDir = Join-Path $InstallDir "agent"

Write-Host "EchoDesk Agent installer"
Write-Host "Install directory: $InstallDir"

$currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must be run as Administrator."
    exit 1
}

$EnvFile = Join-Path $AgentDir ".env"
$EnvExample = Join-Path $AgentDir ".env.example"
if (-not (Test-Path $EnvFile)) {
    if (Test-Path $EnvExample) {
        Write-Host "No agent\.env found - copying from .env.example."
        Write-Host "You MUST edit agent\.env before the Agent can connect (backend URL + credentials)."
        Copy-Item $EnvExample $EnvFile
    } else {
        Write-Warning "agent\.env and agent\.env.example both missing - create agent\.env manually."
    }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error "python was not found on PATH. Install Python 3.12+ and re-run."
    exit 1
}

Write-Host "Creating virtual environment..."
python -m venv (Join-Path $InstallDir "venv")
$venvPython = Join-Path $InstallDir "venv\Scripts\python.exe"

& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install -r (Join-Path $AgentDir "requirements.txt") --quiet

Write-Host "Installing Windows service..."
& $venvPython -m agent.services.installer install

Write-Host ""
Write-Host "Done. Check status with: Get-Service EchoDeskAgent"
Write-Host "Logs: $AgentDir\logs\agent.log"
