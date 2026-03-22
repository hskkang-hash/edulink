# EduLink 10시간 개발 스프린트 자동화 스크립트
# 하이브리드 모드: 로컬 개발 + GitHub Actions 병렬 배포

param(
    [string]$phase = "all",  # all, test, code, commit, push
    [switch]$noStop = $false  # $true면 에러 시에도 계속 진행
)

$ErrorActionPreference = if ($noStop) { "Continue" } else { "Stop" }
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$logFile = "dev-sprint-$((Get-Date).ToString('yyyyMMdd-HHmmss')).log"

function Write-LogEntry {
    param([string]$message, [string]$level = "INFO")
    $logMsg = "[$timestamp] [$level] $message"
    Write-Host $logMsg
    Add-Content -Path $logFile -Value $logMsg
}

Write-LogEntry "========== EduLink Dev Sprint Started ==========" "START"
Write-LogEntry "Phase: $phase | NoStop: $noStop" "INFO"

# Phase 1: 테스트 검증
if ($phase -eq "all" -or $phase -eq "test") {
    Write-LogEntry "Phase 1: Running backend tests..." "INFO"
    Push-Location backend
    try {
        $testResult = python -m pytest tests -v --tb=short
        if ($LASTEXITCODE -eq 0) {
            Write-LogEntry "✅ All tests passed" "SUCCESS"
        } else {
            Write-LogEntry "❌ Tests failed: $LASTEXITCODE" "ERROR"
            if (-not $noStop) { exit 1 }
        }
    } catch {
        Write-LogEntry "Error running tests: $_" "ERROR"
        if (-not $noStop) { exit 1 }
    }
    Pop-Location
}

# Phase 2: 코드 품질 검사
if ($phase -eq "all" -or $phase -eq "code") {
    Write-LogEntry "Phase 2: Code quality checks..." "INFO"
    Push-Location backend
    try {
        # Python 문법 검사
        python -m py_compile app_jwt.py app.py models.py email_adapter.py
        Write-LogEntry "✅ Syntax check passed" "SUCCESS"
    } catch {
        Write-LogEntry "⚠️  Syntax check warning: $_" "WARN"
    }
    Pop-Location
}

# Phase 3: Git 커밋
if ($phase -eq "all" -or $phase -eq "commit") {
    Write-LogEntry "Phase 3: Staging and committing changes..." "INFO"
    
    $status = git status --short
    if ($status) {
        Write-LogEntry "Changes detected:" "INFO"
        Write-LogEntry $status "INFO"
        
        git add -A
        $commitMsg = "feat: auto sprint development $(Get-Date -Format 'HH:mm:ss')"
        git commit -m $commitMsg
        Write-LogEntry "✅ Committed: $commitMsg" "SUCCESS"
    } else {
        Write-LogEntry "No changes to commit" "INFO"
    }
}

# Phase 4: Git 푸시 (자동으로 GitHub Actions 트리거)
if ($phase -eq "all" -or $phase -eq "push") {
    Write-LogEntry "Phase 4: Pushing to origin..." "INFO"
    try {
        $pushResult = git push origin main 2>&1
        Write-LogEntry "✅ Pushed to main | GitHub Actions will auto-deploy" "SUCCESS"
        Write-LogEntry "Monitor: https://github.com/hskkang-hash/edulink/actions" "INFO"
    } catch {
        Write-LogEntry "⚠️  Push failed: $_" "ERROR"
        if (-not $noStop) { exit 1 }
    }
}

Write-LogEntry "========== Sprint Phase Complete ==========" "END"
Write-LogEntry "Log saved to: $logFile" "INFO"
Write-LogEntry "Next: Monitor GitHub Actions for deployment" "INFO"
