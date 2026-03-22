# EDULINK MVP

## Overview
EDULINK is a tutoring-matching MVP where instructors create postings and students apply.
This repository is currently implemented as a Flask + SQLite app with a plain HTML/JS frontend.

## Current Stack
- Backend: Flask
- Database: SQLite (`backend/edulink.db`)
- Auth token: `itsdangerous` signed token (Bearer)
- Frontend: vanilla HTML/CSS/JS (served by backend root)

## Quick Start

### 1) Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2) Run server
```bash
cd backend
python app_jwt.py
```

### 3) Open app
Use:
```text
http://localhost:8000
```

The backend serves `frontend/index.html` at `/`.

## Main Features (Implemented)
- Register / Login / Logout
- Password hashing for new accounts + lazy migration for legacy plain-text passwords on login
- Password policy enforcement (8-128 chars, includes letters + numbers, no whitespace)
- Password change API (authenticated)
- Password reset request/confirm APIs (token not exposed by default; optional local debug exposure)
- Role-aware UI (instructor vs student)
- Instructor posting CRUD
- Student application submit
- Student pending application cancel
- Instructor application approve/reject
- Role-aware application status filters (all/pending/approved/rejected)
- Instructor application search/sort (posting title or student ID, newest/oldest/status)
- Instructor applicant summary modal with recent status filters and per-status counts (all/pending/approved/rejected)
- Applicant modal filter result summary (shown/total) for faster review context
- Accessible modal interactions (ESC close, overlay close, keyboard focus trap)
- Applicant recent items can open posting detail directly from the modal
- Posting modal supports labeled quick return back to applicant summary context with status summary (P/A/R)
- Applicant recent list defaults to 5 items with Show more/Show less toggle
- Applicant recent toggle displays visible count indicator (shown/filtered)
- Applicant recent list uses subtle staggered reveal animation on expand/filter
- Applicant recent animation speed adapts by action (faster on filter, smoother on expand/collapse)
- Respects prefers-reduced-motion by disabling applicant list reveal animations
- Modal open/close transitions also respect reduced-motion settings
- Motion timings are centralized with CSS variables and reused in JS timing logic
- Applicant list stagger step and stagger cap are also configurable via CSS variables
- Applicant toggle/count controls use motion-variable fade transitions for consistent UI timing
- Posting search filters (subject/region/min rate)
- Posting detail modal view
- Instructor modal shortcut: edit posting in form
- Dashboard stats cards (role-based)
- Dashboard recent activity feed (latest 5)
- Activity status badges + relative time labels
- Activity icons + hover/keyboard interaction
- Activity type filters (all/posting/received/submitted)
- Role-aware activity filter visibility + instant cached type switching
- Dashboard skeleton loaders + improved empty/error states
- "My postings only" toggle for instructors
- Enter-key submit on register/login forms
- Posting creation success toast + auto-scroll to postings
- Tax profile onboarding API
- Tax estimate/submit/status/report APIs
- CMS post-refund fee charge API (mock)

## API Endpoints

### Health / Root
- `GET /` frontend page (or API message fallback)
- `GET /health` API health check

### Auth
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/password/change` (auth)
- `POST /auth/password/reset/request`
- `POST /auth/password/reset/confirm`

Password reset note:
- `POST /auth/password/reset/request` no longer returns reset token by default.
- For local debugging only, set environment variable `EXPOSE_RESET_TOKEN_IN_RESPONSE=true`.

### Postings
- `GET /postings`
- `GET /postings/<posting_id>`
- `POST /postings` (auth)
- `PUT /postings/<posting_id>` (owner only)
- `DELETE /postings/<posting_id>` (owner only)

### Applications
- `GET /applications?status=all|pending|approved|rejected&q=keyword&sort=newest|oldest|status` (auth, role-based list; instructor search supports posting title/student email/student organization/student ID)
- `GET /applications/applicants/<student_id>/summary` (auth, instructor only; only applicants who applied to instructor-owned postings)
- `POST /applications` (auth)
- `PATCH /applications/<application_id>` (instructor only)
- `DELETE /applications/<application_id>` (student, pending only)

### Dashboard
- `GET /dashboard/stats` (auth, role-based stats)
- `GET /dashboard/activity?period=today|7d|30d` (auth, latest 5 role-based activity items)

### Tax / CMS (Expansion Plan - mock workflow)
- `POST /api/tax/onboard` (auth)
- `GET /api/tax/estimate?year=YYYY` (auth)
- `POST /api/tax/submit` (auth)
- `GET /api/tax/status/<submission_id>` (auth)
- `GET /api/tax/events?limit=20&event_type=...&claim_code=...` (auth)
- `GET /api/tax/report/<year>` (auth)
- `POST /api/cms/charge` (auth)

### Network / Compliance (Expansion Plan)
- `POST /api/network/link` (auth)
- `POST /api/network/sales` (auth)
- `GET /api/network/compliance?period=YYYY-MM` (auth)
- `GET /api/network/bonuses?period=YYYY-MM` (auth)
- `GET /api/network/admin/summary?period=YYYY-MM` (auth, admin/super_admin)
- `GET /api/network/admin/top-sponsors?period=YYYY-MM&limit=10` (auth, admin/super_admin)
- `GET /api/network/admin/sponsor-trend?user_id=1&months=6` (auth, admin/super_admin)
- `GET /api/network/admin/rules` (auth, admin/super_admin)
- `PUT /api/network/admin/rules` (auth, admin/super_admin)
- `GET /api/network/admin/rules/audits?limit=20` (auth, admin/super_admin)
- `POST /api/network/admin/rules/simulate` (auth, admin/super_admin)
	- Returns preview KPIs (`current_ratio`, `simulated_ratio`, `delta_ratio`) and sponsor impact list (`sponsor_deltas`, top 10)
	- Frontend supports sponsor impact sorting (absolute/gain/loss), Top N, minimum delta filter, and CSV export with current rule snapshot

Note: Admin insight APIs are now restricted to `admin` and `super_admin` roles.

## Notes
- Existing SQLite schemas are auto-migrated for missing columns on startup.
- For local development, always use `http://` on localhost.

## Suggested Next Steps
- Add instructor dashboard metrics (counts by status)
- Add test cases for auth/role permissions
- Add Docker-based local run profile
- Connect frontend tax widgets to `/api/tax/*` and `/api/cms/charge`
- Add scheduler for monthly tax estimate snapshots and claim reminders
- Replace mock tax provider with real HomeTax/partner integration adapter

## CI (GitHub Actions)
- Workflow file: `.github/workflows/ci.yml`
- Trigger: push, pull request
- Runtime: Python 3.11
- Steps:
	- install `backend/requirements.txt`
	- run `python -m pytest backend/tests -v`

## CD (GitHub Actions)
- Workflow file: `.github/workflows/cd.yml`
- Trigger: push to `main`, manual dispatch
- Registry: GHCR (`ghcr.io`)
- Image:
	- `ghcr.io/<owner>/<repo>/backend:latest`
	- `ghcr.io/<owner>/<repo>/backend:sha-<commit>`

## Security Scan (GitHub Actions)
- Workflow file: `.github/workflows/security.yml`
- Trigger: push, pull request, every Monday 03:00 UTC, manual dispatch
	- `force_deploy=true` 사용 시 감사(Audit) 이슈 자동 생성
- Checks:
	- dependency vulnerability scan: `pip-audit`
	- static security scan: `bandit`

## Lint (GitHub Actions)
	- gate 차단 실패는 별도 Slack 알림으로 구분 전송
- Workflow file: `.github/workflows/lint.yml`
- Trigger: push, pull request, manual dispatch
- Checks:
	- static lint: `ruff check backend/app_jwt.py backend/email_adapter.py backend/tests`

## Staging Deploy (GitHub Actions)
- Workflow file: `.github/workflows/deploy-staging.yml`
- Trigger: push to `main`, manual dispatch
- Deploy method: SSH 접속 후 서버에서 `docker compose up -d --build` 실행
- Safety:
	- GitHub Environment `staging` 게이트(승인/보호 규칙 설정 가능)
	- 동시 배포 방지(concurrency group: `staging-deploy`)
	- 배포 후 health check 실패 시 이전 커밋으로 자동 롤백 시도
	- health check 통과 후 metrics endpoint 스모크 체크
	- 역할별 API 스모크 체크(테스트 계정 시드 + admin 권한 검증)
	- 배포 성공/실패 Slack 알림 지원
	- 실패 시 PagerDuty 트리거(선택, severity=warning)
	- 실패 시 Incident 이슈 자동 생성(중복 시 코멘트 추가)
- Required repository secrets:
	- `STAGING_HOST`
	- `STAGING_USER`
	- `STAGING_SSH_KEY`
	- `STAGING_APP_DIR`
	- `STAGING_PORT` (optional, default: 22)
	- `STAGING_HEALTHCHECK_URL` (optional, default: `http://localhost/health`)
	- `STAGING_METRICS_URL` (optional, default: `http://localhost/metrics`)
	- `STAGING_APP_BASE_URL` (optional, default: `http://localhost:8000`)
	- `STAGING_SLACK_WEBHOOK` (optional)
	- `STAGING_PAGERDUTY_ROUTING_KEY` (optional)

## Production Deploy (GitHub Actions)
- Workflow file: `.github/workflows/deploy-production.yml`
- Trigger: git tag push (`vX.Y.Z`), manual dispatch
- Manual dispatch option:
	- `force_deploy=true` 설정 시 staging incident gate를 1회 우회
	- `force_deploy=true`일 때 `force_reason`(10자 이상) 필수
	- `force_deploy=true`일 때 `force_evidence` 필수 (형식: URL, `#123`, `ABC-123`)
- Safety:
	- GitHub Environment `production` 게이트(승인/보호 규칙 설정 가능)
	- 동시 배포 방지(concurrency group: `production-deploy`)
	- 선택 옵션: open staging incident 개수 기준으로 production 배포 차단
	- incident gate는 최근 시간창(lookback) 내 open staging incident만 집계
	- 태그 배포 시 GitHub Release 노트 자동 생성
	- 배포 성공 시 Release 본문에 검증 결과 자동 첨부
	- `force_deploy=true` 사용 시 감사(Audit) 이슈 자동 생성 (옵션 담당자 자동 할당)
	- 감사(Audit) 이슈에 force deploy 승인 근거(`force_evidence`) 자동 기록
	- 워크플로 로그에 운영 체크리스트 단계 출력
	- 배포 후 health + metrics 스모크 체크
	- 선택 옵션: 역할 기반 API 스모크(계정 시드 + 권한 검증)
	- 실패 시 이전 커밋으로 자동 롤백 시도 + 롤백 후 헬스 재검증
	- 배포 성공/실패 Slack 알림 지원
	- gate 차단 시 Slack에 차단 사유/현재 incident 수/임계치/lookback 시간 + 권장 대응 액션 + runbook 링크 포함
	- 실패 시 PagerDuty 트리거(선택, gate 차단 실패는 제외, reason 기반 severity 반영)
	- 실패 알림(Slack/PagerDuty)에 reason 기반 권장 대응 액션 + runbook 링크 포함
	- `severity=critical`인 실패는 전용 P0 Slack 웹훅으로 추가 알림 가능 (`PROD_P0_SLACK_WEBHOOK`)
	- 실패 시 Incident 이슈 자동 생성
	- Incident 이슈에 분류 라벨 자동 부여 (`gate-blocked`/`deploy-failure`, reason 기반 라벨은 whitelist 정규화, 미정의 reason은 `other`)
	- Incident 이슈에 severity 라벨(`severity-warning|severity-error|severity-critical`) 자동 부여
	- Incident 이슈에 priority 라벨(`priority-p0|priority-p1|priority-p2`) 자동 부여
	- `priority-p0` Incident에는 `oncall-unacked` 라벨과 온콜 확인 체크 항목 자동 추가
	- P0 Incident 이슈 코멘트에 `ACKED` 입력 시 `oncall-unacked -> oncall-acked` 자동 전환
	- ACK 지연이 `PROD_P0_ACK_TIMEOUT_MINUTES`를 초과하면 `ack-sla-breached` 라벨 자동 부여
	- open 상태의 `oncall-unacked` P0 Incident는 주기적으로 스캔되어 ACK 지연 시 재알림 코멘트/전용 P0 Slack 알림 전송
	- `oncall-unacked` P0 Incident가 최대 리마인더 횟수에 도달하면 `oncall-escalated` 라벨 + 에스컬레이션 코멘트 자동 기록
	- 에스컬레이션 시 담당자 자동 할당 체인: `PROD_AUDIT_ASSIGNEES` -> `PROD_ESCALATION_ASSIGNEE_FALLBACK` -> 저장소 owner
	- 저장소 owner가 조직 계정이면 owner fallback assignee 적용을 건너뛰고 라벨/코멘트만 유지
	- 선택 옵션: priority별 milestone 자동 할당 (`PROD_INCIDENT_MILESTONE_P0/P1/P2`)
	- 선택 옵션: milestone 미존재 시 자동 생성 (`PROD_AUTO_CREATE_INCIDENT_MILESTONES=true`)
	- milestone title 매칭은 대소문자/여분 공백을 정규화해 비교하며, 복수 매칭 시 자동 할당을 건너뛰고 경고 로그 기록
	- Incident 이슈 본문/재발 코멘트에 권장 대응 액션 + runbook 링크 자동 기록
	- reason whitelist는 `PROD_REASON_LABEL_WHITELIST`(쉼표 구분)로 운영 설정 가능, 미설정 시 기본 목록 사용
	- `PROD_REASON_LABEL_WHITELIST` 검증: 빈 토큰 금지, 정규화 기준 중복 금지, 최대 20개
	- 분류 라벨이 저장소에 없으면 워크플로우에서 자동 생성 시도
	- 동일 태그 실패 재발 시 기존 Incident 이슈에 코멘트 추가(중복 방지)
- Required repository secrets:
	- `PROD_HOST`
	- `PROD_USER`
	- `PROD_SSH_KEY`
	- `PROD_APP_DIR`
	- `PROD_PORT` (optional, default: 22)
	- `PROD_HEALTHCHECK_URL` (optional, default: `http://localhost/health`)
	- `PROD_METRICS_URL` (optional, default: `http://localhost/metrics`)
	- `PROD_APP_BASE_URL` (optional, default: `http://localhost:8000`)
	- `PROD_ENABLE_ROLE_SMOKE` (optional, default: `false`)
	- `PROD_SLACK_WEBHOOK` (optional)
	- `PROD_P0_SLACK_WEBHOOK` (optional, dedicated webhook for critical failure alerts)
	- `PROD_PAGERDUTY_ROUTING_KEY` (optional)
	- `PROD_RUNBOOK_URL` (optional, default: repository `docs/deployment-runbook.md` URL)
	- `PROD_AUDIT_ASSIGNEES` (optional, comma-separated GitHub usernames)
	- `PROD_REASON_LABEL_WHITELIST` (optional, comma-separated reason keys)
	- `PROD_INCIDENT_MILESTONE_P0` (optional, open milestone title for `priority-p0`)
	- `PROD_INCIDENT_MILESTONE_P1` (optional, open milestone title for `priority-p1`)
	- `PROD_INCIDENT_MILESTONE_P2` (optional, open milestone title for `priority-p2`)
	- `PROD_AUTO_CREATE_INCIDENT_MILESTONES` (optional, `true`/`false`, default: `false`)
	- `PROD_P0_ACK_TIMEOUT_MINUTES` (optional, default: `15`, min: `5`, max: `240`)
	- `PROD_P0_ACK_REMINDER_MAX` (optional, default: `3`, min: `1`, max: `10`)
	- `PROD_P0_REPORT_SLACK_WEBHOOK` (optional, weekly P0 incident summary Slack webhook)
	- `PROD_P0_REPORT_WARNING_SLACK_WEBHOOK` (optional, dedicated Slack webhook used only when weekly report status is `warning`)
	- `PROD_P0_REPORT_WARNING_MENTIONS` (optional, raw Slack mention text for warning alerts such as `@channel` or `<@U12345> <@U67890>`)
	- `PROD_P0_REPORT_ARCHIVE_ISSUE` (optional, default: `true`, create or update a weekly archive issue for each report run)
	- `PROD_P0_REPORT_WARN_ESCALATED_DELTA` (optional, default: `1`, warning when weekly escalated delta reaches threshold)
	- `PROD_P0_REPORT_WARN_SLA_BREACH_DELTA` (optional, default: `1`, warning when weekly SLA breach delta reaches threshold)
	- `PROD_P0_REPORT_WARN_UNACKED_PAST_SLA` (optional, default: `1`, warning when current open unacked past-SLA count reaches threshold)
	- `PROD_ESCALATION_ASSIGNEE_FALLBACK` (optional, comma-separated GitHub usernames used when `PROD_AUDIT_ASSIGNEES` is empty)
	- `PROD_AUDIT_ASSIGNEES` / `PROD_ESCALATION_ASSIGNEE_FALLBACK` 검증: 빈 토큰 금지, 소문자 정규화 기준 중복 금지, 최대 20명, GitHub username 형식 준수
	- `PROD_BLOCK_ON_STAGING_INCIDENTS` (optional, `true`/`false`, default: `false`)
	- `PROD_STAGING_INCIDENT_THRESHOLD` (optional, default: `3`)
	- `PROD_STAGING_INCIDENT_LOOKBACK_HOURS` (optional, default: `24`)

## On-call Ack Automation (GitHub Actions)
- Workflow file: `.github/workflows/oncall-ack.yml`
- Trigger: issue comment created/edited
- Behavior:
	- 대상: `incident` + `production` + `priority-p0` + `oncall-unacked` 라벨 이슈
	- 코멘트 본문이 `ACKED by @username` 형식이고, 멘션 계정과 코멘트 작성자가 일치할 때만 `oncall-acked` 라벨로 자동 전환
	- 형식 불일치 시 ACK 가이드 코멘트(`ONCALL_ACK_FORMAT_GUIDE`)를 1회 자동 기록
	- ACK 성공 시 `oncall-escalated` 라벨이 있으면 자동 해제
	- ACK 지연 시간 기준 버킷 라벨 자동 부여 (`ack-under-15m`, `ack-15-30m`, `ack-30-60m`, `ack-over-60m`)
	- ACK 지연 시간이 `PROD_P0_ACK_TIMEOUT_MINUTES`를 초과하면 `ack-sla-breached` 라벨 자동 부여
	- 전환 이력 코멘트에 담당자/원문 링크/UTC 시각, ACK 지연 시간(incident 생성 후 분 단위), ACK SLA 임계치/위반 여부, `time_to_ack_bucket`, 핵심 라벨 요약(status/priority/severity/reason/ack_sla_breached), ACK 시점 라벨 스냅샷 자동 기록

## On-call Unacked Reminder (GitHub Actions)
- Workflow file: `.github/workflows/oncall-unacked-reminder.yml`
- Trigger: every 15 minutes (schedule), manual dispatch
- Behavior:
	- 대상: `incident` + `production` + `priority-p0` + `oncall-unacked` open 이슈
	- 생성 시각 기준 ACK 타임아웃(`PROD_P0_ACK_TIMEOUT_MINUTES`) 초과 시 리마인더 코멘트 자동 기록
	- 이슈별 리마인더 횟수는 `PROD_P0_ACK_REMINDER_MAX`까지 제한
	- 리마인더 임계치 도달 시 `oncall-escalated` 라벨 + 에스컬레이션 코멘트(`ONCALL_UNACKED_ESCALATION`) 자동 기록
	- 에스컬레이션 코멘트에 핵심 라벨 요약(status/priority/severity/reason) + 당시 라벨 스냅샷 자동 첨부
	- 에스컬레이션 담당자 자동 지정 체인: `PROD_AUDIT_ASSIGNEES` -> `PROD_ESCALATION_ASSIGNEE_FALLBACK` -> 저장소 owner (조직 계정 owner는 assignee fallback 제외)
	- 전용 P0 Slack 웹훅(`PROD_P0_SLACK_WEBHOOK`) 설정 시 동일 내용 추가 전송
	- 수동 실행 시 `dry_run=true`로 후보 이슈만 점검 가능

## P0 Weekly Report (GitHub Actions)
- Workflow file: `.github/workflows/p0-weekly-report.yml`
- Trigger: every Monday 09:00 UTC (schedule), manual dispatch
- Behavior:
	- 대상: 최근 기간(`lookback_days`, 기본 7일) 내 생성된 `incident` + `production` + `priority-p0` 이슈
	- 총 incident 수, open/closed, acked, escalated, `ack-sla-breached`, open unacked, open unacked past SLA 수 집계
	- 동일 길이의 직전 기간과 비교해 총 incident 수, acked, escalated, SLA 위반, open unacked 추세(delta) 함께 출력
	- ACK 버킷 분포(`ack-under-15m`, `ack-15-30m`, `ack-30-60m`, `ack-over-60m`)를 워크플로 summary에 기록
	- ACK 버킷 분포도 직전 기간 대비 delta와 함께 기록
	- escalation delta, SLA breach delta, open unacked past SLA가 설정 임계치를 넘으면 report status를 `warning`으로 표시하고 경보 이유를 summary/Slack에 함께 기록
	- SLA 초과 상태로 남아 있는 open unacked incident 상위 5건을 age 기준으로 함께 출력
	- 기본값으로 주차별 archive issue를 생성하거나 같은 날짜 보고서 재실행 시 기존 issue를 갱신해 이력을 보존 (`PROD_P0_REPORT_ARCHIVE_ISSUE=false`로 비활성화 가능)
	- archive issue가 `warning` 상태면 `needs-attention` 라벨을 자동 부여하고, 정상 상태로 돌아오면 해당 라벨 자동 제거
	- archive issue가 `warning` 상태면 후속조치 체크리스트를 본문에 자동 추가하고, 정상 상태로 돌아오면 갱신된 본문에서 제거
	- 선택 옵션: `PROD_P0_REPORT_SLACK_WEBHOOK` 설정 시 동일 요약을 Slack으로 전송
	- 선택 옵션: `PROD_P0_REPORT_WARNING_SLACK_WEBHOOK` 설정 시 `warning` 상태일 때만 전용 경보 Slack 추가 전송
	- 선택 옵션: `PROD_P0_REPORT_WARNING_MENTIONS` 설정 시 warning 전용 Slack 경보에 멘션 체인을 함께 포함
	- 수동 실행 시 `dry_run=true`이면 summary만 생성하고 Slack 전송은 생략

## Operations Runbook
- File: `docs/deployment-runbook.md`
- Contains pre-check, deployment flow, rollback, and incident response steps.

## Incident Postmortem Template
- File: `.github/ISSUE_TEMPLATE/incident-postmortem.md`
- Use this template to record timeline, root cause, and prevention actions after incidents.