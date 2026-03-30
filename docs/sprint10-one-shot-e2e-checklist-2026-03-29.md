# Sprint 10 One-Shot E2E Checklist (Real URL)

## Goal
- Execute exactly one final E2E run on real URL after Sprint 1-9 implementation freeze.
- Keep evidence artifacts for customer demo sign-off.

## Scope
- Environment: production-like real URL only
- Browser baseline: chromium
- Test suite: Playwright full suite (`e2e/tests`)
- Policy: no repeated ad-hoc reruns unless a release-blocking defect is fixed

## Preconditions
- Release candidate code is pushed and deployed.
- Demo seed DB is prepared and validated.
- Social login mode is configured for target environment.
- Monitoring/alerting channels are active.

## Command
```bash
powershell -ExecutionPolicy Bypass -File scripts/run-one-shot-e2e.ps1 -BaseUrl https://your-real-demo-url
```

## Pass Criteria
- Playwright exits with code 0.
- No critical auth/session/payment flow regression.
- HTML report exists at `e2e/report/index.html`.
- JSON result file is generated in `e2e/`.

## Evidence to Archive
- `e2e/report/index.html`
- one-shot JSON result file
- deployment revision information
- issue log for any non-blocking defects

Archive helper command:
```bash
powershell -ExecutionPolicy Bypass -File scripts/archive-one-shot-evidence.ps1 -RcVersion v2.0.0-rc1 -BaseUrl https://your-real-demo-url -ResultFile e2e/chromium-oneshot.json
```

## If Failed
- Record failing scenario and attach trace/video from Playwright output.
- Fix only release-blocking defects.
- Re-run one-shot only after explicit go/no-go approval.

## Approval Log
- QA owner:
- Product owner:
- Engineering owner:
- Executed at (UTC):
- Result: PASS / FAIL
