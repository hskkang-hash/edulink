# EduLink 개발 운영 상태

## 현재 상태 (2026-03-29)
- 운영 모드: 수동 개발
- Legacy Auto-Dev Loop: 기본 비활성화
- 원칙: 현재 세션 기반 개발만 진행, 최종 완료 후 실제 URL one-shot E2E 1회

## v2.0 데모 개발 진행 문서
- 상세항목 진행 문서: docs/v2-demo-progress-live-2026-03-29.md
- 시나리오 기반 10 Sprint 계획: docs/v2-demo-scenario-sprint-plan-2026-03-29.md
- 실행 기준 계획: docs/v2-sprint-1-10-execution-plan-2026-03-26.md
- Sprint 10 one-shot E2E 체크리스트: docs/sprint10-one-shot-e2e-checklist-2026-03-29.md

## 비활성화 반영 사항
- GitHub Actions 15분 스케줄 loop workflow 비활성화
- start-auto-dev.ps1 기본 실행 차단 (force 플래그 필요)
- auto-dev-daemon.ps1 기본 실행 차단 (force 플래그 필요)
- auto-dev.ps1 continue loop 기본 차단 (force 플래그 필요)

## 수동 실행 기준
- 테스트: 필요 시 수동 실행
- 커밋/배포: 승인 후 수동 실행
- E2E: 릴리즈 후보 확정 시 실 URL에서 one-shot 1회
