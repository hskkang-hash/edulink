# SendGrid 이메일 통합 가이드

## 개요

EduLink는 이제 SendGrid를 통해 실제 이메일로 비밀번호 리셋 토큰과 알림을 전송할 수 있습니다.

**두 가지 모드:**
1. **Mock 모드** (기본값) - 서버 로그에 토큰 출력
2. **SendGrid 모드** - 실제 이메일 전송

---

## SendGrid 설정

### Step 1: SendGrid 계정 생성

1. [SendGrid.com](https://sendgrid.com) 방문
2. 계정 생성 및 이메일 확인
3. API 키 생성:
   - Settings → API Keys
   - "Create API Key" 클릭
   - "Full Access" 선택
   - 키 복사 후 안전하게 저장

### Step 2: 라이브러리 설치

```bash
pip install sendgrid==6.11.0
```

또는 requirements.txt가 이미 업데이트됨:
```bash
pip install -r requirements.txt
```

### Step 3: 환경 변수 설정

`.env` 파일 또는 docker/.env 파일:
```bash
EMAIL_ADAPTER_TYPE=sendgrid
SENDGRID_API_KEY=your_actual_sendgrid_api_key_here
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
```

**주의:** API 키를 버전 관리에 커밋하지 마십시오!

### Step 4: 발신자 이메일 검증

SendGrid에서 발신자 이메일을 검증해야 합니다:

1. SendGrid 대시보드 → Settings → Sender Authentication
2. 도메인 또는 단일 발신자 검증 완료
3. 검증된 이메일이 `SENDGRID_FROM_EMAIL`과 일치하는지 확인

---

## 로컬 테스트 (Mock 모드)

```bash
export EMAIL_ADAPTER_TYPE=mock
python app.py
```

서버 로그에서 토큰 확인:
```
MOCK_PASSWORD_RESET_TOKEN: user_id=1 email=user@example.com token=...
```

---

## SendGrid 모드 테스트

### 1. 환경 변수 설정
```bash
export EMAIL_ADAPTER_TYPE=sendgrid
export SENDGRID_API_KEY=SG.xxxxx...
export SENDGRID_FROM_EMAIL=noreply@yourcompany.com
```

### 2. Flask 앱 시작
```bash
python app.py
```

### 3. API 호출 (비밀번호 리셋 요청)
```bash
curl -X POST http://localhost:5000/auth/password/reset/request \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

### 4. 응답 확인

성공 응답:
```json
{
  "message": "If the account exists, reset instructions have been generated",
  "delivery": "mock-log"
}
```

SendGrid 로그 확인:
```
SENDGRID_PASSWORD_RESET_SUCCESS: user_id=1 recipient=test@example.com delivery_id=sendgrid-1-...
```

---

## Docker 환경에서 SendGrid 사용

### docker/.env 파일 수정
```bash
EMAIL_ADAPTER_TYPE=sendgrid
SENDGRID_API_KEY=${SENDGRID_API_KEY}
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
```

### 컨테이너 환경 변수 전달
```bash
docker-compose up --env-file=.env
```

또는 .env 파일 직접 설정:
```bash
cd docker
cat .env | grep SENDGRID
docker-compose up
```

---

## 트러블슈팅

### "SENDGRID_API_KEY not set"
- `.env` 파일에 키 설정 확인
- Docker 실행 시 `--env-file` 옵션 확인
- 환경 변수 목록: `env | grep SENDGRID`

### "sendgrid library not installed"
```bash
pip install sendgrid
```

### "401 Unauthorized"
- API 키가 올바른지 확인
- SendGrid 대시보드에서 키 상태 확인
- 새 키로 다시 시도

### "Invalid email address for"
- 발신자 이메일이 SendGrid에서 검증되었는지 확인
- 오타 확인
- 도메인 기반 검증 사용 권장

### "429 Too Many Requests"
- SendGrid API 속도 제한 도달
- 재시도 대기
- 계정 업그레이드 고려

---

## 프로덕션 체크리스트

- [ ] SendGrid 계정 생성
- [ ] API 키 생성 및 안전하게 저장
- [ ] 발신자 이메일 검증
- [ ] `SENDGRID_API_KEY` 환경 변수 설정
- [ ] `SENDGRID_FROM_EMAIL` 환경 변수 설정  
- [ ] `EMAIL_ADAPTER_TYPE=sendgrid` 설정
- [ ] 모든 이메일(비밀번호 리셋, 알림) 테스트
- [ ] 로그 모니터링 설정
- [ ] 메일 실패 알람 설정

---

## 이메일 템플릿 커스터마이징

[backend/email_adapter.py](../backend/email_adapter.py)에서 `SendGridEmailAdapter` 클래스의 `html_content` 변수를 수정하여 이메일 템플릿을 변경할 수 있습니다.

### 비밀번호 리셋 템플릿
라인 약 215-250: `send_password_reset_token` 메서드의 `html_content`

### 일반 알림 템플릿
라인 약 290-315: `send_notification` 메서드의 `html_content`

---

## 비용 관점

SendGrid 가격:
- **Free:** 월 100개 이메일 (영구)
- **Pro:** 월 $29.95부터 (무제한 이메일)

[SendGrid 가격](https://sendgrid.com/pricing)

---

## 보안 팁

1. **API 키 관리**
   - 프로덕션 환경에서는 별도의 강력한 키 사용
   - 정기적인 키 로테이션
   - 키 권한 최소화 (이메일 전송만)

2. **토큰 로깅**
   - 프로덕션에서는 `mask_token()` 함수로 자동 마스킹됨
   - 전체 토큰은 SendGrid에만 전송

3. **로깅 감시**
   - SendGrid 이메일 델리버리 상태 모니터링
   - 실패율 추적
   - 이상 탐지 알람

---

## 다음 단계

- AWS SES 어댑터 추가
- Mailgun 어댑터 추가
- 이메일 수신 확인 처리
- 배치 이메일 전송

---

## 참고 자료

- [SendGrid API 문서](https://docs.sendgrid.com)
- [SendGrid Python 라이브러리](https://github.com/sendgrid/sendgrid-python)
- [Email Best Practices](https://sendgrid.com/blog/what-is-an-email-api/)
