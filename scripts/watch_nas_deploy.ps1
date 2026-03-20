param(
    [string]$RunId,
    [string]$Workflow = "deploy-nas.yml",
    [int]$IntervalSeconds = 8,
    [int]$TimeoutMinutes = 20,
    [string]$OutputDir = "logs/deploy",
    [switch]$SummarizeFailedLog
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-GhCli {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        throw "GitHub CLI (gh) was not found. Install gh and retry."
    }
}

function Get-TargetRunId {
    param(
        [string]$ProvidedRunId,
        [string]$WorkflowFile
    )

    if ($ProvidedRunId) {
        return [string]$ProvidedRunId
    }

    Write-Host "RunId not provided. Fetching latest workflow run..." -ForegroundColor Cyan
    $listJson = gh run list --workflow $WorkflowFile --limit 20 --json databaseId,status,conclusion,displayTitle,createdAt,event
    $runs = $listJson | ConvertFrom-Json

    if (-not $runs -or $runs.Count -eq 0) {
        throw "No workflow runs found. Trigger a run first, then retry."
    }

    $inProgress = $runs | Where-Object { $_.status -eq "in_progress" -or $_.status -eq "queued" } | Select-Object -First 1
    if ($inProgress) {
        return [string]$inProgress.databaseId
    }

    return [string]($runs | Select-Object -First 1).databaseId
}

function Show-JobStepSummary {
    param(
        [object]$RunInfo
    )

    if (-not $RunInfo.jobs) {
        return
    }

    foreach ($job in $RunInfo.jobs) {
        Write-Host "[Job] $($job.name): $($job.conclusion)"
        if ($job.steps) {
            foreach ($step in $job.steps) {
                Write-Host "  - [$($step.number)] $($step.name): $($step.conclusion)"
            }
        }
    }
}

function Show-FailurePatternSummary {
    param(
        [string]$LogPath
    )

    if (-not (Test-Path $LogPath)) {
        return
    }

    $patterns = @(
        "Health check failed",
        "502",
        "504",
        "Connection refused",
        "fatal:",
        "permission denied",
        "dubious ownership",
        "No such file",
        "timed out",
        "ERROR",
        "Error"
    )

    $hits = Select-String -Path $LogPath -Pattern $patterns -CaseSensitive:$false
    if (-not $hits) {
        Write-Host "No known failure pattern found in failed log."
        return
    }

    Write-Host "Failure pattern summary:" -ForegroundColor Yellow
    $hits |
        Group-Object { $_.Line.Trim() } |
        Sort-Object Count -Descending |
        Select-Object -First 10 |
        ForEach-Object {
            Write-Host ("  - x{0} {1}" -f $_.Count, $_.Name)
        }
}

Assert-GhCli

$targetRunId = Get-TargetRunId -ProvidedRunId $RunId -WorkflowFile $Workflow
$deadline = (Get-Date).AddMinutes($TimeoutMinutes)
$lastStatusLine = $null

Write-Host "Target RunId: $targetRunId" -ForegroundColor Green
Write-Host "Polling interval: ${IntervalSeconds}s, timeout: ${TimeoutMinutes}m"

while ($true) {
    $viewJson = gh run view $targetRunId --json status,conclusion,name,displayTitle,url,jobs
    $run = $viewJson | ConvertFrom-Json

    $conclusion = if ($null -eq $run.conclusion -or [string]::IsNullOrWhiteSpace([string]$run.conclusion)) { "null" } else { [string]$run.conclusion }
    $statusLine = "[{0}] status={1}, conclusion={2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $run.status, $conclusion
    if ($statusLine -ne $lastStatusLine) {
        Write-Host $statusLine
        $lastStatusLine = $statusLine
    }

    if ($run.status -eq "completed") {
        Write-Host "Run completed: $($run.displayTitle)"
        Write-Host "URL: $($run.url)"
        Show-JobStepSummary -RunInfo $run

        if ($run.conclusion -ne "success") {
            New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
            $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $failedLogPath = Join-Path $OutputDir "run_${targetRunId}_failed_${stamp}.log"
            $fullLogPath = Join-Path $OutputDir "run_${targetRunId}_full_${stamp}.log"

            gh run view $targetRunId --log-failed | Out-File -FilePath $failedLogPath -Encoding utf8
            gh run view $targetRunId --log | Out-File -FilePath $fullLogPath -Encoding utf8

            Write-Host "Saved failed log: $failedLogPath" -ForegroundColor Yellow
            Write-Host "Saved full log: $fullLogPath" -ForegroundColor Yellow

            if ($SummarizeFailedLog) {
                Show-FailurePatternSummary -LogPath $failedLogPath
            }

            exit 1
        }

        Write-Host "Deploy success" -ForegroundColor Green
        exit 0
    }

    if ((Get-Date) -gt $deadline) {
        throw "Timeout (${TimeoutMinutes}m): run did not complete. URL: $($run.url)"
    }

    Start-Sleep -Seconds $IntervalSeconds
}
