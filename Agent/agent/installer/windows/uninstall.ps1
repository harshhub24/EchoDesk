# EchoDesk Agent - Windows uninstaller.
#
# Usage (elevated PowerShell): .\uninstall.ps1
# Stops and removes the Windows service. Does NOT delete the project files,
# your .env, or any local device credentials.

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallDir = (Resolve-Path (Join-Path $ScriptDir "..\..\..")).Path

$currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must be run as Administrator."
    exit 1
}

$venvPython = Join-Path $InstallDir "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = "python"
}

& $venvPython -m agent.services.installer uninstall

Write-Host "Service removed. To fully decommission this device, also consider:"
Write-Host "  - Revoking its API key from the owner account (DELETE /devices/{id}/api-key)"
Write-Host "  - Deleting $InstallDir\agent\device_credentials.json"
Write-Host "  - Deleting the install directory: $InstallDir"
