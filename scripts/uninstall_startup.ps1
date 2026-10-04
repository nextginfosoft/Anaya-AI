<#
.SYNOPSIS
    Stops Anaya AI from starting with Windows (removes the Startup shortcut).
    It does not touch any other file. Use -WhatIf to see what would happen.
#>
[CmdletBinding(SupportsShouldProcess)]
param()

$link = Join-Path ([Environment]::GetFolderPath('Startup')) 'Anaya AI.lnk'

if (-not (Test-Path $link)) {
    Write-Host 'Anaya is not set to start with Windows (no shortcut found).'
    return
}

if ($PSCmdlet.ShouldProcess($link, 'Remove startup shortcut')) {
    Remove-Item $link
    Write-Host 'Removed. Anaya will no longer start when you sign in.'
}
