<#
.SYNOPSIS
    Sets up Anaya AI: a virtual environment, the Python packages and the local AI model.
.PARAMETER SkipModel
    Do not run "ollama pull" (useful for developers who only want to run the tests).
#>
param([switch]$SkipModel)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python 3.12 or newer is required: https://www.python.org/downloads/'
}

Write-Host '1/3 Creating the virtual environment (venv)...'
python -m venv venv
$py = Join-Path (Get-Location) 'venv\Scripts\python.exe'

Write-Host '2/3 Installing packages...'
& $py -m pip install --upgrade pip
& $py -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Package installation failed.' }

Write-Host '3/3 Local AI model...'
if ($SkipModel) {
    Write-Host '    skipped (-SkipModel)'
}
elseif (Get-Command ollama -ErrorAction SilentlyContinue) {
    ollama pull llama3.2:3b
}
else {
    Write-Warning 'Ollama was not found. Install it from https://ollama.com/download, then run: ollama pull llama3.2:3b'
}

Write-Host ''
Write-Host 'Done. Start Anaya with:  .\venv\Scripts\python.exe main.py'
Write-Host 'Start with Windows:      .\scripts\install_startup.ps1'
