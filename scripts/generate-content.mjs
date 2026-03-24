import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(process.cwd());
const contentDir = resolve(root, "frontend", "content");
const hubPath = resolve(root, "frontend", "content-hub.html");

mkdirSync(contentDir, { recursive: true });

const articles = [
  ["instructor-onboarding-checklist", "Instructor Onboarding Checklist", "A practical checklist from account creation to first class assignment."],
  ["school-posting-template-guide", "School Posting Template Guide", "How institutions can publish complete and attractive class postings."],
  ["application-screening-rubric", "Application Screening Rubric", "A fair and repeatable scoring model for applicant reviews."],
  ["session-checkin-best-practice", "Session Check-in Best Practice", "Reliable check-in operations with location and time validation."],
  ["lesson-log-writing-tips", "Lesson Log Writing Tips", "How to write concise and useful lesson records for operations."],
  ["monthly-settlement-read-guide", "How to Read Monthly Settlements", "Understand gross, withholding, and net payout quickly."],
  ["tax-refund-flow-explained", "Tax Refund Flow Explained", "From estimate to submission and status tracking in one flow."],
  ["institution-dashboard-kpi", "Institution Dashboard KPI Guide", "Key operational indicators institutions should monitor daily."],
  ["district-budget-monitoring", "District Budget Monitoring Guide", "How to interpret budget utilization and coverage metrics."],
  ["mlm-compliance-35-rule", "MLM 35 Percent Compliance Rule", "Operational checkpoints for keeping bonus payouts compliant."],
  ["sos-emergency-matching-playbook", "SOS Emergency Matching Playbook", "A quick response process for urgent instructor vacancies."],
  ["review-quality-criteria", "Review Quality Criteria", "Rules for trustworthy and actionable reviews."],
  ["contract-signing-workflow", "E-Contract Signing Workflow", "Steps from contract draft to signature completion."],
  ["escrow-payment-lifecycle", "Escrow Payment Lifecycle", "Prepay, release, and refund handling across scenarios."],
  ["account-security-baseline", "Account Security Baseline", "A baseline for password, session, and recovery controls."],
  ["incident-response-runbook", "Incident Response Runbook Basics", "A simple framework for outage triage and communication."],
  ["mobile-ux-accessibility", "Mobile UX Accessibility Checklist", "Readable and accessible mobile patterns for core screens."],
  ["adsense-policy-operation", "AdSense Policy Operations Guide", "How to prevent invalid traffic and policy violations."],
  ["customer-support-sla", "Customer Support SLA Design", "How to classify requests and define response targets."],
  ["release-readiness-check", "Release Readiness Checklist", "Final verification before production deployment."],
];

const articleTemplate = (title, summary) => `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title} | EduLink</title>
  <meta name="description" content="${summary}">
  <style>
    body{font-family:Segoe UI,Arial,sans-serif;max-width:900px;margin:40px auto;padding:0 16px;line-height:1.8;color:#1f2937}
    h1,h2{color:#111827}
    .meta{font-size:13px;color:#6b7280}
    .box{border:1px solid #e5e7eb;background:#f9fafb;border-radius:10px;padding:14px}
    a{color:#2563eb}
  </style>
</head>
<body>
  <p class="meta">Category: EduLink Operations | Updated: 2026-03-24</p>
  <h1>${title}</h1>
  <p>${summary}</p>
  <h2>Key Points</h2>
  <div class="box">
    <p>1. Define clear start and finish conditions from the user perspective.</p>
    <p>2. Provide recovery paths for failure, permission errors, and network issues.</p>
    <p>3. Keep action logs and ownership metadata for auditability.</p>
  </div>
  <h2>Execution Sequence</h2>
  <p>Requirement review -> screen design -> API integration -> E2E validation -> operations update.</p>
  <p><a href="/content-hub.html">Go to Content Hub</a> | <a href="/">Back to Home</a></p>
</body>
</html>
`;

for (const [slug, title, summary] of articles) {
  const filePath = resolve(contentDir, `${slug}.html`);
  writeFileSync(filePath, articleTemplate(title, summary), "utf8");
}

const links = articles
  .map(([slug, title, summary]) => `    <li><a href="/content/${slug}.html">${title}</a> - ${summary}</li>`)
  .join("\n");

const hubHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Content Hub | EduLink</title>
  <meta name="description" content="Operational guides for instructors, institutions, districts, and admins.">
  <style>
    body{font-family:Segoe UI,Arial,sans-serif;max-width:980px;margin:40px auto;padding:0 16px;line-height:1.75;color:#1f2937}
    h1{color:#111827}
    ul{padding-left:18px}
    li{margin:8px 0}
    a{color:#2563eb}
    .meta{font-size:13px;color:#6b7280}
  </style>
</head>
<body>
  <p class="meta">EduLink Content Hub | 20 public documents</p>
  <h1>EduLink Operations Content Hub</h1>
  <p>Indexable guides for core product operations and service quality.</p>
  <ul>
${links}
  </ul>
  <p><a href="/">Back to Home</a></p>
</body>
</html>
`;

writeFileSync(hubPath, hubHtml, "utf8");
console.log(`Generated ${articles.length} articles and content hub.`);
