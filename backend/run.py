#!/usr/bin/env python
"""
EduLink Flask Application - Single Entrypoint
메인 실행 파일: app_jwt.py의 래퍼 및 실행 포인트
"""
import sys
import os
from pathlib import Path

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

# app_jwt가 메인 구현
from app_jwt import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"🚀 Starting EduLink on http://localhost:{port}")
    print(f"📝 API Docs: http://localhost:{port}/docs (if Swagger available)")
    print(f"🏥 Health Check: http://localhost:{port}/health")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        reload=debug,
        use_reloader=debug
    )
