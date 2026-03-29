# EduLink v2.0 개발 진행 현황 (상세항목 기준)

기준일: 2026-03-29  
기준 계획서: docs/v2-demo-scenario-sprint-plan-2026-03-29.md, docs/v2-sprint-1-10-execution-plan-2026-03-26.md

## 1) 요약 진행률

- 전체 Sprint 진행률(10개 기준): 35%
- 완료: 3개 (Sprint 2 일부, Sprint 7 일부, 계획/문서 체계)
- 진행중: 4개
- 대기: 3개

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
- 상태: 진행중 (백엔드+프론트 기본연결 완료)
- 완료
  - social_identities 테이블 추가 (backend/app_jwt.py)
  - Google/Kakao 소셜 로그인 API 추가: POST /auth/social-login (backend/app_jwt.py)
  - 소셜 로그인 단위 테스트 3개 추가 (backend/tests/test_auth_passwords.py)
  - 로그인 화면 Google/Kakao 버튼 + API 호출 연동 (frontend/index.html)
- 남은 작업
  - 운영모드에서 토큰 검증 강화를 위한 provider 검증 어댑터 도입

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
- 상태: 부분완료
- 완료
  - 리뷰/평점 저장 구조 및 조회 API 존재
- 남은 작업
  - 완료율/노쇼율/응답속도 통합 점수 산식 대시보드 반영

### Sprint 8 - Finance and settlement
- 상태: 부분완료
- 완료
  - 정산 요약, CSV 내려받기 등 백엔드 기반 존재
- 남은 작업
  - 기관/운영자 관점 월간 지표 시각화 강화

### Sprint 9 - 1000 user scale pass
- 상태: 진행중
- 완료
  - 1000명 기준 데모 데이터 스크립트 추가 (backend/seed_demo_v2.py)
  - 역할 고정 수량 반영: 강사10/학교5/기관5/운영자2/학생978
  - 시드 실행 검증 완료: 출력 기준 1000명 데이터 생성 확인
  - 시드 성능 개선: 해시 1회 재사용으로 반복 실행 시간 단축
- 남은 작업
  - 운영 데이터와 분리된 안전 시드 옵션 추가

### Sprint 10 - Final demo hardening and one-shot e2e
- 상태: 대기 (요청사항 반영)
- 정책 반영
  - 최종 개발완료 후 실제 URL에서 e2e 1회 일괄 실행
- 남은 작업
  - 실행 시점 고정(Release Candidate 기준)
  - 최종 e2e 체크리스트와 보고서 템플릿 확정

## 3) 고객 데모 데이터/콘텐츠 준비 현황

- 사용자군 정의: 완료
  - 강사 10, 학교 5, 교육기관 5, 시스템 운영자 2, 학생 978
- 콘텐츠 반영: 진행중
  - 공고/지원/세션/리뷰 데이터 생성 로직 구현
- 대시보드 반영: 진행중
  - 역할별 통계 API는 존재, 시드 데이터 표시 검증 진행 중

## 4) 테스트 전략 현황

- 단위 테스트
  - 인증 테스트(9개) 실행 통과
- E2E
  - 중간 단계의 분산 e2e는 최소화
  - 최종 완료 시 실제 URL one-shot e2e 1회 수행 예정 (요청사항 준수)

## 5) 지금부터의 실행 순서

1. 운영모드 소셜 토큰 검증 어댑터 추가 (Sprint 2 잔여)
2. 데모 데이터 안전 시드 옵션(운영 데이터 분리) 추가 (Sprint 9 잔여)
3. 대시보드에서 데모 데이터 표시 확인
4. Sprint 10 체크리스트 잠금 후 실제 URL 최종 e2e 1회 실행
