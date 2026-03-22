# EduLink Docker 배포 가이드

## 개요

이 docker-compose 설정은 EduLink 애플리케이션을 완전한 프로덕션 환경으로 배포합니다.

**포함된 서비스:**
- **nginx**: Nginx 리버스 프록시 + HTTPS 종료 (포트 80, 443)
- **backend**: Flask 애플리케이션 (내부 포트 5000)
- **db**: PostgreSQL 13 데이터베이스 (포트 5432)
- **redis**: Redis 캐시 (포트 6379)

## 빠른 시작

### 1. 환경 설정
```bash
cd docker
cp .env.example .env
# .env 파일을 편집하여 실제 값 설정
nano .env
```

### 2. 서비스 시작
```bash
docker-compose up -d
```

모든 서비스가 실행 중인지 확인:
```bash
docker-compose ps
```

### 3. 헬스 체크
```bash
# Flask 백엔드 헬스 확인
curl http://localhost:5000/health

# PostgreSQL 접근
psql -h localhost -U edulink_user -d edulink_db

# Redis 접근
redis-cli -p 6379
```

## 환경 변수 상세 설명

| 변수 | 설명 | 기본값 | 예제 |
|------|------|--------|------|
| `FLASK_ENV` | Flask 실행 환경 | development | production |
| `SECRET_KEY` | 세션 및 토큰용 비밀키 | super-secret-key-... | 안전한 임의의 문자열 |
| `EXPOSE_RESET_TOKEN_IN_RESPONSE` | 비밀번호 리셋 토큰 응답 노출 | false | true (디버그만) |
| `POSTGRES_DB` | 데이터베이스 이름 | edulink_db | 변경 가능 |
| `POSTGRES_USER` | 데이터베이스 사용자 | edulink_user | 변경 가능 |
| `POSTGRES_PASSWORD` | 데이터베이스 암호 | change-in-production | 강한 암호 설정 |

## 유용한 명령어

### 서비스 재시작
```bash
docker-compose restart
```

### 로그 확인
```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 서비스만
docker-compose logs -f backend
docker-compose logs -f db
```

### 서비스 중지
```bash
docker-compose down
```

### 데이터 삭제 (경고: 취소 불가)
```bash
docker-compose down -v
```

## 보안 주의사항

⚠️ **프로덕션 배포 시:**

1. `SECRET_KEY`를 강력한 임의 문자열로 변경
2. `POSTGRES_PASSWORD`를 강력한 암호로 변경
3. `EXPOSE_RESET_TOKEN_IN_RESPONSE=false` 유지 (로그 마스킹 활성화)
4. 포트 범위 제한 또는 방화벽 설정
5. HTTPS/TLS 설정 (nginx 리버스 프록시 추천)
6. 정기적인 데이터베이스 백업

## 트러블슈팅

### 포트 이미 사용 중
```bash
# 포트 충돌 확인
lsof -i :5000
lsof -i :5432
lsof -i :6379

# docker-compose.yml에서 포트 번호 변경
```

### 데이터베이스 연결 실패
```bash
# db 서비스가 준비되었는지 확인
docker-compose logs db

# 데이터베이스 컨테이너 재시작
docker-compose restart db
```

### 백엔드 시작 실패
```bash
# 백엔드 로그 확인
docker-compose logs backend

# 필요시 컨테이너 재빌드
docker-compose up --build backend
```

## 프로덕션 배포 체크리스트

- [ ] `.env` 파일에 안전한 비밀번호 설정
- [ ] `FLASK_ENV=production` 확인
- [ ] `EXPOSE_RESET_TOKEN_IN_RESPONSE=false` 확인
- [ ] 헬스 체크 엔드포인트 검증
- [ ] 데이터베이스 백업 수동 실행
- [ ] 로그 마스킹 확인 (`mask_token` 함수)
- [ ] 방화벽 및 포트 제한 설정
- [ ] SSL/TLS 인증서 설정
- [ ] 모니터링 서비스 통합

## 추가 정보

- Flask 앱: [backend/Dockerfile](../backend/Dockerfile)
- 환경 변수: [.env.example](.env.example)
- 메인 애플리케이션: [backend/app.py](../backend/app.py)
