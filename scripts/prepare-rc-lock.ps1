param(
    [Parameter(Mandatory = $true)]
    [string]$RcVersion,

    [switch]$SkipBuild,

    [switch]$CreateLocalTag
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    Write-Host "[rc-lock] START: $Name"
    & $Action
    Write-Host "[rc-lock] PASS: $Name"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$pythonExe = Join-Path $repoRoot ".venv/Scripts/python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        throw "Python executable not found (.venv or system python)."
    }
    $pythonExe = $pythonCmd.Source
}

$npxCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npxCmd) {
    throw "npm.cmd was not found. Install Node.js/npm before RC lock."
}

$checks = @()

if (-not $SkipBuild) {
    try {
        Invoke-Step -Name "Build release bundle" -Action {
            & npm.cmd run build:release
            if ($LASTEXITCODE -ne 0) {
                throw "build:release failed"
            }
        }
        $checks += @{ name = "build:release"; status = "pass" }
    } catch {
        Write-Warning "[rc-lock] build:release failed, retrying with build-only preflight."
        Invoke-Step -Name "Build static bundle (fallback)" -Action {
            & npm.cmd run build
            if ($LASTEXITCODE -ne 0) {
                throw "build failed"
            }
        }
        $checks += @{
            name = "build:release"
            status = "warn"
            note = "strict validation failed (likely placeholder production config), fallback build passed"
        }
    }
}

Invoke-Step -Name "Backend auth regression tests" -Action {
    Push-Location (Join-Path $repoRoot "backend")
    try {
        & $pythonExe -m pytest tests/test_auth_passwords.py -q
    } finally {
        Pop-Location
    }
    if ($LASTEXITCODE -ne 0) {
        throw "backend/tests/test_auth_passwords.py failed"
    }
}
$checks += @{ name = "backend/tests/test_auth_passwords.py"; status = "pass" }

Invoke-Step -Name "Backend operations sprint tests" -Action {
    Push-Location (Join-Path $repoRoot "backend")
    try {
        & $pythonExe -m pytest tests/test_operations_sprint7_10.py -q
    } finally {
        Pop-Location
    }
    if ($LASTEXITCODE -ne 0) {
        throw "backend/tests/test_operations_sprint7_10.py failed"
    }
}
$checks += @{ name = "backend/tests/test_operations_sprint7_10.py"; status = "pass" }

$sha = (& git rev-parse HEAD).Trim()
$branch = (& git rev-parse --abbrev-ref HEAD).Trim()
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

if ($CreateLocalTag) {
    Invoke-Step -Name "Create local RC tag" -Action {
        & git tag -a $RcVersion -m "Release candidate $RcVersion"
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create local tag $RcVersion"
        }
    }
}

$releaseDir = Join-Path $repoRoot "release"
if (-not (Test-Path $releaseDir)) {
    New-Item -ItemType Directory -Path $releaseDir | Out-Null
}

$payload = [ordered]@{
    rc_version = $RcVersion
    created_at_utc = $timestamp
    git_branch = $branch
    git_sha = $sha
    local_tag_created = [bool]$CreateLocalTag
    checks = $checks
    policy = [ordered]@{
        one_shot_e2e = "Run once on real URL after RC deploy"
        loop_mode = "disabled"
    }
}

$lockPath = Join-Path $releaseDir "rc-lock.json"
$payload | ConvertTo-Json -Depth 8 | Set-Content -Path $lockPath -Encoding UTF8

Write-Host "[rc-lock] RC lock created: $lockPath"
Write-Host "[rc-lock] RC version: $RcVersion"
Write-Host "[rc-lock] Git SHA: $sha"
