# Run all JSP comparison SA batches sequentially (random init via jsp_ft10_comparison.json template).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$instances = @("abz5", "ta02", "ta22", "ta31", "ta51")
$logDir = Join-Path $root "results"
$masterLog = Join-Path $logDir ".launch_logs_jsp_sa_random_init_master.log"

"[$(Get-Date -Format o)] Starting JSP SA rerun (random init)" | Out-File -FilePath $masterLog -Encoding utf8

foreach ($inst in $instances) {
    $log = Join-Path $logDir ".launch_logs_jsp_${inst}_simulated_annealing.log"
    $err = Join-Path $logDir ".launch_logs_jsp_${inst}_simulated_annealing.err"
    "[$(Get-Date -Format o)] BEGIN $inst simulated_annealing" | Tee-Object -FilePath $masterLog -Append
    python scripts/launch_jsp_run.py $inst simulated_annealing 2>&1 | Tee-Object -FilePath $log
    if ($LASTEXITCODE -ne 0) {
        "[$(Get-Date -Format o)] FAILED $inst exit=$LASTEXITCODE" | Tee-Object -FilePath $masterLog -Append
        exit $LASTEXITCODE
    }
    "[$(Get-Date -Format o)] DONE $inst" | Tee-Object -FilePath $masterLog -Append
}

"[$(Get-Date -Format o)] All JSP SA batches complete" | Tee-Object -FilePath $masterLog -Append
