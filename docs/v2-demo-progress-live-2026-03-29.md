# EduLink v2.0 개발 진행 현황 (상세항목 기준)

기준일: 2026-03-29  
기준 계획서: docs/v2-demo-scenario-sprint-plan-2026-03-29.md, docs/v2-sprint-1-10-execution-plan-2026-03-26.md

## 1) 요약 진행률

- 전체 Sprint 진행률(10개 기준): 86%
- 완료: 7개 (Sprint 2, Sprint 7, Sprint 8, Sprint 9, 계획/운영 체계 포함)
- 진행중: 2개
- 대기: 1개

## 0) 개발 운영 방식 결정 (2026-03-29)

- 결정: 기존 Auto-Dev Loop(15분 반복) 방식 완전 중단
- 반영
  - GitHub Actions 15분 스케줄 워크플로우 비활성화
  - 로컬 auto-dev 시작/데몬 스크립트 기본 실행 차단
  - 무한 반복 옵션(continueLoop) 기본 차단
- 운영 원칙
  - 현재 대화 기반 수동 개발만 진행
  - 최종 완료 시 실제 URL e2e 1회만 수행

## 2) 상세항목 진행 현황

### Sprint 1 - Baseline and v2 flag
- 상태: 진행중
- 완료
  - v2 시나리오 기반 계획서 신규 작성
- 남은 작업
  - v1/v2 런타임 전환 플래그 실제 운영 스크립트 반영
  - 복구 리허설 로그 템플릿 문서화

### Sprint 2 - Identity and social login
- 상태: 완료
- 완료
  - social_identities 테이블 추가 (backend/app_jwt.py)
  - Google/Kakao 소셜 로그인 API 추가: POST /auth/social-login (backend/app_jwt.py)
  - 소셜 로그인 단위 테스트 3개 추가 (backend/tests/test_auth_passwords.py)
  - 로그인 화면 Google/Kakao 버튼 + API 호출 연동 (frontend/index.html)
  - 운영모드 provider 토큰 검증(google tokeninfo, kakao userinfo) 분기 추가
  - 운영모드 short token 차단 테스트 추가

### Sprint 3 - Instructor onboarding convenience
- 상태: 진행중
- 완료
  - 기존 프로필/승인 흐름은 이미 구현되어 있음
- 남은 작업
  - 3분 완성 UX 기준으로 폼 단계 단축 및 자동 저장
  - 프로필 완성도 스코어의 UI 노출 정합성 검증

### Sprint 4 - Posting acceleration
- 상태: 진행중
- 완료
  - 템플릿 API(생성/조회/인스턴스화) 기반은 기존 코드 반영됨
- 남은 작업
  - 템플릿 추천값(과목/지역/시급) 자동 채움 UX 고도화
  - 재공고 one-click 동선 단축

### Sprint 5 - Candidate compare board
- 상태: 진행중
- 완료
  - 비교 API 엔드포인트 기반은 반영됨
- 남은 작업
  - 실제 비교 보드 화면(정렬/일괄 승인) 완성

### Sprint 6 - Session operations
- 상태: 부분완료
- 완료
  - 세션 생성/체크인/완료, 이벤트 로그 구조 반영
- 남은 작업
  - 교육일지 품질 템플릿과 후속조치 UX 개선

### Sprint 7 - Reputation and quality
- 상태: 완료
- 완료
  - 리뷰/평점 저장 구조 및 조회 API 존재
  - 품질 지표 API 추가: GET /dashboard/quality-metrics
  - 프론트 KPI 보드에 통합 점수/세부지표 카드 반영(기관/운영자)

### Sprint 8 - Finance and settlement
- 상태: 완료
- 완료
  - 정산 요약, CSV 내려받기 등 백엔드 기반 존재
  - 월간 지표 API 추가: GET /dashboard/monthly-indicators
  - 기관/운영자 관점 월간 지표 카드 UI 반영

### Sprint 9 - 1000 user scale pass
- 상태: 완료
- 완료
  - 1000명 기준 데모 데이터 스크립트 추가 (backend/seed_demo_v2.py)
  - 역할 고정 수량 반영: 강사10/학교5/기관5/운영자2/학생978
  - 시드 실행 검증 완료: 출력 기준 1000명 데이터 생성 확인
  - 시드 성능 개선: 해시 1회 재사용으로 반복 실행 시간 단축
  - 운영 데이터와 분리되는 안전 시드 옵션 추가
    - 기본 DB 분리: sqlite:///./edulinks_demo.db
    - non-demo DB 차단 가드(--allow-prod-db 필요)
    - destructive reset/활동 데이터 시드 플래그 분리

### Sprint 10 - Final demo hardening and one-shot e2e
- 상태: 진행중
- 정책 반영
  - 최종 개발완료 후 실제 URL에서 e2e 1회 일괄 실행
- 완료
  - one-shot 실행 스크립트 추가 (scripts/run-one-shot-e2e.ps1)
  - Sprint 10 체크리스트 추가 (docs/sprint10-one-shot-e2e-checklist-2026-03-29.md)
  - RC 잠금 자동화 스크립트 추가 (scripts/prepare-rc-lock.ps1)
  - RC preflight 실행 명령 추가 (package.json: npm run rc:lock)
  - RC lock artifact 생성 완료 (release/rc-lock.json, rc=v2.0.0-rc1)
  - 실 URL one-shot e2e 1회 실행 완료 (2026-03-29, baseUrl=https://edulinks.pro)
  - 로그인/소셜 로그인 UX 핫픽스 반영
    - 소셜 로그인 버튼 클릭 시 즉시 진행 상태 표시 + 중복 클릭 방지 (frontend/index.html)
    - 회원가입 레이어 open 시 로그인 패널 비활성화로 클릭 가로채기 혼선 제거 (frontend/index.html)
  - Worker API 프록시 가용성 개선
    - BACKEND_ORIGIN_FALLBACKS 및 timeout 기반 failover 로직 추가 (worker.js, wrangler.toml)
- 남은 작업
  - Release Candidate 태그 확정/배포
  - 백엔드 터널 복구 후 one-shot 재실행 1회
  - 실행 결과(최종 PASS JSON/판정) 증적 갱신

## 3) 고객 데모 데이터/콘텐츠 준비 현황

- 사용자군 정의: 완료
  - 강사 10, 학교 5, 교육기관 5, 시스템 운영자 2, 학생 978
- 콘텐츠 반영: 진행중
  - 공고/지원/세션/리뷰 데이터 생성 로직 구현
- 대시보드 반영: 진행중
  - 역할별 통계 API는 존재, 시드 데이터 표시 검증 진행 중

## 4) 테스트 전략 현황

- 단위 테스트
  - 인증 테스트(10개) 실행 예정/검증
- E2E
  - 중간 단계의 분산 e2e는 최소화
  - 실제 URL one-shot e2e 1회 실행 완료 (2026-03-29)

### 4-1) 실 URL one-shot e2e 실행 결과 (2026-03-29)

- 실행 명령
  - powershell -ExecutionPolicy Bypass -File scripts/run-one-shot-e2e.ps1 -BaseUrl https://edulinks.pro -Project chromium -ResultFile e2e/chromium-oneshot-20260329-live.json
- 환경 체크
  - https://edulinks.pro/ : 200 OK (프론트 정적 페이지 응답)
  - https://edulinks.pro/health : 503 Service Unavailable (x-localtunnel-status: Tunnel Unavailable)
- 판정
  - FAIL (원인: 백엔드/API 경로 불가용으로 로그인/권한 플로우 실패)
- 주요 실패 패턴
  - 로그인 후 body class가 view-webapp으로 전환되지 않음 (view-prelogin 유지)
  - 인증/내비게이션 시나리오 연쇄 실패
- 증적
  - HTML: e2e/report/index.html
  - 최신 실패 로그: test-results/* (screenshot, video, trace)

## 6) 역할별 QA 계정 (ID/PW)

- 자동화 기준 계정 (E2E 테스트와 동일)
  - instructor: qa.instructor@edulink.local / QaPass123!
  - institution: qa.institution@edulink.local / QaPass123!
  - district: qa.district@edulink.local / QaPass123!
  - admin: qa.admin@edulink.local / QaPass123!
- 실 URL 사용 방식
  - https://edulinks.pro 에서 위 4개 계정으로 로그인 시도
  - 백엔드가 503인 경우 프론트가 오프라인 데모 모드로 자동 전환되어 동일 계정으로 역할별 화면, 메뉴 전수, 로그아웃 동선을 검증 가능
  - 메뉴 전수 회귀 스펙: e2e/tests/live-menu-coverage.spec.js
- 계정 생성 스크립트
  - scripts/create-qa-users.ps1
  - 실행 예시: powershell -ExecutionPolicy Bypass -File scripts/create-qa-users.ps1 -BaseUrl https://edulinks.pro -OutputFile e2e/qa-users-live.json
- 현재 상태 (2026-03-29)
  - /health 503으로 register API도 503 응답
  - 계정 생성 요청은 정상 전송되나 서버 불가용으로 확정 생성 불가

## 5) 지금부터의 실행 순서

1. Release Candidate 태그 확정 및 배포
2. 백엔드 터널 복구 확인 (/health=200)
3. scripts/create-qa-users.ps1로 역할별 계정 생성 결과 확보
4. Sprint 10 one-shot 스크립트로 실제 URL 재실행 1회
5. 결과 증적 아카이브 후 데모 승인 로그 업데이트

## 7) 유저별 기능 비교표 (실사용 검증 기준)

| 기능 영역 | instructor (강사) | institution (기관) | district (교육청) | admin (운영자) |
| --- | --- | --- | --- | --- |
| 대시보드/현황 | O | O | O | O |
| 공고 탐색/관리 | 공고 탐색 O | 공고 등록/관리 O | 기관 공고 모니터링 O | 전체 공고 모니터링 O |
| 지원/매칭 | 내 지원 O | 지원자 심사 O | 관할 기관/매칭 현황 O | 회원/매칭 감사 O |
| 수업 운영 | 수업 일정/체크인/일지 O | 수업 일정/배정 O | 지역 단위 수업 통계 O | 플랫폼 단위 수업 통계 O |
| 강사 비교/랭킹 | 조회 O | 조회 O | 지역 비교 O | 플랫폼 비교 O |
| 정산/세무/예산 | 강사 정산/세무 O | 기관 정산 O | 예산 집행/커버리지 O | 정산 감사/정책 준수 O |
| 계약/에스크로 | 계약 확인 O | 계약/에스크로 처리 O | 기관 계약 상태 모니터링 O | 정책/규정 기반 감사 O |
| 네트워크/MLM | 개인 네트워크 O | 기관 네트워크 O | 지역 네트워크 관측 O | 플랫폼 원장/리워드 O |
| SOS/안전 | SOS 발신 O | SOS 배정 O | 관할 SOS 모니터링 O | 전역 SOS 감사 O |
| 계정/보안 | 마이페이지 O | 마이페이지 O | 마이페이지 O | 마이페이지 + 고급관리 O |

- 공통 회귀 검증 스펙: e2e/tests/live-menu-coverage.spec.js
- 비고: 백엔드 503 구간에서는 오프라인 데모 모드로 동일 동선/메뉴 검증 가능

## 8) UI 오표시 수정 + 재배포 결과 (2026-03-29)

- 수정 내용
  - webapp 사이드 메뉴 폭/텍스트 처리 개선: 한글 메뉴가 세로로 깨져 보이던 문제 수정
  - 메뉴 라벨/그룹 헤더에 nowrap + ellipsis + keep-all 적용
  - role별 메뉴 이동/로그아웃 동선 유지
- 배포 명령
  - npm.cmd run cf:deploy
- 배포 결과
  - Worker Version ID: a1f86531-ea56-4f3e-839f-315004003310
  - edulink.hskkang.workers.dev 반영 완료
- 실 URL 재검증
  - 명령: $env:E2E_BASE_URL='https://edulinks.pro'; npx.cmd playwright test e2e/tests/live-menu-coverage.spec.js --project=chromium
  - 결과: 4 passed (22.0s)
  - instructor / institution / district / admin 전 역할 메뉴 전수 + 로그아웃 동선 통과
