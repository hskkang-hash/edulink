#!/usr/bin/env pwsh
<#
.SYNOPSIS
    EduLink 무인 24/7 자동 개발 모드
    
.DESCRIPTION
    사용자 개입 없이 15분 주기로 자동 개발을 계속 진행:
    - 테스트 실행
    - 자동 커밋
    - 배포 안정성 검증
    
.EXAMPLE
    .\auto-dev-daemon.ps1              # 무한 루프 시작
    .\auto-dev-daemon.ps1 -interval 30 # 30분 주기
    .\auto-dev-daemon.ps1 -once        # 1회만 실행
#>

param(
    [int]$interval = 15,    # 분 단위 주기 (기본 15분)
    [switch]$once = $false,  # 1회만 실행
    [switch]$forceLegacyLoop = $false
)

if (-not $forceLegacyLoop) {
    Write-Host "Legacy Auto-Dev daemon loop is disabled for this project." -ForegroundColor Yellow
    Write-Host "Use current manual development flow only." -ForegroundColor Yellow
    exit 0
}

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$LOG_FILE = Join-Path $SCRIPT_DIR "auto-dev-daemon.log"
$LOCK_FILE = Join-Path $SCRIPT_DIR ".auto-dev.lock"

function Log([string]$level, [string]$msg) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] [$level] $msg"
    Write-Host $logLine
    Add-Content -Path $LOG_FILE -Value $logLine -Encoding UTF8
}

function Initialize {
    Log "START" "============================================"
    Log "INFO" "Daemon started | Interval: ${interval}min | Once: ${once}"
}

function Check-Lock {
    if (Test-Path $LOCK_FILE) {
        $lockTime = (Get-Item $LOCK_FILE).LastWriteTime
        $age = (Get-Date) - $lockTime
        
        # 락 파일이 30분 이상 오래되면 무시
        if ($age.TotalMinutes -gt 30) {
            Log "WARN" "⚠ Stale lock file detected, removing..."
            Remove-Item $LOCK_FILE -Force -ErrorAction SilentlyContinue
            return $false
        } else {
            Log "WARN" "⚠ Another instance running (lock age: $([math]::Round($age.TotalMinutes))min)"
            return $true
        }
    }
    return $false
}

function Set-Lock {
    Set-Content -Path $LOCK_FILE -Value (Get-Date -Format "o") -Encoding UTF8
}

function Release-Lock {
    Remove-Item $LOCK_FILE -Force -ErrorAction SilentlyContinue
}

function Run-AutoDev {
    <# auto-dev.ps1 실행 #>
    Log "INFO" "Triggering auto-dev pipeline..."
    
    try {
        Push-Location $SCRIPT_DIR
        
        # auto-dev.ps1이 있으면 실행, 없으면 dev-sprint.ps1 실행
        if (Test-Path "auto-dev.ps1") {
            Log "INFO" "Running auto-dev.ps1 (quick mode)..."
            & .\auto-dev.ps1 -step quick 2>&1 | ForEach-Object {
                Log "PIPE" $_
            }
        } elseif (Test-Path "dev-sprint.ps1") {
            Log "INFO" "Running dev-sprint.ps1..."
            & .\dev-sprint.ps1 2>&1 | ForEach-Object {
                Log "PIPE" $_
            }
        } else {
            Log "ERROR" "✗ No automation script found"
            return $false
        }
        
        Log "SUCCESS" "✓ Pipeline cycle completed"
        return $true
        
    } catch {
        Log "ERROR" "✗ Pipeline error: $_"
        return $false
    } finally {
        Pop-Location
    }
}

function Wait-ForNextCycle {
    Log "INFO" "Waiting ${interval} minutes until next cycle..."
    for ($i = 0; $i -lt $interval; $i++) {
        if ($i % 5 -eq 0) {
            Log "INFO" "[$([math]::Round($interval - $i))min remaining...]"
        }
        Start-Sleep -Seconds 60
    }
}

# ===== Main Loop =====

Initialize

$cycleCount = 0

do {
    $cycleCount++
    $startTime = Get-Date
    
    Log "INFO" "========== Cycle $cycleCount ($(Get-Date -Format 'HH:mm:ss')) =========="
    
    # 중복 실행 방지
    if (Check-Lock) {
        Log "WARN" "⚠ Skipping cycle (lock exists)"
        Wait-ForNextCycle
        continue
    }
    
    # 내부 잠금 설정
    Set-Lock
    
    # 자동 개발 실행
    try {
        $success = Run-AutoDev
        
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        if ($success) {
            Log "SUCCESS" "✓ Cycle completed in ${elapsed}s"
        } else {
            Log "WARN" "⚠ Cycle had issues (${elapsed}s)"
        }
    } finally {
        Release-Lock
    }
    
    if ($once) {
        Log "INFO" "One-time execution mode, exiting..."
        break
    }
    
    Wait-ForNextCycle
    
} while ($true)

Log "END" "Daemon stopped gracefully"
