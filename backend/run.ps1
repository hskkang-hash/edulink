#!/usr/bin/env pwsh
# EduLink Flask Application Runner
# PowerShell 실행 스크립트

param(
    [string]$env = "development",  # development, staging, production
    [int]$port = 8000,
    [switch]$debug = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 EduLink Backend Startup" -ForegroundColor Cyan
Write-Host "Environment: $env" -ForegroundColor Yellow
Write-Host "Port: $port" -ForegroundColor Yellow
Write-Host "Debug: $debug" -ForegroundColor Yellow

# 환경 변수 설정
$env:PORT = $port
$env:DEBUG = if ($debug) { "true" } else { "false" }

# 의존성 확인
Write-Host "`n📦 Checking dependencies..." -ForegroundColor Cyan
python -m pip show flask > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing requirements..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
}

# 데이터베이스 초기화
Write-Host "`n🗄️  Initializing database..." -ForegroundColor Cyan
if (Test-Path "edulink.db") {
    Write-Host "Database exists: edulink.db" -ForegroundColor Green
} else {
    Write-Host "Creating new database..." -ForegroundColor Yellow
}

# Flask 앱 실행
Write-Host "`n✨ Starting Flask application..." -ForegroundColor Green
Write-Host "API available at: http://localhost:$port" -ForegroundColor Green
Write-Host "Health check: http://localhost:$port/health" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Yellow

python run.py
