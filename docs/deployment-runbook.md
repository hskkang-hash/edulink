# EduLink Deployment Runbook

## Scope
- Environment: staging, production
- Pipeline: GitHub Actions workflows
  - `.github/workflows/deploy-staging.yml`
  - `.github/workflows/deploy-production.yml`

## 1) Pre-Deployment Checklist
- Confirm CI green: tests, lint, security scan
- Confirm target version/tag
  - production: `vX.Y.Z` format
- Confirm environment secrets are set
- Confirm database backup exists (production)
- Confirm incident channel on-call availability

## 2) Standard Deployment Flow
1. Trigger workflow (push tag or manual dispatch)
2. Verify environment approval gate completion
3. Watch checklist logs in workflow run
4. Confirm health and metrics smoke checks passed
5. Confirm Slack deploy success notification

## 3) Post-Deployment Validation
- API health check (`/health`) returns 200
- Metrics endpoint (`/metrics`) returns 200
- Optional role smoke result is PASS
- Confirm latest release note includes deployment validation section

## 4) Rollback Procedure
1. Identify failed workflow run and target previous commit
2. In server shell:
   - checkout previous commit
   - `docker compose -f docker/docker-compose.yml up -d --build`
3. Re-run health check and metrics check
4. Confirm rollback notification is sent
5. Open incident ticket and attach run URL

## 5) Incident Response
- Severity levels:
  - Sev-1: service unavailable, auth broken, data integrity risk
  - Sev-2: partial outage or degraded performance
- Communication:
  - Slack incident channel
  - PagerDuty (if configured)
- Required artifacts:
  - workflow run URL
  - tag/commit SHA
  - health check output
  - rollback verification output

## 6) Recovery Completion Criteria
- Health and metrics restored
- Critical endpoints functional
- Error rate normalized
- Incident summary published
