# Move all JSP comparison result batches and launch logs into a dated backup folder.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backup = Join-Path $root "results\backup\jsp_lpt_init_2026-08-07"
New-Item -ItemType Directory -Force -Path $backup | Out-Null

$moved = @()
Get-ChildItem (Join-Path $root "results") -Directory | Where-Object { $_.Name -match "_jsp_" } | ForEach-Object {
    Move-Item -LiteralPath $_.FullName -Destination $backup
    $moved += $_.Name
}

Get-ChildItem (Join-Path $root "results") -File | Where-Object { $_.Name -like ".launch_logs*jsp*" } | ForEach-Object {
    Move-Item -LiteralPath $_.FullName -Destination $backup
    $moved += $_.Name
}

$readme = @"
JSP comparison backup (structured job-major init labeled longest_processing_time)
Created: 2026-08-07
Reason: Comparison rerun with domain_config.initial_solution = random

Moved items ($($moved.Count)):
$($moved -join "`n")
"@
Set-Content -Path (Join-Path $backup "README.txt") -Value $readme -Encoding UTF8
Write-Output "Backed up $($moved.Count) items to $backup"
