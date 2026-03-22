# EduLink API 스펙 (OpenAPI 3.0 형식)

**기본 정보**
- Base URL: `http://localhost:8000`
- 인증: Bearer Token (JWT)
- Content-Type: `application/json`

---

## 인증 (Auth)

### POST /auth/register
사용자 등록

**요청:**
```json
{
  "email": "user@example.com",
  "password": "Pass1234",
  "role": "instructor|student|admin"
}
```

**응답:** 201
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "instructor",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**실패:** 400 (invalid password), 409 (이미 존재)

---

### POST /auth/login
사용자 로그인

**요청:**
```json
{
  "email": "user@example.com",
  "password": "Pass1234"
}
```

**응답:** 200
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**실패:** 401 (인증 실패)

---

### GET /auth/me
현재 사용자 정보

**요청 헤더:**
```
Authorization: Bearer <token>
```

**응답:** 200
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "instructor"
}
```

**실패:** 401 (토큰 없음 또는 유효하지 않음)

---

### POST /auth/password/change
비밀번호 변경 (인증 필요)

**요청:**
```json
{
  "current_password": "Pass1234",
  "new_password": "NewPass5678"
}
```

**응답:** 200
```json
{
  "message": "Password updated successfully"
}
```

**실패:** 400 (현재 비밀번호 불일치)

---

### POST /auth/password/reset/request
비밀번호 초기화 요청

**요청:**
```json
{
  "email": "user@example.com"
}
```

**응답:** 200
```json
{
  "delivery": "mock-log",
  "message": "Reset token sent (check logs in mock mode)"
}
```

---

### POST /auth/password/reset/confirm
비밀번호 초기화 확인

**요청:**
```json
{
  "token": "<reset_token>",
  "new_password": "NewPass1234"
}
```

**응답:** 200
```json
{
  "message": "Password reset successfully"
}
```

---

## 공고 (Postings)

### GET /postings
공고 목록 조회

**쿼리 파라미터:**
- `subject` (optional): 과목 필터
- `region` (optional): 지역 필터
- `min_rate` (optional): 최소 시급
- `status` (optional): recruiting, closed, filled
- `q` (optional): 검색 키워드

**응답:** 200
```json
[
  {
    "id": 1,
    "title": "중1 수학 과외",
    "subject": "math",
    "region": "Seoul",
    "rate": 50000,
    "status": "recruiting",
    "created_at": "2026-03-22T10:00:00+00:00",
    "owner_id": 2,
    "applicant_count": 3
  }
]
```

---

### POST /postings
새 공고 생성 (instructor만)

**요청 헤더:**
```
Authorization: Bearer <token>
```

**요청:**
```json
{
  "title": "중1 수학 과외",
  "subject": "math",
  "region": "Seoul",
  "rate": 50000
}
```

**응답:** 201
```json
{
  "id": 1,
  "title": "중1 수학 과외",
  "subject": "math",
  "region": "Seoul",
  "rate": 50000,
  "status": "recruiting",
  "created_at": "2026-03-22T10:00:00+00:00"
}
```

**실패:** 403 (학생은 생성 불가)

---

### GET /postings/<posting_id>
공고 상세 조회

**응답:** 200
```json
{
  "id": 1,
  "title": "중1 수학 과외",
  "subject": "math",
  "region": "Seoul",
  "rate": 50000,
  "status": "recruiting",
  "created_at": "2026-03-22T10:00:00+00:00",
  "owner": {
    "id": 2,
    "email": "instructor@example.com"
  }
}
```

---

### PUT /postings/<posting_id>
공고 수정 (소유자만)

**요청:**
```json
{
  "title": "중1 수학 과외 (심화반)",
  "rate": 55000
}
```

**응답:** 200
```json
{
  "id": 1,
  "title": "중1 수학 과외 (심화반)",
  "rate": 55000,
  "updated_at": "2026-03-22T11:00:00+00:00"
}
```

**실패:** 403 (소유자 아님)

---

### DELETE /postings/<posting_id>
공고 삭제 (소유자만)

**응답:** 200
```json
{
  "message": "Posting deleted"
}
```

---

## 지원 (Applications)

### POST /applications
지원 신청 (student만)

**요청:**
```json
{
  "posting_id": 1
}
```

**응답:** 201
```json
{
  "id": 1,
  "posting_id": 1,
  "student_id": 3,
  "status": "pending",
  "created_at": "2026-03-22T10:00:00+00:00"
}
```

**실패:** 409 (중복 지원), 403 (강사는 지원 불가)

---

### GET /applications
지원 목록 조회

**쿼리 파라미터:**
- `status`: pending, approved, rejected
- `q`: 검색 키워드 (제목, 이메일, 학생ID)
- `sort`: newest, oldest, status (상태 우선)

**응답:** 200
```json
[
  {
    "id": 1,
    "posting_id": 1,
    "posting_title": "중1 수학 과외",
    "student_id": 3,
    "student_email": "student@example.com",
    "status": "pending",
    "created_at": "2026-03-22T10:00:00+00:00"
  }
]
```

**권한:**
- `student`: 자신의 지원만 조회
- `instructor`: 자신의 공고에 지원된 것만 조회
- `admin`: 전체 조회

---

### PATCH /applications/<application_id>
지원 상태 변경 (instructor만)

**요청:**
```json
{
  "status": "approved|rejected"
}
```

**응답:** 200
```json
{
  "id": 1,
  "status": "approved",
  "updated_at": "2026-03-22T11:00:00+00:00"
}
```

---

### DELETE /applications/<application_id>
지원 취소 (학생, pending 상태만)

**응답:** 200
```json
{
  "message": "Application cancelled"
}
```

**실패:** 403 (승인된 것은 취소 불가)

---

## 지원자 요약 (Applicants)

### GET /applications/applicants/<student_id>/summary
특정 학생의 지원 요약 (instructor only)

**응답:** 200
```json
{
  "student_id": 3,
  "student_email": "student@example.com",
  "summary": {
    "all": 5,
    "pending": 2,
    "approved": 2,
    "rejected": 1
  },
  "recent": [
    {
      "id": 1,
      "posting_id": 1,
      "posting_title": "중1 수학 과외",
      "status": "pending",
      "created_at": "2026-03-22T10:00:00+00:00"
    }
  ]
}
```

---

## 대시보드 (Dashboard)

### GET /dashboard/stats
대시보드 통계 (역할별 다름)

**응답 (Instructor):** 200
```json
{
  "role": "instructor",
  "postings_count": 5,
  "applications_count": 12,
  "approved_count": 8,
  "rejected_count": 2
}
```

**응답 (Student):** 200
```json
{
  "role": "student",
  "applied_count": 5,
  "approved_count": 2,
  "pending_count": 2
}
```

---

### GET /dashboard/activity
최근 활동 조회

**쿼리 파라미터:**
- `period`: today, 7d, 30d (기본값: today)

**응답:** 200
```json
[
  {
    "id": 1,
    "type": "posting|application|approval|rejection",
    "description": "중1 수학 과외 지원됨",
    "timestamp": "2026-03-22T10:00:00+00:00"
  }
]
```

---

## 세무 (Tax)

### POST /api/tax/onboard
세무 정보 온보딩

**요청:**
```json
{
  "business_registration_number": "123-45-67890",
  "organization_name": "EduLink Tutor"
}
```

**응답:** 201
```json
{
  "submission_id": "tax-001",
  "status": "pending_review"
}
```

---

### GET /api/tax/estimate
환급금 예상액 조회

**쿼리 파라미터:**
- `year`: YYYY (기본값: 현재 연도)

**응답:** 200
```json
{
  "year": 2026,
  "estimated_refund": 500000,
  "status": "mock",
  "currency": "KRW"
}
```

---

### POST /api/tax/submit
정산 제출

**요청:**
```json
{
  "year": 2026
}
```

**응답:** 201
```json
{
  "submission_id": "tax-submission-001",
  "status": "submitted"
}
```

---

### GET /api/tax/status/<submission_id>
정산 상태 조회

**응답:** 200
```json
{
  "submission_id": "tax-submission-001",
  "status": "approved|pending|rejected",
  "amount": 500000
}
```

---

### GET /api/tax/report/<year>
연도별 정산 보고서

**응답:** 200
```json
{
  "year": 2026,
  "total_income": 5000000,
  "withheld_tax": 165000,
  "net_income": 4835000,
  "report_url": "https://..."
}
```

---

## 네트워크 (Network / MLM)

### POST /api/network/link
후원 관계 생성

**요청:**
```json
{
  "sponsor_email": "sponsor@example.com"
}
```

**응답:** 201
```json
{
  "relationship_id": "link-001",
  "status": "pending_confirmation"
}
```

---

### POST /api/network/sales
판매 실적 기록

**요청:**
```json
{
  "base_price": 1000000,
  "pv": 100000,
  "bv": 1000000
}
```

**응답:** 201
```json
{
  "sale_id": "sale-001",
  "pv": 100000,
  "bonuses_calculated": {
    "direct_bonus": 50000,
    "sponsor_bonus": 25000
  }
}
```

---

## 관리자 (Admin)

### GET /api/network/admin/summary
관리자 대시보드 요약 (admin/super_admin only)

**쿼리 파라미터:**
- `period`: YYYY-MM (기본값: 현재 월)

**응답:** 200
```json
{
  "period": "2026-03",
  "total_sales": 50000000,
  "total_pv": 5000000,
  "total_bonuses_paid": 1750000,
  "compliance_ratio": 0.35
}
```

---

### GET /api/network/admin/rules
보상 규칙 조회

**응답:** 200
```json
{
  "levels": [
    {
      "level": 1,
      "min_pv": 200000,
      "bonus_ratio": 0.03
    },
    {
      "level": 2,
      "min_pv": 5000000,
      "bonus_ratio": 0.06
    }
  ]
}
```

---

### PUT /api/network/admin/rules
보상 규칙 수정

**요청:**
```json
{
  "levels": [
    {
      "level": 1,
      "min_pv": 200000,
      "bonus_ratio": 0.03
    }
  ]
}
```

**응답:** 200
```json
{
  "message": "Rules updated"
}
```

---

## 상태 코드

| 코드 | 의미 |
|------|------|
| 200 | OK (요청 성공) |
| 201 | Created (생성됨) |
| 400 | Bad Request (요청 오류) |
| 401 | Unauthorized (인증 필요) |
| 403 | Forbidden (권한 없음) |
| 404 | Not Found (찾을 수 없음) |
| 409 | Conflict (중복/충돌) |
| 500 | Internal Server Error (서버 오류) |

---

## 오류 응답

모든 오류는 다음 형식:
```json
{
  "error": "에러 메시지",
  "code": "error_code"
}
```

예:
```json
{
  "error": "Password must include at least one number",
  "code": "invalid_password"
}
```

---

**마지막 업데이트:** 2026-03-22  
**API 버전:** 1.0-MVP
