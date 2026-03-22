#!/bin/bash
# Docker entrypoint script
# Runs database migrations before starting the Flask application

set -e

echo "Starting EduLink Backend with Database Migrations..."

# 데이터베이스 마이그레이션 실행
echo "Running database migrations..."
flask db upgrade

# Flask 애플리케이션 시작
echo "Starting Flask application..."
exec gunicorn --bind 0.0.0.0:5000 --timeout 120 --access-logfile - --error-logfile - app_jwt:app
