# EduLink v2.0 Sprint 1-10 상세 실행계획 (착수본)

기준일: 2026-03-26  
기준 코드: backend/app_jwt.py, frontend/index.html, e2e/tests/*

## 1. 목표

- v1 운영 안정성을 유지하면서 v2 Program A~C(Sprint 1~10)를 단계적으로 가동
- Sprint별 완료 조건을 코드/테스트/롤백 기준으로 강제
- Sprint 10(SOS 실시간 대체 배치)까지 즉시 개발 가능한 백로그를 실행 단위로 분해

## 2. Sprint 1-10 상세 계획

## Sprint 1 (A1) v1 기준선 봉인

- 산출물
  - release/v1-stable 브랜치
  - v1.0-stable 태그
  - DB 스냅샷 + Worker version 매핑
  - 회귀 테스트 결과 스냅샷
- 체크리스트
  - 30분 내 복구 리허설 1회

## Sprint 2 (A2) 기능 플래그/환경 분리

- 산출물
  - FF_V2_SUPPLY_CLOUD, FF_V2_OPERATIONS_CLOUD, FF_V2_FINANCE_ENGINE, FF_V2_ROLE_HOME, FF_V2_CONTRACT_PRICING, FF_V2_MATCHING_ENGINE
  - env 세트(v1, v2-canary, v2-prod)
- 체크리스트
  - 동일 배포본에서 설정만 바꿔 v1/v2 전환 가능

## Sprint 3 (A3) 데이터 전환 프레임

- 산출물
  - expand/migrate/contract 가이드
  - 마이그레이션 네이밍 규칙
  - idempotent 백필 템플릿
- 체크리스트
  - 신규 테이블 추가 후 v1 회귀 통과

## Sprint 4 (B1) 강사 마스터 프로필

- 산출물
  - 프로필/자격/서류/검증 상태 통합 조회 API
  - 프로필 완성도 계산
- 체크리스트
  - 단일 조회로 강사 상태 설명 가능

## Sprint 5 (B2) 평판 엔진

- 산출물
  - 완료율/노쇼율/평균리뷰/응답속도 집계
  - 점수 산식 + 관리자 보정
- 체크리스트
  - 점수와 근거지표 동시 노출

## Sprint 6 (B3) 가용 슬롯/배정 가능성

- 산출물
  - 슬롯 정규화
  - 과목/지역/시간 적합도 계산
  - 반복 수업 배정 지표
- 체크리스트
  - 후보 우선순위가 재현 가능

## Sprint 7 (C1) 기관 공고 템플릿

- 목표
  - 반복 공고 업무를 템플릿 기반으로 표준화
- API
  - POST /postings/templates
  - GET /postings/templates
  - POST /postings/templates/{id}/instantiate
  - PATCH /postings/{id}/status
- 완료 기준
  - 템플릿으로 공고 생성 시 기존 공고 API와 호환

## Sprint 8 (C2) 지원자 비교/심사 보드

- 목표
  - 기관이 한 화면에서 비교/심사 가능
- API
  - GET /applications/compare?posting_id={id}
- 화면(다음 작업)
  - 비교표(리뷰, 프로필상태, 과목/지역 적합도)
  - 일괄 심사 액션

## Sprint 9 (C3) 세션 운영 이벤트 표준화

- 목표
  - 세션 라이프사이클 이벤트 기록 체계 확립
- 데이터
  - session_events 테이블
- 이벤트
  - session_created
  - session_checkin
  - session_completed
  - session_adjusted

## Sprint 10 (C4) SOS 대체배치

- 목표
  - SOS 생성/수락 이벤트를 운영 로그에 통합
- 이벤트
  - sos_created
  - sos_accepted
- 다음 단계
  - SSE 스트림 + 타임아웃/재배정 정책 구현

## 3. 이번 착수에서 실제 반영된 코드

- backend/app_jwt.py
  - posting_templates, session_events 테이블 추가
  - 공고 템플릿 생성/조회/인스턴스화 API 추가
  - 공고 상태 전환 API 추가
  - 지원자 비교 API 추가
  - 세션/SOS 이벤트 로깅 훅 추가

- backend/tests/test_operations_sprint7_10.py
  - Sprint 7~10 API 및 이벤트 로그 검증 테스트 추가

## 4. 즉시 실행 순서

1. 백엔드 단위 테스트 실행
2. 전체 E2E(Playwright) 일괄 실행
3. 실패 케이스를 Sprint별 결함 백로그로 분류
4. Sprint 8 UI 비교보드, Sprint 10 SSE를 다음 커밋에서 구현

## 5. 리스크

- 실도메인 백엔드가 503이면 E2E는 환경 실패로 전파됨
- 현재 Sprint 10은 API/이벤트 중심 착수 상태이며 실시간 채널(SSE)은 후속 구현 필요
- 템플릿 반복 스케줄의 배치 생성(job runner)은 아직 미구현
