param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,

    [string]$Project = "chromium",

    [string]$ResultFile = "e2e/chromium-oneshot.json",

    [string]$QaEmail = "qa.instructor@edulink.local",

    [string]$QaPassword = "QaPass123!",

    [switch]$AllowLocalUrl
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not $AllowLocalUrl -and $BaseUrl -match "localhost|127\.0\.0\.1") {
    throw "BaseUrl must be a real URL for one-shot execution. Use -AllowLocalUrl only for local rehearsal."
}

$env:E2E_BASE_URL = $BaseUrl

Write-Host "[one-shot-e2e] BaseUrl: $BaseUrl"
Write-Host "[one-shot-e2e] Project: $Project"
Write-Host "[one-shot-e2e] ResultFile: $ResultFile"

$registerUri = "{0}/auth/register" -f $BaseUrl.TrimEnd('/')
$registerBody = @{ email = $QaEmail; password = $QaPassword; role = "instructor" } | ConvertTo-Json
try {
    Invoke-RestMethod -Method Post -Uri $registerUri -Body $registerBody -ContentType "application/json" -TimeoutSec 20 | Out-Null
    Write-Host "[one-shot-e2e] QA account ensured via register: $QaEmail"
}
catch {
    # Existing user or strict policy response is acceptable for one-shot precondition.
    Write-Warning "QA account pre-check returned non-blocking response: $($_.Exception.Message)"
}

if (Test-Path $ResultFile) {
    try {
        Remove-Item $ResultFile -Force
    }
    catch {
        $originalPath = $ResultFile
        $dir = Split-Path -Parent $originalPath
        $name = [System.IO.Path]::GetFileNameWithoutExtension($originalPath)
        $ext = [System.IO.Path]::GetExtension($originalPath)
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $fallbackName = "{0}-{1}{2}" -f $name, $stamp, $ext
        $ResultFile = if ($dir) { Join-Path $dir $fallbackName } else { $fallbackName }
        Write-Warning "Result file was locked and could not be removed. Using fallback file: $ResultFile"
    }
}

$resultDir = Split-Path -Parent $ResultFile
if ($resultDir -and -not (Test-Path $resultDir)) {
    New-Item -ItemType Directory -Path $resultDir -Force | Out-Null
}
$env:PLAYWRIGHT_HTML_OPEN = "never"

$npxCmd = Get-Command npx.cmd -ErrorAction SilentlyContinue
if (-not $npxCmd) {
    throw "npx.cmd was not found. Install Node.js/npm before running one-shot e2e."
}

& npx.cmd playwright test "--project=$Project" "--reporter=dot,html"
$exitCode = $LASTEXITCODE

$summary = [ordered]@{
    executed_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    base_url = $BaseUrl
    project = $Project
    exit_code = $exitCode
    status = $(if ($exitCode -eq 0) { "pass" } else { "fail" })
}

$summary | ConvertTo-Json -Depth 4 | Set-Content -Path $ResultFile -Encoding UTF8

if ($exitCode -ne 0) {
    throw "One-shot E2E failed with exit code $exitCode"
}

if (-not (Test-Path $ResultFile)) {
    throw "One-shot E2E completed but JSON report was not generated: $ResultFile"
}

$reportInfo = Get-Item $ResultFile
if ($reportInfo.Length -le 2) {
    throw "One-shot E2E JSON report is empty: $ResultFile"
}

Write-Host "[one-shot-e2e] Completed successfully."
Write-Host "[one-shot-e2e] JSON report: $ResultFile"
Write-Host "[one-shot-e2e] HTML report: e2e/report/index.html"
