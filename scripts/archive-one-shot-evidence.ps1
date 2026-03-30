param(
    [string]$RcVersion = "v2.0.0-rc1",
    [string]$BaseUrl = "",
    [string]$ResultFile = "e2e/chromium-oneshot.json"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss")
$targetDir = Join-Path $repoRoot ("release/evidence/" + $timestamp)
New-Item -ItemType Directory -Path $targetDir -Force | Out-Null

$resultPath = Join-Path $repoRoot $ResultFile
$reportDir = Join-Path $repoRoot "e2e/report"
$reportIndex = Join-Path $reportDir "index.html"

if (-not (Test-Path $resultPath)) {
    throw "Result file not found: $ResultFile"
}

Copy-Item -Path $resultPath -Destination (Join-Path $targetDir (Split-Path $resultPath -Leaf)) -Force

if (Test-Path $reportDir) {
    Copy-Item -Path $reportDir -Destination (Join-Path $targetDir "report") -Recurse -Force
}

$sha = (& git rev-parse HEAD).Trim()
$summary = [ordered]@{
    archived_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    rc_version = $RcVersion
    base_url = $BaseUrl
    git_sha = $sha
    result_file = (Split-Path $resultPath -Leaf)
    report_available = (Test-Path $reportIndex)
}

$summary | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $targetDir "e2e-evidence-summary.json") -Encoding UTF8

Write-Host "[e2e-archive] Evidence archived: $targetDir"
