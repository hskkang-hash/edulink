#!/usr/bin/env pwsh
<#
.SYNOPSIS
    EduLink 무인 개발 환경 시작
    
.DESCRIPTION
    백그라운드에서 자동 개발 파이프라인을 시작합니다.
    - 15분 주기로 자동 테스트, 커밋, 배포
    - 로그 파일: auto-dev-daemon.log
    - 언제든지 중단 가능
    
.EXAMPLE
    .\start-auto-dev.ps1               # 백그라운드 시작
    .\start-auto-dev.ps1 -console      # 콘솔에서 실행
    .\start-auto-dev.ps1 -interval 30  # 30분 주기로 시작
#>

param(
    [switch]$console = $false,   # 콘솔에서 실행 (백그라운드 아님)
    [int]$interval = 15,         # 주기 (분)
    [switch]$once = $false,      # 1회만
    [switch]$forceLegacyLoop = $false
)

if (-not $forceLegacyLoop) {
    Write-Host "Legacy Auto-Dev Loop is disabled for this project." -ForegroundColor Yellow
    Write-Host "Proceed with current manual development only." -ForegroundColor Yellow
    Write-Host "If you intentionally need the legacy loop, run with -forceLegacyLoop." -ForegroundColor DarkYellow
    exit 0
}

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$DAEMON_SCRIPT = Join-Path $SCRIPT_DIR "auto-dev-daemon.ps1"
$LOG_FILE = Join-Path $SCRIPT_DIR "auto-dev-daemon.log"

function Check-Prerequisites {
    Write-Host "✓ Checking prerequisites..." -ForegroundColor Cyan
    
    $checks = @(
        @{ name = "Python"; cmd = "python --version" },
        @{ name = "Git"; cmd = "git --version" },
        @{ name = "PowerShell"; cmd = "$PSVersionTable.PSVersion" }
    )
    
    foreach ($check in $checks) {
        try {
            if ($check.cmd -eq "$PSVersionTable.PSVersion") {
                Write-Host "  ✓ PowerShell: $($PSVersionTable.PSVersion.ToString())" -ForegroundColor Green
            } else {
                $result = Invoke-Expression $check.cmd 2>&1 | Select-Object -First 1
                Write-Host "  ✓ $($check.name): $result" -ForegroundColor Green
            }
        } catch {
            Write-Host "  ✗ $($check.name) not found" -ForegroundColor Red
        }
    }
}

function Show-Menu {
    Write-Host "`n========== EduLink Auto-Dev Mode ==========" -ForegroundColor Cyan
    Write-Host "    Autonomous development every ${interval} minutes" -ForegroundColor Cyan
    Write-Host "    Features:" -ForegroundColor Cyan
    Write-Host "      • Automated testing" -ForegroundColor Gray
    Write-Host "      • Auto commit & push" -ForegroundColor Gray
    Write-Host "      • Deployment validation" -ForegroundColor Gray
    Write-Host "      • Release preparation" -ForegroundColor Gray
    Write-Host "`n    Logs: $LOG_FILE" -ForegroundColor Gray
    Write-Host "=========================================`n" -ForegroundColor Cyan
}

function Start-BackgroundDaemon {
    Write-Host "🚀 Starting background daemon..." -ForegroundColor Yellow
    
    # 이미 실행 중인지 확인
    $existing = Get-Process -Name "pwsh" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*auto-dev-daemon*"
    }
    
    if ($existing) {
        Write-Host "⚠ Background daemon already running (PID: $($existing.Id))" -ForegroundColor Yellow
        Write-Host "  View logs: Get-Content '$LOG_FILE' -Tail 50 -Wait" -ForegroundColor Gray
        return
    }
    
    # 백그라운드 프로세스 시작
    $argList = "-NoProfile -ExecutionPolicy Bypass -File `"$DAEMON_SCRIPT`" -interval $interval"
    if ($once) { $argList += " -once" }
    
    $process = Start-Process powershell.exe -ArgumentList $argList -WindowStyle Hidden -PassThru
    
    Write-Host "✓ Background daemon started (PID: $($process.Id))" -ForegroundColor Green
    Write-Host "`n  Monitor progress:" -ForegroundColor Cyan
    Write-Host "    Get-Content '$LOG_FILE' -Tail 50 -Wait" -ForegroundColor Gray
    Write-Host "`n  Kill daemon:" -ForegroundColor Cyan
    Write-Host "    Stop-Process -Id $($process.Id)" -ForegroundColor Gray
    Write-Host "`n  View status:" -ForegroundColor Cyan
    Write-Host "    Get-Process -Id $($process.Id)" -ForegroundColor Gray
}

function Start-ConsoleDaemon {
    Write-Host "🎮 Running in console mode..." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Gray
    
    & $DAEMON_SCRIPT -interval $interval -once:$once
}

# ===== Main =====

Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force -ErrorAction SilentlyContinue

Check-Prerequisites
Show-Menu

if ($console) {
    Start-ConsoleDaemon
} else {
    Start-BackgroundDaemon
    
    # 시작 후 처음 로그 표시
    Write-Host "`nInitial logs:" -ForegroundColor Gray
    Start-Sleep -Seconds 2
    if (Test-Path $LOG_FILE) {
        Get-Content $LOG_FILE -Tail 10
    }
}
