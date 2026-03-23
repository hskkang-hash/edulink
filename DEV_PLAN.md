# EduLink 개발 계획서 (PRD 기반)

**기준일:** 2026-03-23  
**버전:** 1.0  
**방침:** 사용자별 기능 우선 | 완성도 중심 | 기존 3개 요청(auto-dev 시리즈) 취소

---

## 📊 현재 개발 상태 분석

### ✅ 완료된 영역

| 영역 | 상태 | 비고 |
|------|------|------|
| 백엔드 Flask API (`app_jwt.py`) | ✅ 완료 | 실제 운영 엔트리포인트 |
| 인증: 회원가입/로그인/토큰 | ✅ 완료 | 패스워드 해싱, 정책 검증 |
| 비밀번호 변경/재설정 | ✅ 완료 | 이메일 어댑터 연동 |
| 공고(Postings) CRUD | ✅ 완료 | GET/POST/PUT/DELETE |
| 지원(Applications) CRUD | ✅ 완료 | 상태 변경, 삭제 포함 |
| 세무 온보딩/조회/신고 | ✅ 완료 | Mock HomeTax/삼쩜삼 |
| CMS 후불 청구 | ✅ 완료 | 이용료 자동화 |
| MLM 네트워크 링크/판매/보너스 | ✅ 완료 | 35% 방판법 컴플라이언스 |
| 관리자(Admin) API | ✅ 완료 | 회원관리, 역할변경, 요약 |
| 교육청(District) API | ✅ 완료 | 기관목록, 비교, 예산 |
| 대시보드 통계 API | ✅ 완료 | stats, activity |
| Prometheus 메트릭 | ✅ 완료 | /metrics 엔드포인트 |
| Docker 설정 | ✅ 완료 | docker-compose, nginx |
| 기본 테스트 스위트 | ✅ 완료 | test_full_journey, test_mvp_flow 등 |
| 프론트엔드 UI 쉘 | ✅ 완료 | index.html (단일 파일) |

### ⚠️ 미완성/결함 영역

| 영역 | 상태 | 문제 |
|------|------|------|
| `main.py` (레거시) | ⚠️ 혼재 | Pydantic BaseModel import 누락, demo_token 평문 사용 |
| 프론트 - 강사 대시보드 | ❌ 미구현 | 실제 API 연동 없음 |
| 프론트 - 강사 공고/지원 | ❌ 미구현 | 정적 더미 UI만 존재 |
| 프론트 - 강사 정산/세무 | ❌ 미구현 | 없음 |
| 프론트 - 기관 관리 웹 | ❌ 미구현 | 없음 |
| 프론트 - 관리자 웹 | ❌ 미구현 | 없음 |
| 강사 프로필 온보딩 | ❌ 미구현 | DB 스키마 없음 |
| 수업 세션 (GPS 체크인) | ❌ 미구현 | API/DB 없음 |
| SOS 긴급 매칭 알림 | ❌ 미구현 | 없음 |
| 전자계약 | ❌ 미구현 | 없음 |
| 강사 리뷰/평점 | ❌ 미구현 | DB/API 없음 |
| 에스크로 결제 (Stripe/KCP) | ❌ 미구현 | Mock만 있음 |
| 양방향 일정 예약 | ❌ 미구현 | 없음 |

---

## 🎯 개발 우선순위 원칙

1. **사용자별 기능 우선** — 강사 → 기관 → 관리자 → 교육청 순
2. **완성도 중심** — 미완성 화면 없이 각 기능을 끝낸 후 다음으로
3. **프론트+백엔드 동시 완성** — API만 있고 UI 없는 기능은 미완성으로 간주
4. **보안 우선** — 평문 토큰, 미검증 입력 즉시 수정

---

## 🗂️ Sprint 계획

---

### 🔴 Sprint 1: 백엔드 결함 수정 + 강사 프로필 온보딩
**기간:** Week 1 | **우선순위:** P0 (사용자 진입 게이트)

#### 1-1. 레거시 `main.py` 제거/정리
- [x] `app_jwt.py`를 단일 엔트리포인트로 확정
- [ ] `main.py`, `main_fixed.py`, `main_new.py`, `main_simple.py` 삭제 또는 archive 처리
- [ ] `demo_token` 평문 인증 제거 (보안 취약점)

#### 1-2. 강사 프로필 온보딩 API 구현
- [x] DB 테이블: `instructor_profiles` — 이름, 생년월일, 과목(복수), 지역, 시간, 사업자번호 등
- [x] `POST /instructor/profile` — 프로필 최초 등록
- [x] `GET /instructor/profile` — 본인 프로필 조회
- [x] `PUT /instructor/profile` — 수정
- [x] `GET /instructor/profile/status` — 승인 상태 조회 (`pending`/`approved`/`rejected`)
- [x] 관리자 승인/반려 API: `PATCH /admin/profiles/<id>/review`

#### 1-3. 범죄경력 조회 동의 플래그
- [x] `instructor_profiles`에 `background_check_consent` 컬럼 추가
- [x] `child_abuse_consent` 컬럼 추가
- [x] 동의 없이 매칭 불가 로직 적용

---

### 🔴 Sprint 2: 강사용 프론트엔드 (핵심 화면)
**기간:** Week 1-2 | **우선순위:** P0 (강사 = 핵심 사용자)

#### 2-1. 강사 대시보드 (`/instructor/home`)
- [x] 이번 달 수익 요약 카드 (총수익, 원천징수, 순수령액)
- [x] 예정 수업 목록 (날짜, 과목, 학교)
- [x] 지원 현황 요약 (대기/승인/거절)
- [x] 실제 API 연동: `GET /dashboard/stats`, `GET /dashboard/activity`

#### 2-2. 강사 공고 리스트 (`/instructor/postings`)
- [x] 과목/지역/급여 필터
- [x] 공고 카드 (학교명, 과목, 시급, 평점)
- [x] 지원하기 버튼 → `POST /applications`
- [x] 내 지원 현황 탭 (`GET /applications`)
- [x] 지원 취소 기능 (`DELETE /applications/<id>`)

#### 2-3. 강사 프로필 온보딩 화면 (`/instructor/onboarding`)
- [x] 단계별 폼 (기본정보 → 교육정보 → 세무정보 → 신원확인)
- [x] 동의서 체크박스 (원천징수, 범죄경력, 아동학대)
- [x] 제출 후 심사 대기 상태 표시

#### 2-4. 강사 인증 화면
- [x] 로그인 폼 → API 연동
- [x] 회원가입 폼 (역할 선택: 강사/기관)
- [x] 비밀번호 재설정 플로우

---

### 🟡 Sprint 3: 수업 세션 관리
**기간:** Week 2 | **우선순위:** P0 (핵심 비즈니스 플로우)

#### 3-1. 수업 세션 API
- [x] DB 테이블: `sessions` — posting_id, instructor_id, org_id, scheduled_at, checked_in_at, completed_at, duration_minutes, status
- [x] `POST /sessions` — 수업 생성 (기관이 배정 시 자동)
- [x] `GET /sessions` — 내 수업 목록 (역할별 필터)
- [x] `POST /sessions/<id>/checkin` — GPS 체크인 (위경도 기록)
- [x] `POST /sessions/<id>/complete` — 수업 완료 + 일지 작성
- [x] 자동 정산 계산: `rate × (실제시간/예정시간) × (1 - 0.033)`

#### 3-2. 수업 세션 프론트 (`/instructor/sessions`)
- [x] 오늘 수업 목록
- [x] GPS 체크인 버튼 (위치 API 사용)
- [x] 수업 완료 + 일지 작성 폼
- [x] 수업 이력 조회

---

### 🟡 Sprint 4: 정산 및 세무 화면 (강사)
**기간:** Week 2-3 | **우선순위:** P0 (핵심 가치)

#### 4-1. 강사 정산 화면 (`/instructor/settlements`)
- [x] 월별 정산 탭 — API: `GET /postings/settlement-summary`
- [x] 총수익 / 원천징수 / 순수령액 표시
- [x] 정산 명세 다운로드 (CSV)

#### 4-2. 강사 환급금 조회 화면
- [x] 세무 온보딩 폼 → `POST /api/tax/onboard`
- [x] 환급금 조회 버튼 → `GET /api/tax/estimate`
- [x] 연도별 환급 예상액 표시 (2022~2025)
- [x] "신고 대행 신청" 버튼 → `POST /api/tax/submit`
- [x] 신고 진행 상태 트래커 → `GET /api/tax/status/<id>`

---

### 🟠 Sprint 5: 기관(Organisation) 웹 
**기간:** Week 3 | **우선순위:** P0 (B2B 고객)

#### 5-1. 기관 대시보드 (`/org/dashboard`)
- [x] KPI 카드: 당일 수업, 신규공고, 정산대기, 평가대기
- [x] 이번 달 통계 (총수업, 강사평점, 월정산액)
- [x] 실제 API 연동: `GET /dashboard/stats`

#### 5-2. 기관 공고 관리 (`/org/postings`)
- [x] 공고 생성 폼 → `POST /postings`
- [x] 공고 목록/수정/삭제
- [x] 공고별 지원자 목록 → `GET /applications?posting_id=<id>`
- [x] 지원자 승인/거절 → `PATCH /applications/<id>`
- [x] 지원자 상세 프로필 (범죄경력 확인, 리뷰 등)

#### 5-3. 기관 수업 실적 (`/org/sessions`)
- [x] 수업 목록 (강사명, 과목, 상태)
- [x] 시간 보정 기능 (예정→실제)
- [x] 정산액 자동 재계산 표시

#### 5-4. 기관 정산 (`/org/settlements`)
- [x] 월별 정산 현황
- [x] 강사별 지급 상태
- [x] Excel/CSV 다운로드

---

### 🔵 Sprint 6: 관리자 웹
**기간:** Week 3-4 | **우선순위:** P1

#### 6-1. 강사 승인 관리
- [x] 신청자 목록 → `GET /admin/users`
- [x] 프로필 상세 + 서류 확인
- [x] 승인/반려 → `PATCH /admin/profiles/<id>/review`

#### 6-2. MLM 컴플라이언스 대시보드
- [x] 35% 규제 비율 게이지 → `GET /api/network/compliance`
- [x] 월별 재계산 로그 표시
- [x] 보상 규칙 편집/시뮬레이션 → `PUT /api/network/admin/rules`, `POST /api/network/admin/rules/simulate`
- [x] TOP 스폰서 순위 → `GET /api/network/admin/top-sponsors`

#### 6-3. 전체 플랫폼 요약
- [x] 사용자 통계 (강사/기관/관리자 수)
- [x] 총 매칭 건수, 정산액
- [x] API: `GET /admin/platform-summary`

---

### 🔵 Sprint 7: SOS 긴급 매칭 + 리뷰
**기간:** Week 4 | **우선순위:** P1 (차별화 기능)

#### 7-1. SOS 긴급 매칭 API
- [x] `POST /sos` — SOS 공고 생성 (기관)
- [x] `GET /sos/available` — 조건 매칭 강사 목록
- [x] `POST /sos/<id>/accept` — 강사 수락
- [ ] WebSocket 또는 SSE: 실시간 SOS 알림 push

#### 7-2. 강사 리뷰/평점 API
- [x] DB: `reviews` — reviewer_id, instructor_id, session_id, rating, comment
- [x] `POST /reviews` — 리뷰 작성 (기관/학생)
- [x] `GET /reviews?instructor_id=<id>` — 강사 리뷰 목록
- [x] 강사 평균 평점 계산 → 프로필에 반영

#### 7-3. 리뷰 화면
- [x] 기관: 수업 완료 후 평점 입력 폼
- [x] 강사: 내 리뷰 목록 조회

---

### ⚪ Sprint 8: 교육청 웹 (B2G)
**기간:** Week 4-5 | **우선순위:** P1

#### 8-1. 교육청 대시보드 (`/district/dashboard`)
- [x] KPI 요약 (학교 수, 프로그램 수, 강사 수, 학생 수)
- [x] API: `GET /district/budget-summary`, `GET /district/regional-comparison`

#### 8-2. 학교별 현황
- [x] 학교 목록 → `GET /district/institutions`
- [x] 학교별 프로그램/예산/강사 상세

#### 8-3. 통계 리포트
- [x] 만족도, 참여도, 결원 대응률
- [ ] 리포트 생성 (PDF/CSV)

---

### ⚪ Sprint 9: 전자계약 + 에스크로 (고도화)
**기간:** Week 5+ | **우선순위:** P2

#### 9-1. 전자계약
- [x] DB: `contracts` — 계약서 파일, 서명 상태, 만료일
- [x] 계약서 발송/서명/다운로드 API
- [x] 기관 웹 계약 관리 화면

#### 9-2. 에스크로 결제 연동
- [x] Stripe 에스크로 플로우 (사전결제 → 수업완료 → 정산)
- [x] 환불 로직 (노쇼, 취소)

---

## 🔄 다음 즉시 실행 작업 (Sprint 1 시작)

### 지금 당장 할 것:

1. **`instructor_profiles` 테이블 + API 구현** (`app_jwt.py` 확장)
2. **프론트 강사 대시보드 실제 연동** (`index.html` 확장)
3. **`sessions` 테이블 + 체크인/완료 API**
4. **`main.py` 보안 취약점** (`demo_token` 평문) 제거

---

## 📈 완성도 기준 (Definition of Done)

각 스프린트 기능은 아래를 모두 만족해야 "완료":
- [ ] API 구현 + 단위 테스트 통과
- [ ] 프론트 화면 연동 (더미 데이터 없음)
- [ ] 에러 케이스 처리 (401, 403, 400, 404)
- [ ] 역할(Role) 기반 접근 제어 검증

---

*이 문서는 개발 진행에 따라 지속 업데이트됩니다.*
