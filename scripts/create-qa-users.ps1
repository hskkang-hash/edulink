param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,

    [string]$OutputFile = "e2e/qa-users-live.json"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$users = @(
    @{ role = "instructor"; email = "qa.instructor@edulink.local"; password = "QaPass123!"; display_name = "QA Instructor" },
    @{ role = "institution"; email = "qa.institution@edulink.local"; password = "QaPass123!"; display_name = "QA Institution" },
    @{ role = "district"; email = "qa.district@edulink.local"; password = "QaPass123!"; display_name = "QA District" },
    @{ role = "admin"; email = "qa.admin@edulink.local"; password = "QaPass123!"; display_name = "QA Admin" }
)

$registerUri = "{0}/auth/register" -f $BaseUrl.TrimEnd('/')
$results = @()

foreach ($user in $users) {
    $body = @{ email = $user.email; password = $user.password; role = $user.role } | ConvertTo-Json

    try {
        Invoke-RestMethod -Method Post -Uri $registerUri -Body $body -ContentType "application/json" -TimeoutSec 25 | Out-Null
        $results += [ordered]@{
            email = $user.email
            role = $user.role
            password = $user.password
            status = "created"
            message = "registered"
        }
        Write-Host "[qa-users] created: $($user.email)"
    }
    catch {
        $statusCode = $null
        $message = $_.Exception.Message

        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }

        $normalizedStatus = if ($statusCode -eq 409 -or $message -match "already|exists|duplicate") {
            "exists"
        }
        elseif ($statusCode -eq 503) {
            "backend_unavailable"
        }
        else {
            "failed"
        }

        $results += [ordered]@{
            email = $user.email
            role = $user.role
            password = $user.password
            status = $normalizedStatus
            message = $message
        }
        Write-Warning "[qa-users] ${normalizedStatus}: $($user.email) - $message"
    }
}

$outputDir = Split-Path -Parent $OutputFile
if ($outputDir -and -not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

$summary = [ordered]@{
    executed_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    base_url = $BaseUrl
    register_uri = $registerUri
    users = $results
}

$summary | ConvertTo-Json -Depth 5 | Set-Content -Path $OutputFile -Encoding UTF8

Write-Host "[qa-users] Output: $OutputFile"
