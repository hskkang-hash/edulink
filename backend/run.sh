#!/bin/bash
# EduLink Flask Application Runner
# Bash 실행 스크립트

ENV=${1:-development}
PORT=${2:-8000}
DEBUG=${3:-false}

echo "🚀 EduLink Backend Startup"
echo "Environment: $ENV"
echo "Port: $PORT"
echo "Debug: $DEBUG"

# 환경 변수 설정
export PORT=$PORT
export DEBUG=$DEBUG

# 의존성 확인
echo ""
echo "📦 Checking dependencies..."
python -m pip show flask > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Installing requirements..."
    python -m pip install -r requirements.txt
fi

# 데이터베이스 초기화
echo ""
echo "🗄️  Initializing database..."
if [ -f "edulink.db" ]; then
    echo "Database exists: edulink.db"
else
    echo "Creating new database..."
fi

# Flask 앱 실행
echo ""
echo "✨ Starting Flask application..."
echo "API available at: http://localhost:$PORT"
echo "Health check: http://localhost:$PORT/health"
echo "Press Ctrl+C to stop"
echo ""

python run.py
