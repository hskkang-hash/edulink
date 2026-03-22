# EDULINK 기능 요구사항 상세 명세

**Version:** 1.0  
**Date:** March 2026  
**Status:** MVP Functions Specification

---

## 1. 강사 모바일 앱 기능 (Mobile-First)

### 1.1 인증 & 프로필

#### `/auth/login` — 로그인
**용도:** 강사 앱 진입

**API 엔드포인트:**
- `POST /api/auth/login` - 로그인
- `POST /api/auth/logout` - 로그아웃
- `POST /api/auth/refresh` - 토큰 갱신

**기능:**
```
입력:
├── 카카오톡 간편 인증 (OAuth2)
├── 휴대폰번호 + OTP
└── 생체 인증 (지문/안면)

출력:
├── JWT Access Token (1시간 만료)
├── Refresh Token (7일만료)
└── 사용자 기본정보
```

**DB 쿼리:**
```sql
SELECT users.*, fastapi_users.* 
FROM users
WHERE phone_number = ? AND is_active = true;
```

**캐시:**
- Redis: `session:{sessionId}` → 사용자 정보 (30분)

**보안:**
- HTTPS TLS 1.3
- Rate Limiting: 5회/분
- OTP 검증: 유효시간 5분

---

#### `/instructor/profile/onboarding` — 온보딩
**용도:** 강사 프로필 완성

**필수 정보 입력:**
```
1단계: 기본정보
├── 이름
├── 생년월일
└── 휴대폰번호

2단계: 교육정보
├── 과목 (복수 선택)
│   ├── 국어, 수학, 영어
│   ├── 과학, 사회, 기술
│   └── 예술, 음악, 체육
├── 교육 수준 (복수 선택)
│   ├── 초등, 중학, 고등
│   ├── 대학, 성인
│   └── 기타
├── 지역 (복수 선택)
│   ├── 서울/경기/인천
│   ├── 영남권, 호남권, 충청권
│   └── 강원, 제주
└── 수업 가능 시간
    ├── 요일별 선택 (월~일)
    └── 시간대 설정 (예: 18:00-21:00)

3단계: 세무정보
├── 사업자등록증 OR 소득 신고서류
├── 3.3% 원천징수 동의서
└── 계좌번호 (정산 수령)

4단계: 신원 확인
├── 신분증 사진 (필수)
├── 자격증 사진 (선택)
└── 아동학대/성범죄 조회 동의 (필수)
```

**API 엔드포인트:**
- `POST /api/instructors/profile` - 프로필 저장
- `POST /api/instructors/documents/upload` - 서류 업로드
- `GET /api/instructors/profile/{id}` - 프로필 조회

**데이터베이스:**
```sql
INSERT INTO instructors (
  user_id, subjects, regions, availability_hours,
  business_registration, tax_consent, bank_account, 
  background_check_consent, status
) VALUES (...);

-- status: pending → reviewing → approved OR rejected
```

**파일 저장소:** S3 / Minio
```
instructors/{instructorId}/
├── business_registration.pdf
├── background_check_consent.pdf
├── id_card.jpg
└── certificate.jpg
```

**상태 관리:**
- "제출 대기중" → 관리자 검수 (24~48시간)
- "규정조회중" → 범죄경력 조회 API 호출 중
- "승인됨" → 매칭 가능
- "반려됨" → 관리자 메모와 함께 수정 요청

---

### 1.2 매칭 & 공고

#### `/instructor/postings` — 공고 조회 & 지원
**용도:** 수업 기회 발굴

**API 엔드포인트:**
- `GET /api/postings?subject=math&region=gangnam&min_rate=30000` - 필터된 공고조회
- `GET /api/postings/{id}` - 공고 상세
- `POST /api/applications/{postingId}` - 지원
- `GET /api/instructor/applications` - 내 지원 현황

**필터 기능:**
```
Query Parameters:
├── subject: string (과목)
├── region: string (지역)
├── min_rate: number (최저 시급)
├── type: enum (온라인/오프라인)
├── status: enum (모집중/마감)
├── sort_by: enum (최신/인기/급여높음)
└── page: number (페이지네이션)
```

**응답 데이터:**
```json
{
  "postings": [
    {
      "id": "posting_001",
      "organizationName": "강남중학교",
      "title": "중1 수학 과외",
      "subject": "math",
      "level": "middle",
      "region": "gangnam",
      "address": "서울시 강남구 테헤란로",
      "type": "offline",
      "duration": "weekly",
      "hours": ["weekday", "18:00-19:00"],
      "rate": 40000,
      "requiredQualifications": [],
      "preferredQualifications": ["수학교육학"],
      "organizationRating": 4.8,
      "organizationReviewCount": 215,
      "status": "recruiting",
      "appliedCount": 3,
      "createdAt": "2026-03-22",
      "expiresAt": "2026-03-29"
    }
  ],
  "total": 245,
  "page": 1,
  "pageSize": 20
}
```

**지원 로직:**
```
1. 사용자 클릭 "지원하기"
   ↓
2. 조건 확인 (프로필 완성 여부, 과목/지역 매칭)
   ↓
3. 지원 신청 생성 (status: pending)
   ├── DB: INSERT into applications
   ├── Cache: 지원 내역 Redis 저장
   └── Event: 기관에 알림 발송
   ↓
4. 기관의 선택 대기
   ├── 기간: 7일
   └── 상태: pending → selected OR rejected
   ↓
5. 선택 결과 강사에게 알림 (푸시 + 인앱)
```

**DB 스키마:**
```sql
CREATE TABLE postings (
  id VARCHAR PRIMARY KEY,
  organization_id UUID REFERENCES organizations(id),
  subject VARCHAR,
  level ENUM,
  region VARCHAR,
  address TEXT,
  type ENUM ('online', 'offline'),
  rate DECIMAL(10, 2),
  status ENUM ('recruiting', 'closed', 'filled'),
  created_at TIMESTAMP,
  expires_at TIMESTAMP,
  created_by UUID REFERENCES users(id)
);

CREATE TABLE applications (
  id VARCHAR PRIMARY KEY,
  posting_id VARCHAR REFERENCES postings(id),
  instructor_id UUID REFERENCES instructors(user_id),
  status ENUM ('pending', 'selected', 'rejected'),
  applied_at TIMESTAMP,
  responded_at TIMESTAMP,
  response_reason TEXT -- 거절 사유
);
```

---

### 1.3 수업 관리

#### `/instructor/sessions/{id}` — 수업 출석 & 일지
**용도:** 수업 실행 및 기록

**API 엔드포인트:**
- `GET /api/sessions/upcoming` - 예정된 수업
- `POST /api/sessions/{id}/checkin` - GPS 체크인
- `POST /api/sessions/{id}/complete` - 수업 완료
- `GET /api/sessions/{id}/log` - 수업 일지 조회

**GPS 체크인:**
```
Request:
{
  "sessionId": "session_001",
  "latitude": 37.4979,
  "longitude": 127.0276,
  "timestamp": "2026-03-24T18:00:00Z"
}

검증:
├── GPS 좌표가 설정된 위치에서 1km 내인지 확인
├── 체크인 시간이 수업 시작 30분 이내인지 확인
└── 이미 체크인되지 않았는지 확인

Response:
{
  "sessionId": "session_001",
  "checkInTime": "2026-03-24T17:55:00Z",
  "actualLocation": {
    "distance": 0.2,  // km
    "valid": true
  },
  "status": "checked_in"
}
```

**수업 완료:**
```
사용자 입력:
├── 실제 강의 시간 (자동 기반값: 예정시간)
├── 학습 내용 요약 (텍스트)
├── 다음 수업 과제 (선택사항)
├── 학생 태도 평가 (⭐1-5)
└── 기타 메모 (선택사항)

저장 처리:
├── DB: INSERT session_logs
├── 정산 자동 계산 (시간 × 시급)
├── Cache: 정산액 일시 저장
├── Event: 정산 이벤트 발행
└── Celery: 월말 정산 배치 예약
```

**DB 스키마:**
```sql
CREATE TABLE sessions (
  id VARCHAR PRIMARY KEY,
  application_id VARCHAR REFERENCES applications(id),
  instructor_id UUID,
  organization_id UUID,
  scheduled_start TIMESTAMP,
  scheduled_end TIMESTAMP,
  actual_start TIMESTAMP,
  actual_end TIMESTAMP,
  location_type ENUM ('online', 'offline'),
  location_address TEXT,
  online_link VARCHAR,
  status ENUM ('pending', 'in_progress', 'completed', 'cancelled'),
  gps_checkin JSONB (latitude, longitude, distance),
  created_at TIMESTAMP
);

CREATE TABLE session_logs (
  id VARCHAR PRIMARY KEY,
  session_id VARCHAR REFERENCES sessions(id),
  learning_summary TEXT,
  next_assignment TEXT,
  student_attitude_rating INT,
  notes TEXT,
  actual_duration_minutes INT,
  logged_at TIMESTAMP
);
```

---

### 1.4 정산 & 환급

#### `/instructor/settlements` — 월별 정산 & 환급금 조회
**용도:** 수익 관리 및 세무

**탭 1: 월별 정산 현황**

**API 엔드포인트:**
- `GET /api/settlements/monthly?year=2026&month=3` - 월별 정산 조회
- `GET /api/settlements/history` - 정산 이력

**응답 데이터:**
```json
{
  "month": "2026-03",
  "summary": {
    "totalRevenue": 2500000,
    "withholding": 82500,  // 3.3%
    "netPayment": 2417500,
    "compensationBonus": 150000,  // MLM 보상
    "totalPayment": 2567500,
    "paymentDate": "2026-04-05",
    "status": "completed"  // pending, in_progress, completed
  },
  "breakdown": [
    {
      "sessionDate": "2026-03-24",
      "sessionCount": 5,
      "revenue": 200000,
      "withholding": 6600,
      "netAmount": 193400,
      "status": "settled"
    }
  ],
  "mlmBreakdown": {
    "level": "level_2",
    "directSales": 2500000,
    "downlineSales": 5000000,
    "bonusRate": 0.06,
    "bonusAmount": 150000
  }
}
```

**자동 정산 로직:**
```
매일 자정:
1. 어제자 완료된 모든 수업 조회
2. 수업료 합계 계산
3. 3.3% 원천징수 계산
4. MLM 보상 계산 (월 단위)
5. PostgreSQL 저장
6. Redis 캐시 갱신
7. 사용자 대시보드 업데이트

월말:
1. 한 달 전체 거래 조회
2. 최종 정산액 계산
3. 환급금 조회 필요 여부 판단
4. 정산 완료 기록
5. 지급 스케줄링
```

**탭 2: 환급금 조회 (무료)**

**API 엔드포인트:**
- `POST /api/tax/refund-inquiry` - 환급금 조회 (간편인증)
- `GET /api/tax/refund-inquiry/status` - 조회 상태
- `POST /api/tax/filing/deferred` - 기한 후 신고 신청

**환급금 조회 흐름:**
```
Step 1: 간편 인증
├── 카카오톡 간편인증 클릭
├── 카카오 서버에 인증 요청
└── 사용자가 인증하면 토큰 반환

Step 2: 홈택스 API 호출
├── 간편인증 토큰과 사용자 정보 함께 전송
├── 홈택스 API가 사용자의 세금 데이터 조회
└── 미수령 환급금 계산

Step 3: 결과 제시
├── 연도별 환급금 표시
│   ├── 2025년: 1,200,000원
│   ├── 2024년: 850,000원
│   └── 2023년: 620,000원
├── 총 환급금: 2,670,000원
└── 신고 시 예상 환급액 (20~25% 수수료 공제 후)

Step 4: 신고 대행 신청 (선택)
├── "신고 대행 신청" 버튼 클릭
├── 신고년도 선택
├── 후불 결제 동의
└── 신고 프로세스 시작
```

**DB 스키마:**
```sql
CREATE TABLE settlements (
  id VARCHAR PRIMARY KEY,
  instructor_id UUID REFERENCES instructors(user_id),
  settlement_month DATE,
  total_revenue DECIMAL(12, 2),
  withholding_amount DECIMAL(12, 2),
  net_payment DECIMAL(12, 2),
  mlm_bonus DECIMAL(12, 2),
  total_payment DECIMAL(12, 2),
  payment_date DATE,
  payment_method VARCHAR,
  bank_account VARCHAR,
  status ENUM ('pending', 'in_progress', 'completed', 'failed'),
  created_at TIMESTAMP
);

CREATE TABLE tax_refund_inquiries (
  id VARCHAR PRIMARY KEY,
  instructor_id UUID REFERENCES instructors(user_id),
  inquiry_date TIMESTAMP,
  hometax_token VARCHAR,  -- 간편인증 토큰
  years INT ARRAY,  -- 조회 년도
  refund_amounts DECIMAL ARRAY,  -- 연도별 환급액
  total_refund DECIMAL(12, 2),
  status ENUM ('pending', 'completed', 'error'),
  error_message TEXT
);

CREATE TABLE tax_filings (
  id VARCHAR PRIMARY KEY,
  instructor_id UUID REFERENCES instructors(user_id),
  filing_type ENUM ('regular', 'deferred'),
  filing_year INT,
  filing_date TIMESTAMP,
  submitted_to VARCHAR,  -- 'hometax' OR 'samcheomsam'
  refund_amount DECIMAL(12, 2),
  service_fee DECIMAL(12, 2),  -- 20~25%
  net_refund DECIMAL(12, 2),
  status ENUM ('submitted', 'approved', 'rejected'),
  cms_charge_date DATE,  -- 자동 출금 날짜
  created_at TIMESTAMP
);
```

---

## 2. 기관 관리자 웹 기능 (Desktop-First 반응형)

### 2.1 대시보드

#### `/org/dashboard` — 기관 KPI 대시보드
**용도:** 업무 현황 한눈에 파악

**구성 요소:**

**1) 오늘의 일정 (실시간)**
```json
{
  "type": "card",
  "title": "📅 당일 예정 수업 (3개)",
  "items": [
    {
      "time": "14:00",
      "title": "중1 수학",
      "instructor": "김강사",
      "location": "강남구 테헤란로",
      "status": "on-time",  // on-time, late, pending_checkin
      "studentCount": 5
    }
  ]
}
```

**2) KPI 타일**
```json
{
  "kpis": [
    {
      "label": "총 수업",
      "value": 47,
      "change": "+5 (월)",
      "trend": "up"
    },
    {
      "label": "강사 평점",
      "value": "4.7/5.0",
      "change": "+0.1",
      "trend": "up"
    },
    {
      "label": "이탈률",
      "value": "3.2%",
      "change": "-0.5%",
      "trend": "down"  // down is good
    },
    {
      "label": "월 정산액",
      "value": "12,500,000원",
      "change": "+2.5M (+25%)",
      "trend": "up"
    }
  ]
}
```

**3) 인기 강사 (Top 5)**
```json
{
  "instructors": [
    {
      "rank": 1,
      "name": "김강사",
      "subject": "영어",
      "rating": 4.9,
      "reviewCount": 156,
      "sessionCount": 32,
      "earnedInMonth": 1280000
    }
  ]
}
```

**API 엔드포인트:**
- `GET /api/organizations/{orgId}/dashboard` - 종합 대시보드
- `GET /api/sessions/today` - 오늘 일정
- `GET /api/instructors/top` - 인기 강사

---

### 2.2 공고 및 지원

#### `/org/postings/{id}/applications` — 지원자 관리
**용도:** 공고에 지원한 강사 검토 및 선택

**API 엔드포인트:**
- `GET /api/postings/{id}/applications` - 지원자 목록
- `POST /api/applications/{appId}/select` - 강사 선택
- `POST /api/applications/{appId}/reject` - 거절 (사유 입력)
- `POST /api/applications/{appId}/prescreen` - 사전 평가

**지원자 목록 테이블:**
```json
{
  "applications": [
    {
      "id": "app_001",
      "instructorId": "inst_001",
      "name": "김강사",
      "experience": 5,  // 년
      "rating": 4.9,
      "reviewCount": 156,
      "region": "강남",
      "availableHours": ["월", "수", "금"],
      "certificateStatus": "verified",
      "backgroundCheckStatus": "passed",
      "appliedAt": "2026-03-22T10:30:00",
      "status": "pending"
    }
  ],
  "total": 3,
  "pending": 2,
  "selected": 1
}
```

**지원자 상세 프로필 모달:**
```json
{
  "instructor": {
    "id": "inst_001",
    "name": "김강사",
    "experience": "5년",
    "rating": 4.9,
    "reviewCount": 156,
    "subjects": ["수학", "영어"],
    "regions": ["강남", "서초"],
    "availability": "월~금 18:00~21:00",
    "certificates": [
      {
        "name": "수학교육학 석사",
        "issuer": "서울대학교",
        "verifiedAt": "2026-03-15",
        "verified": true
      }
    ],
    "backgroundCheck": {
      "status": "passed",
      "checkedAt": "2026-03-15",
      "validUntil": "2027-03-15"
    },
    "recentReviews": [
      {
        "from": "학부모",
        "rating": 5,
        "comment": "매우 친절하고 효율적입니다",
        "date": "2026-03-20"
      }
    ]
  },
  "actions": [
    {
      "label": "인스턴트 계약",
      "action": "select"
    },
    {
      "label": "제안서 발송",
      "action": "send_offer"
    },
    {
      "label": "거절",
      "action": "reject"
    }
  ]
}
```

**선택 처리 로직:**
```
1. 기관이 "인스턴트 계약" 클릭
   ├── DB: applications.status = "selected"
   ├── 계약서 자동 생성
   ├── 강사에게 알림 (푸시 + 이메일)
   └── 다른 지원자에게 "거절" 알림

2. 계약서 서명 프로세스
   ├── 기관-강사 전자계약
   ├── 양쪽 모두 서명 필요
   └── 완료되면 sessions 테이블에 생성
```

---

### 2.3 수업 관리

#### `/org/sessions/{id}` — 수업 실적 및 보정
**용도:** 수업 실행 현황을 파악하고 정산액 보정

**API 엔드포인트:**
- `GET /api/sessions/{id}` - 수업 조회
- `POST /api/sessions/{id}/adjust` - 시간 보정
- `GET /api/sessions/{id}/logs` - 강사 일지 조회

**수업 상태 화면:**
```json
{
  "session": {
    "id": "session_001",
    "date": "2026-03-24",
    "instructor": "김강사",
    "subject": "중1 수학",
    "scheduled": {
      "start": "18:00",
      "end": "19:00",
      "duration": 60
    },
    "actual": {
      "checkInTime": "17:55",
      "checkOutTime": "19:02",
      "duration": 62  // minutes
    },
    "adjustments": {
      "original": 60,
      "adjusted": 62,
      "reason": "학생 요청으로 2분 연장"
    },
    "settlement": {
      "rate": 40000,  // per hour
      "calculation": "40000 × (62/60) = 41,333",
      "fee": 2066,  // 5%
      "instructorPayment": 39,266
    },
    "instructorLog": {
      "summary": "단원 1~3 완료, 과제 2개 부여",
      "nextAssignment": "연습문제 풀이",
      "studentAttitude": 5
    },
    "status": "completed"
  }
}
```

**시간 보정 로직:**
```
상황 1: 강사가 조기 출석 또는 늑장
├── GPS 체크인 시간 vs 예정 시간
└── 자동으로 조정되나, 기관에서 확인 가능

상황 2: 강사가 초과 근무
├── 학생 요청으로 수업 연장
├── 기관이 수동으로 시간 선택
└── 정산액 자동 재계산

상황 3: 결석/지각
├── 시간 0 → 정산 없음
└── 불만 처리 프로세스 시작
```

---

### 2.4 정산 관리

#### `/org/settlements` — 월별 정산
**용도:** 강사 급여 지급 및 기록 관리

**API 엔드포인트:**
- `GET /api/settlements/monthly/{month}` - 월별 정산 조회
- `POST /api/settlements/{month}/confirm` - 정산 완료 확인
- `GET /api/settlements/{month}/export` - 엑셀/CSV 내보내기

**정산 현황:**
```json
{
  "period": "2026-03",
  "summary": {
    "totalRevenue": 12500000,  // 수업료 총합
    "withholding": 412500,  // 3.3% 자동
    "instructorPayment": 12087500,
    "settlementCount": 150,  // 정산된 강사 수
    "status": "completed",  // pending, in_progress, completed
    "completedAt": "2026-04-05"
  },
  "breakdown": [
    {
      "instructor": "김강사",
      "sessionCount": 32,
      "totalAmount": 1280000,
      "withholding": 42240,
      "netPayment": 1237760,
      "paymentStatus": "completed",
      "paymentDate": "2026-04-05"
    }
  ],
  "summary_tabs": {
    "completed": {
      "count": 145,
      "totalAmount": 11987500
    },
    "pending_adjustment": {
      "count": 3,
      "reason": "시간 분쟁 - 관리자 검토 대기"
    },
    "pending_docs": {
      "count": 2,
      "reason": "강사 서류 미완료"
    }
  }
}
```

**엑셀 내보내기 기능:**
- 정산 내역 (강사명, 시간, 금액)
- 세금 계산서 (원천징수 내역)
- 지급 명세서 (지급일, 금액, 상태)

---

## 3. 에듀링크 최고 관리자 웹 기능

### 3.1 회원 관리

#### 강사 승인 관리
**용도:** 신규 강사 심사 및 승인

**상태 플로우:**
```
신청
  ↓
신원 확인 검수
  ├── 신분증 확인
  ├── 자격증 확인
  └── 서류 완성도 확인
  ↓
범죄경력조회 (정부 DB)
  ├── 아동학대 여부
  ├── 성범죄 여부
  └── 기타 범죄 기록
  ↓
관리자 승인 또는 반려
  ├── 승인: 즉시 매칭 가능
  ├── 반려: 거절 사유 전달
  └── 모류: 대기 상태 유지
```

**관리자 화면:**
```json
{
  "applicants": {
    "new": 12,
    "reviewing": 5,
    "approved": 1240,
    "rejected": 34
  },
  "applications": [
    {
      "id": "app_inst_001",
      "instructor": "김강사",
      "appliedAt": "2026-03-22",
      "subjects": ["수학", "영어"],
      "regions": ["강남", "서초"],
      "documents": {
        "idCard": "✅ 제출됨",
        "certificate": "✅ 제출됨",
        "backgroundCheckConsent": "✅ 동의함",
        "taxDocument": "✅ 제출됨"
      },
      "backgroundCheck": {
        "status": "in_progress",  // pending, in_progress, passed, failed
        "checkedAt": null,
        "result": null
      },
      "adminReview": {
        "status": "pending",
        "notes": ""
      },
      "actions": [
        { "label": "승인", "action": "approve" },
        { "label": "반려", "action": "reject" }
      ]
    }
  ]
}
```

---

### 3.2 MLM 컴플라이언스 관리

#### 35% 규제 모니터링
**용도:** 방판법 준수 확인

**대시보드:**
```json
{
  "compliance": {
    "ratio": 0.325,  // 32.5%
    "status": "safe",  // safe, warning, critical
    "threshold": 0.35,
    "totalRevenue": 50000000,  // Γ
    "totalCompensation": 16250000,  // C
    "regulatoryLimit": 17500000,  // 0.35 * Γ
    "surplus": 1250000,  // 여유분
    "warningThreshold": 0.34,  // 34%에서 경고
    "lastRecalculated": "2026-03-21",
    "nextRecalculation": "2026-03-28"
  },
  "monthlyHistory": [
    {
      "month": "2026-03",
      "ratio": 0.325,
      "status": "safe"
    },
    {
      "month": "2026-02",
      "ratio": 0.318,
      "status": "safe"
    }
  ],
  "adjustmentHistory": [
    {
      "date": "2026-03-15",
      "event": "Level 3 promotional bonus 조정",
      "previousRatio": 0.335,
      "newRatio": 0.325,
      "adjustment": -0.01,
      "reason": "상한 초과로 자동 보정"
    }
  ]
}
```

**강사 레벨별 보상:**
```json
{
  "levels": [
    {
      "level": 1,
      "minPV": 200000,
      "compensationRate": 0.03,
      "activeInstructors": 245,
      "monthlyTotal": 3200000,
      "avgBonus": 13061
    },
    {
      "level": 2,
      "minPV": 5000000,
      "compensationRate": 0.06,
      "activeInstructors": 45,
      "monthlyTotal": 6800000,
      "avgBonus": 151111
    },
    {
      "level": 3,
      "minPV": 10000000,
      "compensationRate": 0.21,
      "activeInstructors": 8,
      "monthlyTotal": 4100000,
      "avgBonus": 512500
    }
  ],
  "leadershipBonus": {
    "monthlyTotal": 2150000,
    "count": 5,
    "avgBonus": 430000
  ]
}
```

---

## 4. 교육청 대시보드 기능

### 4.1 지역 통합 모니터링

#### `/district/dashboard` — 관할 학교 통계
**용도:** 교육청이 관할 학교들의 방과후/늘봄학교 현황을 통합 모니터링

**API 엔드포인트:**
- `GET /api/districts/{districtId}/dashboard` - 통합 대시보드
- `GET /api/districts/{districtId}/schools` - 학교별 현황
- `GET /api/districts/{districtId}/budget` - 예산 현황

**통합 대시보드:**
```json
{
  "district": "전남교육청",
  "statistics": {
    "totalSchools": 245,
    "programs": 1230,
    "instructors": 890,
    "students": 12500,
    "budgetExecutionRate": 0.873,
    "satisfactionRate": 4.6,  // 만족도
    "attendanceRate": 0.932,
    "instructorSosResponseRate": 0.962,  // 2시간 내 대응률
    "paymentCompleteRate": 0.995
  },
  "alerts": [
    {
      "severity": "warning",
      "school": "강진중학교",
      "issue": "예산 초과 예상",
      "budget_used": 4350000,
      "budget_limit": 5000000,
      "remaining": 650000,
      "daysLeft": 10
    },
    {
      "severity": "info",
      "instructor": "박강사",
      "rating": 3.8,
      "issue": "강사 평점 4.0 이하 - 모니터링 권장"
    }
  ],
  "schools": [
    {
      "name": "강진중학교",
      "programs": 8,
      "expenses": {
        "budget": 5000000,
        "used": 4350000,
        "remaining": 650000
      },
      "instructors": 8,
      "satisfactionRate": 4.5,
      "sosCount": 2,
      "avgSosResponseTime": "1시간 45분"
    }
  ]
}
```

---

## 5. 백엔드 서비스 기능 (API)

### 5.1 매칭 서비스 API

#### POST /api/postings/sos
**용도:** 긴급 공고 생성

```json
Request:
{
  "organizationId": "org_001",
  "subject": "math",
  "level": "middle",
  "region": "gangnam",
  "address": "서울시 강남구 테헤란로",
  "startTime": "2026-03-24T18:00:00",
  "endTime": "2026-03-24T19:00",
  "rate": 50000,  // SOS 요금은 일반 요금보다 높을 수 있음
  "urgent": true,
  "expiresIn": 120  // 120분 유효
}

Response:
{
  "id": "sos_posting_001",
  "status": "active",
  "matchingSent": 150,  // 조건에 맞는 강사 150명에게 알림 발송
  "selectedAt": null,
  "selectedInstructor": null
}
```

**실시간 알림:**
- 조건 맞는 강사들에게 푸시 알림 (즉시)
- "당신의 지역에서 긴급 출강 요청이 왔습니다!"
- 첫 번째 수락한 강사에게 매칭

---

### 5.2 정산 서비스 API

#### POST /api/settlements/calculate
**용도:** 월말 자동 정산 배치

```json
Request:
{
  "month": "2026-03",
  "dryRun": false  // true면 실제 저장하지 않고 계산만 함
}

Response:
{
  "month": "2026-03",
  "totalInstructors": 150,
  "totalRevenue": 12500000,
  "totalWithholding": 412500,
  "totalPayment": 12087500,
  "mlmBonus": 1850000,
  "settlementBreakdown": [
    {
      "instructorId": "inst_001",
      "name": "김강사",
      "revenue": 1280000,
      "withholding": 42240,
      "netPayment": 1237760,
      "mlmBonus": 150000,
      "totalPayment": 1387760,
      "paymentDate": "2026-04-05"
    }
  ],
  "status": "pending_approval",
  "createdAt": "2026-04-01T00:00:00"
}
```

**정산 프로세스 (Celery 비동기):**
```
매월 1일 자정:
1. 지난 달 모든 완료된 수업 조회
2. 수업별 정산액 계산
3. 강사별 합계 계산
4. 3.3% 원천징수 계산
5. MLM 보상 계산
   ├── 레벨별 비율 조회
   ├── 다운라인 실적 합계
   └── 리더십 보너스 계산
6. 35% 규제 확인
7. DB 저장 (settlements 테이블)
8. 강사들에게 알림 발송
9. 기관에 정산 완료 보고
10. 지급 스케줄링 (기관별 계약 조건)
```

---

### 5.3 세무 서비스 API

#### POST /api/tax/refund-inquiry
**용도:** 환급금 조회 (홈택스 연동)

```json
Request:
{
  "instructorId": "inst_001",
  "authToken": "kakao_auth_token_xyz",  // 간편인증 토큰
  "inquiryYears": [2025, 2024, 2023]
}

Response:
{
  "instructorId": "inst_001",
  "inquiryDate": "2026-03-22",
  "results": {
    "2025": {
      "income": 20000000,
      "estimatedTax": 2000000,
      "refund": 1200000,
      "status": "not_filed"
    },
    "2024": {
      "income": 18000000,
      "estimatedTax": 1800000,
      "refund": 850000,
      "status": "not_filed"
    },
    "2023": {
      "income": 16500000,
      "estimatedTax": 1650000,
      "refund": 620000,
      "status": "not_filed"
    }
  },
  "totalRefund": 2670000,
  "note": "기한 후 신고 가능 (최대 5년)"
}
```

---

## 6. 비즈니스 로직 특화 기능

### 6.1 MPV 우선순위

**P0 (필수 - Week 1-2)**
- [ ] 강사 로그인 & 프로필 온보딩
- [ ] 공고 조회 & 지원
- [ ] 수업 출석 체크인 & 완료
- [ ] 월별 정산 자동 계산
- [ ] 원천징수 3.3% 적용
- [ ] 기관 공고 생성 & 지원자 관리
- [ ] 기관 정산 현황 조회

**P1 (고가용성 - Week 3)**
- [ ] 환급금 조회 (홈택스 연동)
- [ ] 신고 대행 신청 (산쩜삼)
- [ ] SOS 긴급 매칭
- [ ] MLM 보상 계산 & 35% 모니터링
- [ ] 관리자 강사 승인 관리
- [ ] 교육청 통합 대시보드

**P2 (확장 기능 - Post MVP)**
- [ ] 양방향 일정 예약 (온디맨드)
- [ ] AI 매칭 알고리즘
- [ ] 보고서 생성 (PDF/DOCX/PPTX)
- [ ] 시스템 권장사항 (성능 최적화)

---

**다음 문서: [3_Permissions.md](3_Permissions.md)**
