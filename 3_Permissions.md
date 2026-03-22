# EDULINK 권한 관리 및 접근 제어

**Version:** 1.0  
**Date:** March 2026  
**Framework:** Casbin + FastAPI-Users + React-Admin  
**Status:** RBAC Specification Complete

---

## 1. RBAC 권한 모델 (Role-Based Access Control)

### 1.1 주체(Subject) 정의

**강사 권한 레벨:**
```
Instructor
├── Level 1 (기본 강사)
│   ├── 상태: 신규 / 활성 / 미활성
│   ├── 조건: PV ≥ 200,000 (월)
│   └── 권한: 공고 지원, 수업 수행, 정산 조회 (자신의 것)
│
├── Level 2 (우수 강사)
│   ├── 상태: 3개월 평균 4.5★ + 월 100만원 이상 수익
│   ├── 조건: PV ≥ 5,000,000 (월)
│   └── 권한: 레벨1 + 다운라인 모집 (MLM), 리뷰 응답
│
└── Level 3 (리더)
    ├── 상태: 1년 연속 우수 + 10명 이상 다운라인 활성
    ├── 조건: PV ≥ 10,000,000 (월)
    └── 권한: 레벨2 + 팀 리더보드, 교육 콘텐츠 제작
```

**기관 권한 레벨:**
```
Organization
├── Admin (기관 관리자)
│   ├── 권한:
│   │   ├── 공고 CRUD (자신 기관의)
│   │   ├── 강사 지원자 검토 & 수락/거절
│   │   ├── 수업 일정 관리
│   │   ├── 정산 현황 조회 & 확인
│   │   ├── 기관 통계 조회
│   │   └── 하위 역할 생성 (Accountant, Viewer)
│   └── 범위: 자신 기관만
│
├── Accountant (회계담당)
│   ├── 권한:
│   │   ├── 정산 현황 조회
│   │   ├── 세금 보고서 생성
│   │   ├── 맞춤법 확인 (검토만)
│   │   └── 엑셀 내보내기
│   └── 범위: 자신 기관만 (부분 접근)
│
└── Viewer (뷰어)
    ├── 권한:
    │   ├── 대시보드 조회 (읽기 전용)
    │   ├── 통계 조회 (읽기 전용)
    │   └── 보고서 다운로드 (읽기 전용)
    └── 범위: 자신 기관만 (읽기 전용)
```

**슈퍼 관리자 권한 레벨:**
```
Super Admin
├── Compliance Officer (컴플라이언스)
│   ├── 권한:
│   │   ├── 강사 승인/거절
│   │   ├── MLM 규제 모니터링 (35% 규제)
│   │   ├── 강사 레벨 관리 (승격/강등)
│   │   ├── 관할 기관 모니터링
│   │   └── 벌금/정지 조치
│   └── 범위: 전체 시스템
│
├── Financial Officer (재무)
│   ├── 권한:
│   │   ├── 전체 정산 현황
│   │   ├── 세금 보고서 검증
│   │   ├── 보정산 승인
│   │   ├── 결제 게이트웨이 설정
│   │   └── 재무 리포트
│   └── 범위: 전체 시스템
│
└── Technical Officer (기술)
    ├── 권한:
    │   ├── 시스템 설정 변경
    │   ├── DB 접근 (읽기 위주)
    │   ├── API 토큰 관리
    │   ├── 로그 검열
    │   └── 긴급 차단 (차단목록 관리)
    └── 범위: 전체 시스템
```

**교육청 권한:**
```
District Admin (교육청 관리자)
├── 권한:
│   ├── 관할 학교 공고 모니터링
│   ├── 관할 지역 통계 조회
│   ├── 예산 집행 현황 모니터링
│   ├── 강사 평점/만족도 조회
│   └── 보고서 생성 (교육청용)
└── 범위: 관할 학교만 (읽기 전용 위주)
```

---

### 1.2 객체(Object) 정의

**Domain 분류:**
```
Resource Domain 구조:
├── User Domain
│   ├── Profile (프로필)
│   ├── Account (계정)
│   ├── Auth (인증)
│   └── Verification (확인)
│
├── Instructor Domain
│   ├── Applications (지원)
│   ├── Sessions (수업)
│   ├── Reviews (리뷰)
│   ├── Earnings (수익)
│   ├── MLM (다단계)
│   └── Qualifications (자격증)
│
├── Organization Domain
│   ├── Postings (공고)
│   ├── Settings (설정)
│   ├── Members (멤버)
│   ├── Billing (청구)
│   └── Analytics (분석)
│
├── Matching Domain
│   ├── SOS (긴급)
│   ├── OnDemand (온디맨드)
│   ├── Schedule (일정)
│   └── Contracts (계약)
│
├── Settlement Domain
│   ├── Monthly (월별)
│   ├── Payments (지급)
│   ├── Withholding (원천징수)
│   └── Adjustments (보정)
│
├── Tax Domain
│   ├── Refund (환급)
│   ├── FilingAuto (자동신고)
│   ├── FilingDeferred (기한후신고)
│   └── Compliance (컴플라이언스)
│
├── MLM Domain
│   ├── Compensation (보상)
│   ├── Hierarchy (계층)
│   ├── Compliance (규제)
│   └── Reports (보고)
│
├── Admin Domain
│   ├── Users (사용자)
│   ├── Organizations (기관)
│   ├── Settings (설정)
│   ├── Monitoring (모니터링)
│   └── Audit (감사)
│
└── Report Domain
    ├── Generated (생성)
    ├── Templates (템플릿)
    ├── Delivery (배포)
    └── Archive (보관)
```

---

### 1.3 작업(Action) 정의

**표준 작업:**
```
CRUD + Special
├── C: Create (생성)
├── R: Read (조회)
├── U: Update (수정)
├── D: Delete (삭제)
├── S: Submit (제출)
├── A: Approve (승인)
└── X: Execute (실행)

Domain 특화 작업:
├── Instructor Specific
│   ├── apply (지원)
│   ├── complete_session (수업 완료)
│   ├── view_earnings (수익 조회)
│   ├── request_refund_inquiry (환급 조회 신청)
│   └── claim_competion (보상 청구)
│
├── Organization Specific
│   ├── select_instructor (강사 선택)
│   ├── adjust_session_hours (시간 보정)
│   ├── confirm_settlement (정산 확인)
│   └── export_report (보고서 내보내기)
│
├── Admin Specific
│   ├── approve_instructor (강사 승인)
│   ├── monitor_compliance (규제 모니터링)
│   ├── adjust_mlm_level (레벨 조정)
│   ├── block_user (차단)
│   └── audit_transaction (거래 감시)
│
└── Technical Specific
    ├── modify_system_config (시스템 설정 변경)
    ├── manage_api_tokens (API 토큰 관리)
    ├── view_system_logs (로그 조회)
    └── emergency_block (긴급 차단)
```

---

## 2. Casbin 정책 정의

### 2.1 정책 규칙 (Policy Rules)

**기본 형식:**
```
ptype, subject, domain, object, action, effect
```

**예시:**
```
# 강사 레벨 1: 자신의 프로필 조회
p, instructor_level1, user, profile, read, allow

# 강사 레벨 1: 공고 조회 및 지원
p, instructor_level1, matching, postings, read, allow
p, instructor_level1, matching, applications, create, allow
p, instructor_level1, matching, applications, read, allow

# 강사 레벨 1: 자신의 수업만 조회
p, instructor_level1, instructor, sessions, read, allow
p, instructor_level1, instructor, sessions, update_own, allow

# 강사 레벨 2: 레벨 1 + 다운라인 모집
p, instructor_level2, instructor, mlm, read, allow
p, instructor_level2, instructor, mlm, recruit, allow

# 기관 관리자: 공고 CRUD
p, organization_admin, organization, postings, create, allow
p, organization_admin, organization, postings, read, allow
p, organization_admin, organization, postings, update, allow
p, organization_admin, organization, postings, delete, allow

# 기관 관리자: 강사 선택
p, organization_admin, organization, applications, read, allow
p, organization_admin, organization, applications, approve, allow
p, organization_admin, organization, applications, reject, allow

# 기관 회계담당: 정산만 조회
p, organization_accountant, organization, settlement, read, allow
p, organization_accountant, organization, settlement, export, allow

# 슈퍼 관리자 - 컴플라이언스: 강사 승인
p, admin_compliance, admin, instructors, approve, allow
p, admin_compliance, admin, instructors, reject, allow
p, admin_compliance, admin, mlm, monitor, allow
p, admin_compliance, admin, mlm, adjust_level, allow

# 교육청: 관할 학교만 모니터링
p, district_admin, district, schools, read, allow
p, district_admin, district, statistics, read, allow

# 시스템 관리자: 모든 권한
p, system_admin, *, *, *, allow
```

---

### 2.2 역할 상속 (Role Inheritance)

**그룹 정책:**
```
g, subject, role, domain
```

**예시:**
```
# 강사 레벨 2는 강사 레벨 1의 권한을 모두 상속
g, instructor_level2, instructor_level1, instructor

# 강사 레벨 3은 강사 레벨 2의 권한을 모두 상속
g, instructor_level3, instructor_level2, instructor

# 기관 회계담당은 뷰어 권한 상속
g, organization_accountant, organization_viewer, organization

# 컴플라이언스 담당자는 파이낸셜 담당자의 읽기 권한 상속
g, admin_compliance, admin_financial, admin_compliance

# 사용자가 여러 역할 가능
g, user_kim@example.com, instructor_level1, instructor
g, user_kim@example.com, organization_admin, organization
```

---

### 2.3 리소스 제약 (Resource Constraints)

**소유권 기반 접근 제어:**
```
# 강사는 자신의 세션만 조회 가능
p2, instructor_level1, instructor, sessions_own, read, allow
# 조건: session.instructor_id == current_user.id

# 기관은 자신의 공고만 수정 가능
p2, organization_admin, organization, postings_own, update, allow
# 조건: posting.organization_id == current_user.organization_id

# 기관은 자신의 교사만 관리 가능
p2, organization_admin, organization, instructors_own, manage, allow
# 조건: instructor in organization.instructors
```

---

## 3. 기능별 권한 매트릭스

### 3.1 강사 앱 권한

| 기능 | Level 1 | Level 2 | Level 3 | 설명 |
|------|---------|---------|---------|------|
| **인증 & 프로필** |
| 로그인 | ✅ | ✅ | ✅ | 모두 가능 |
| 프로필 조회 | ✅ | ✅ | ✅ | 자신의 프로필만 |
| 프로필 수정 | ✅ | ✅ | ✅ | 기본정보만 수정 가능 |
| 문서 재제출 | ✅ | ✅ | ✅ | 거절된 경우만 |
| **매칭** |
| 공고 조회 | ✅ | ✅ | ✅ | 조건(과목, 지역)에 맞는 것만 |
| 공고 지원 | ✅ | ✅ | ✅ | 지원 3개까지 (주당) |
| 지원 취소 | ✅ | ✅ | ✅ | 시작 24시간 전까지 |
| 다운라인 모집 | ❌ | ✅ | ✅ | MLM 기능 |
| SOS 알림 수신 | ✅ | ✅ | ✅ | 조건에 맞으면 자동 |
| **수업** |
| 예정 수업 조회 | ✅ | ✅ | ✅ | 자신의 수업만 |
| 수업 체크인 | ✅ | ✅ | ✅ | GPS 포함 |
| 수업 완료 | ✅ | ✅ | ✅ | 일지 작성 필수 |
| 수업 취소 | ✅ | ✅ | ✅ | 2시간 전까지 벌금 없음 |
| **정산** |
| 월별 정산 조회 | ✅ | ✅ | ✅ | 자신의 정산만 |
| 환급금 조회 | ✅ | ✅ | ✅ | 무료 |
| 신고 대행 신청 | ✅ | ✅ | ✅ | 기한 후 신고 |
| **MLM** |
| 보상 현황 조회 | ❌ | ✅ | ✅ | 레벨 2부터 |
| 다운라인 관리 | ❌ | ✅ | ✅ | 모집한 강사만 |
| 팀 보고서 | ❌ | ❌ | ✅ | 레벨 3만 |
| **리뷰** |
| 받은 리뷰 조회 | ✅ | ✅ | ✅ | 자신의 리뷰만 |
| 리뷰 응답 | ✅ | ✅ | ✅ | 받은 리뷰에만 응답 |

---

### 3.2 기관 관리자 웹 권한

| 기능 | Admin | Accountant | Viewer | 설명 |
|------|-------|-----------|--------|------|
| **공고** |
| 공고 생성 | ✅ | ❌ | ❌ | Admin만 생성 |
| 공고 조회 | ✅ | ❌ | ✅ | Accountant 제외 |
| 공고 수정 | ✅ | ❌ | ❌ | 자신 기관만 |
| 공고 삭제 | ✅ | ❌ | ❌ | 마감 후만 가능 |
| **지원자 관리** |
| 지원자 조회 | ✅ | ❌ | ✅ | Accountant 제외 |
| 강사 선택 | ✅ | ❌ | ❌ | Admin만 |
| 강사 거절 | ✅ | ❌ | ❌ | 사유 필수 |
| **정산** |
| 정산 현황 조회 | ✅ | ✅ | ✅ | 읽기 전용 |
| 정산 확인 | ✅ | ❌ | ❌ | Admin만 |
| 정산 보정 | ✅ | ❌ | ❌ | 시간 조정 등 |
| 정산 내보내기 | ✅ | ✅ | ❌ | 다운로드 권한 |
| **기관 설정** |
| 회원 관리 | ✅ | ❌ | ❌ | Admin만 |
| 역할 생성 | ✅ | ❌ | ❌ | Admin만 |
| 청구 정보 관리 | ✅ | ✅ | ❌ | 기본 수정 가능 |
| **대시보드** |
| 대시보드 조회 | ✅ | ❌ | ✅ | 읽기 전용 |
| 통계 조회 | ✅ | ✅ | ✅ | 매출, 만족도 등 |
| 리포트 생성 | ✅ | ✅ | ❌ | PDF, 엑셀 |

---

### 3.3 슈퍼 관리자 권한

| 기능 | 컴플라이언스 | 재무 | 기술 | 설명 |
|------|-----------|------|------|------|
| **강사** |
| 강사 승인 | ✅ | ❌ | ❌ | 신원조회 후 승인 |
| 강사 거절 | ✅ | ❌ | ❌ | 사유 기록 필수 |
| 강사 차단 | ✅ | ❌ | ✅ | 긴급 제재 |
| 강사 모니터링 | ✅ | ❌ | ❌ | 평점, 민원 추적 |
| **MLM** |
| 규제 모니터링 | ✅ | ✅ | ❌ | 35% 실시간 체크 |
| 레벨 승격 | ✅ | ❌ | ❌ | 수동 승격 |
| 레벨 강등 | ✅ | ❌ | ❌ | 규제 위반 시 |
| 보상 보정 | ✅ | ✅ | ❌ | 계산 오류 수정 |
| **정산** |
| 전체 정산 조회 | ❌ | ✅ | ❌ | 모든 기관 데이터 |
| 정산 승인 | ❌ | ✅ | ❌ | 월별 최종 승인 |
| 지급 스케줄 | ❌ | ✅ | ❌ | 지급일 조정 |
| **세무** |
| 환급금 조회 | ❌ | ✅ | ❌ | 홈택스 API 호출 |
| 신고 대행 | ❌ | ✅ | ❌ | 산쩜삼 제출 |
| 세금 보고서 | ❌ | ✅ | ❌ | 감시/감독 |
| **시스템** |
| 설정 변경 | ❌ | ❌ | ✅ | API 설정 등 |
| 로그 조회 | ❌ | ❌ | ✅ | 감시 로그 |
| API 토큰 관리 | ❌ | ❌ | ✅ | 외부 연동 |
| 유지보수 | ❌ | ❌ | ✅ | DB 접근 (읽기) |
| **감사** |
| 감사 로그 조회 | ✅ | ✅ | ❌ | 거래 추적 |
| 분쟁 해결 | ✅ | ❌ | ❌ | 민원 처리 |

---

## 4. 구현 패턴 (FastAPI + Casbin)

### 4.1 미들웨어 설정

**FastAPI 권한 확인 미들웨어:**
```python
from fastapi import Depends, HTTPException
from fastapi_users import current_active_user
import casbin

# Casbin 초기화
enforcer = casbin.Enforcer("rbac_model.conf", "rbac_policy.csv")

async def check_permission(
    request: Request,
    user: User = Depends(current_active_user),
    enforcer = Depends(get_enforcer)
):
    """
    요청 경로와 메서드를 통해 권한 확인
    """
    method = request.method
    path = request.url.path
    
    # API 경로 → domain:object:action으로 변환
    # e.g., POST /api/postings → organization:postings:create
    
    resource = parse_resource(path, method)
    
    # 사용자 역할 조회
    user_roles = await get_user_roles(user.id)
    
    # Casbin 권한 확인
    for role in user_roles:
        if enforcer.enforce(role, resource.domain, resource.object, resource.action):
            return True
    
    raise HTTPException(status_code=403, detail="Permission denied")

@app.get("/api/instructors/applications")
async def get_applications(
    user: User = Depends(current_active_user),
    permission = Depends(check_permission)
):
    """권한 확인 후 데이터 반환"""
    pass
```

---

### 4.2 리소스 소유권 체크

**소유권 기반 조회:**
```python
@app.get("/api/instructors/{instructor_id}/sessions")
async def get_instructor_sessions(
    instructor_id: str,
    user: User = Depends(current_active_user)
):
    """
    강사는 자신의 세션만 조회 가능
    """
    # 1. Role 기반 권한 확인
    if not enforcer.enforce(user_role, "instructor", "sessions", "read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 2. 소유권 확인 (자신의 ID만 조회 가능)
    if user.id != instructor_id:
        raise HTTPException(status_code=403, detail="Cannot view other's data")
    
    # 3. 데이터 반환
    sessions = db.query(Session).filter(Session.instructor_id == user.id).all()
    return sessions
```

**기관 기반 조회:**
```python
@app.get("/api/organizations/{org_id}/settlements")
async def get_org_settlements(
    org_id: str,
    user: User = Depends(current_active_user)
):
    """
    기관 관리자는 자신 기관의 정산만 조회 가능
    """
    # 1. Role 기반 권한 확인
    if user.role not in ["organization_admin", "organization_accountant"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 2. 조직 소속 확인
    user_org = db.query(User).filter(User.id == user.id).first().organization_id
    if user_org != org_id:
        raise HTTPException(status_code=403, detail="Cannot view other organization")
    
    # 3. 데이터 반환
    settlements = db.query(Settlement).filter(
        Settlement.organization_id == org_id
    ).all()
    return settlements
```

---

### 4.3 동적 권한 확인

**멀티 테넌트 권한:**
```python
@app.post("/api/applications/{app_id}/approve")
async def approve_application(
    app_id: str,
    user: User = Depends(current_active_user)
):
    """
    기관 관리자만 자신 기관의 지원자를 승인 가능
    """
    application = db.query(Application).filter(Application.id == app_id).first()
    posting = db.query(Posting).filter(Posting.id == application.posting_id).first()
    
    # 1. Role 확인
    if user.role != "organization_admin":
        raise HTTPException(status_code=403, detail="Only admin can approve")
    
    # 2. 조직 확인
    if user.organization_id != posting.organization_id:
        raise HTTPException(status_code=403, detail="Different organization")
    
    # 3. 상태 확인
    if application.status != "pending":
        raise HTTPException(status_code=400, detail="Already decided")
    
    # 4. 처리
    application.status = "selected"
    db.commit()
    
    # 5. 알림 발송
    await send_notification(application.instructor_id, "You have been selected")
    
    return {"status": "success"}
```

---

### 4.4 React-Admin 권한 통합

**React-Admin 리소스 권한:**
```jsx
// src/authProvider.ts
const authProvider = {
  login: async (user) => {
    // 로그인 후 권한 조회
    const roles = await fetch('/api/auth/me').then(r => r.json());
    localStorage.setItem('roles', JSON.stringify(roles));
  },

  checkAuth: async () => {
    // 토큰 유효성 확인
    const token = localStorage.getItem('token');
    if (!token) throw new Error('No token');
  },

  getPermissions: async () => {
    // 권한 목록 반환
    const roles = JSON.parse(localStorage.getItem('roles'));
    return roles.map(r => r.resource);
  }
};

// src/App.jsx
export default function App() {
  return (
    <Admin authProvider={authProvider}>
      {/* Admin만 접근 가능 */}
      <Resource
        name="instructors"
        list={<InstructorList />}
        edit={<InstructorEdit />}
        permissions={['organization_admin', 'admin_compliance']}
      />
      
      {/* Accountant는 읽기만 가능 */}
      <Resource
        name="settlements"
        list={<SettlementList />}
        edit={<SettlementEdit />}
        permissions={['organization_admin']}  // Admin만 쓰기 가능
        readPermissions={['organization_accountant']}  // Accountant는 읽기만
      />
    </Admin>
  );
}
```

---

## 5. 감시 로그 (Audit Log)

### 5.1 주요 권한 변경 로깅

```sql
CREATE TABLE audit_logs (
    id VARCHAR PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    user_role VARCHAR,
    action VARCHAR,  -- create, read, update, delete, approve, reject
    domain VARCHAR,  -- instructor, organization, settlement, etc.
    object_id VARCHAR,
    object_type VARCHAR,
    resource_before JSONB,  -- 수정 전 값
    resource_after JSONB,   -- 수정 후 값
    status VARCHAR,  -- success, failed
    reason TEXT,  -- 거절 이유, 오류 메시지
    ip_address VARCHAR,
    timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_action ON audit_logs(action, domain);
```

### 5.2 감시할 핵심 작업

```
1. 강사 승인 (admin_compliance)
2. 강사 거절 (admin_compliance)
3. 강사 차단/해제 (admin_compliance, admin_technical)
4. MLM 레벨 승격/강등 (admin_compliance)
5. 정산 보정 (organization_admin, admin_financial)
6. 정산 승인 (admin_financial)
7. 환급금 조회 (instructor, admin_financial)
8. 신고 대행 납부 (admin_financial)
9. 이용자 차단 (admin_compliance, admin_technical)
10. 시스템 설정 변경 (admin_technical)
```

---

## 6. 보안 체크리스트

- [ ] 모든 API 엔드포인트에 권한 확인 미들웨어 적용
- [ ] 소유권 확인: 사용자 ID, 조직 ID 일치 여부
- [ ] JWT 토큰 만료 시간 설정 (접근: 1시간, 갱신: 7일)
- [ ] Rate limiting: 5회/분 (로그인), 10회/초 (일반)
- [ ] HTTPS TLS 1.3 모든 통신 암호화
- [ ] 암호 정책: 최소 8자, 특수문자, 숫자 포함
- [ ] 감사 로그 6개월 보관
- [ ] 민감 정보 마스킹 (전화번호, 계좌번호)
- [ ] IP 화이트리스트 (관리자 기능)
- [ ] 다중 인증 (MFA) 관리자 필수

---

**다음 문서: [4_Viz_architecture.md](4_Viz_architecture.md)**
