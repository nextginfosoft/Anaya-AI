<#
.SYNOPSIS
    Makes Anaya AI start when you sign in to Windows (adds a shortcut to your Startup folder).
.DESCRIPTION
    Runs pythonw.exe main.py, so there is no console window. The project's venv is used if it exists.
    Safe to run again: it just refreshes the shortcut. Use -WhatIf to see what would happen.
#>
[CmdletBinding(SupportsShouldProcess)]
param()

$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$venvPythonw = Join-Path $root 'venv\Scripts\pythonw.exe'

if (Test-Path $venvPythonw) {
    $pythonw = $venvPythonw
}
else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { throw 'Python was not found. Run scripts\setup.ps1 first.' }
    $pythonw = Join-Path (Split-Path $python.Source) 'pythonw.exe'
}
if (-not (Test-Path $pythonw)) { throw "pythonw.exe was not found at $pythonw" }

$link = Join-Path ([Environment]::GetFolderPath('Startup')) 'Anaya AI.lnk'

if ($PSCmdlet.ShouldProcess($link, "Create startup shortcut to `"$pythonw`" main.py")) {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($link)
    $shortcut.TargetPath = $pythonw
    $shortcut.Arguments = 'main.py'
    $shortcut.WorkingDirectory = $root
    $shortcut.WindowStyle = 7
    $shortcut.Description = 'Anaya AI voice assistant (push-to-talk)'
    $shortcut.Save()
    Write-Host "Anaya will start when you sign in. Shortcut: $link"
}
