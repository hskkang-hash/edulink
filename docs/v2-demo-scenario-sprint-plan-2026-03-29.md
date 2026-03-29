# EduLink v2.0 Demo Sprint Plan (Scenario-Based)

Date: 2026-03-29  
Scope: Demo-ready v2.0 with convenience-focused flows, Google/Kakao login, and 1000-user data scale

## 1. Demo User Scenario Backbone

Primary scenario used for planning:
1. Instructor signs in with Google/Kakao and completes profile in less than 3 minutes.
2. School or institution posts a class request from a template in less than 2 minutes.
3. Instructor applies, institution compares candidates on one board, and approves.
4. Session is scheduled, checked in, completed, and reviewed.
5. District and admin dashboards monitor quality, utilization, and risk in one screen.
6. System operators validate service health and launch one-shot real URL e2e before demo.

Convenience principles reflected:
- Minimize clicks for the top 3 tasks per role.
- Use role-specific dashboards with actionable cards.
- Prefer defaults and templates over manual input.
- Keep login friction low using social providers.

## 2. 10 Sprint Development Plan

### Sprint 1 - Baseline and V2 feature flag
- Freeze current baseline, define rollback points, and introduce v2 flags.
- Add demo/staging runtime profile separate from production.
- Exit criteria: One command can switch between v1 and v2 behavior.

### Sprint 2 - Identity foundation and social login
- Add Google/Kakao social login API contract and account-linking model.
- Keep email/password flow as fallback.
- Exit criteria: New user can sign in by provider and receive bearer token.

### Sprint 3 - Instructor onboarding convenience
- Implement quick profile completion, status badges, and required docs checklist.
- Add profile completeness score for dashboard.
- Exit criteria: 80%+ profile completion possible in one page.

### Sprint 4 - Institution/school posting acceleration
- Add posting templates, recurrence defaults, and smart field suggestions.
- Add draft/save and one-click repost behavior.
- Exit criteria: New posting creation under 2 minutes.

### Sprint 5 - Candidate comparison board
- Implement compare view with profile, rating, availability, and region fit.
- Support batch approve/reject actions.
- Exit criteria: Institution can finalize a candidate without leaving comparison view.

### Sprint 6 - Session operations and evidence
- Strengthen session check-in, complete, and event timeline.
- Add structured teaching note and follow-up action fields.
- Exit criteria: Session lifecycle is fully traceable.

### Sprint 7 - Reputation and quality metrics
- Build rating aggregates, completion/no-show signals, and response-time metrics.
- Expose quality KPIs in institution and district dashboard.
- Exit criteria: Score and evidence are visible together.

### Sprint 8 - Finance and settlement clarity
- Improve settlement summary (approved/pending/paid), export quality, and audit trail.
- Add monthly indicators for institutions and admins.
- Exit criteria: Finance summary is demo-ready and CSV-exportable.

### Sprint 9 - Scale pass for 1000 users
- Seed and validate with 1000 users, realistic postings/apps/sessions/reviews.
- Tune dashboard queries and high-traffic endpoints.
- Exit criteria: Core role dashboards respond within acceptable demo latency.

### Sprint 10 - Demo hardening and one-shot e2e
- Freeze feature scope, run full regression once on the real URL, and publish runbook.
- Fix critical defects only.
- Exit criteria: Single final e2e pass on real URL is green.

## 3. Demo Data Blueprint (1000 Users)

Fixed role counts:
- Instructors: 10
- Schools: 5
- Institutions: 5
- System operators: 2 (admin role)
- Students/learners: 978

Content and activity targets for demo realism:
- Postings: 40
- Applications: multi-applicant per posting
- Approved applications: at least 1 per posting
- Sessions: mix of completed and scheduled
- Reviews: attached to completed sessions

## 4. Final Test Strategy (Real URL, one-time e2e)

Policy requested for demo:
- Do not run distributed e2e continuously during implementation.
- Execute one consolidated e2e run only after final development completion.
- Run target: real deployed URL (not localhost-only dry run).

Execution checklist:
1. Freeze build artifacts and seed demo data.
2. Run smoke checks (`/health`, auth, dashboard stats).
3. Run full Playwright e2e suite once against real URL.
4. Archive reports and defect log.
5. Apply only blocker fixes, then rerun once if required.

## 5. Implemented assets in this workspace

- Social login endpoint for Google/Kakao in backend auth layer.
- Demo seed script that generates 1000 users and role-specific activity data.
- This scenario-driven sprint plan for customer demo communication.
