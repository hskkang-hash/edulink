// @ts-check
/**
 * EduLink Demo Screenshot Capture
 * 실 URL(https://edulinks.pro) 기준으로 주요 화면을 캡처합니다.
 * 실행: $env:E2E_BASE_URL="https://edulinks.pro"; npx playwright test e2e/tests/demo-screenshots.spec.js --project=chromium
 *
 * QA 계정은 프론트엔드 오프라인 데모 모드(qa.*@edulink.local)를 사용하므로
 * 백엔드 API 불가 상황에서도 전체 화면 캡처가 가능합니다.
 */
const { test, expect } = require('@playwright/test');
const path = require('path');

const QA_PASSWORD = 'QaPass123!';

const ROLES = {
  instructor: 'qa.instructor@edulink.local',
  institution: 'qa.institution@edulink.local',
  district: 'qa.district@edulink.local',
  admin: 'qa.admin@edulink.local',
};

const SCREENSHOT_DIR = 'e2e/screenshots';

/**
 * @param {import('@playwright/test').Page} page
 * @param {string} email
 */
async function loginAs(page, email) {
  await page.goto('/');
  await page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {});
  await expect(page.locator('#loginSection')).toBeVisible({ timeout: 20000 });
  await page.locator('#loginEmail').fill(email);
  await page.locator('#loginPassword').fill(QA_PASSWORD);
  await page.locator('#loginBtn').click();
  // Accept either view-webapp or view-web
  await expect(page.locator('body')).toHaveClass(/view-web(app)?/, { timeout: 30000 });
}

/**
 * @param {import('@playwright/test').Page} page
 * @param {string} screenId
 */
async function navigateTo(page, screenId) {
  const link = page.locator(`.rail-link[data-screen="${screenId}"]`).first();
  const isVisible = await link.isVisible();
  if (isVisible) {
    await link.click();
    await page.waitForTimeout(800);
  }
}

/**
 * @param {import('@playwright/test').Page} page
 * @param {string} name
 */
async function snap(page, name) {
  await page.waitForTimeout(600);
  await page.screenshot({
    path: `${SCREENSHOT_DIR}/${name}.png`,
    fullPage: false,
  });
}

// ─── 01. 랜딩 / 로그인 화면 ───────────────────────────────────────────────────
test('01_landing_login', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/');
  await page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {});
  await snap(page, '01_landing_login');
});

// ─── 02. 강사 대시보드 ─────────────────────────────────────────────────────────
test('02_instructor_dashboard', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await loginAs(page, ROLES.instructor);
  await navigateTo(page, 'dashboardSection');
  await snap(page, '02_instructor_dashboard');
});

// ─── 03. 강사 공고 탐색 ────────────────────────────────────────────────────────
test('03_instructor_postings', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await loginAs(page, ROLES.instructor);
  await navigateTo(page, 'postingsSection');
  await snap(page, '03_instructor_postings');
});

// ─── 04. 강사 정산 / 세금 ─────────────────────────────────────────────────────
test('04_instructor_fintech', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await loginAs(page, ROLES.instructor);
  // fintechSection 또는 taxSection
  await navigateTo(page, 'fintechSection');
  const hasFintech = await page.locator('#fintechSection').isVisible();
  if (!hasFintech) await navigateTo(page, 'taxSection');
  await snap(page, '04_instructor_fintech');
});

// ─── 05. 강사 마이페이지 / 자격서류 ──────────────────────────────────────────
test('05_instructor_mypage', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await loginAs(page, ROLES.instructor);
  await navigateTo(page, 'securitySection');
  await snap(page, '05_instructor_mypage');
});

// ─── 06. 기관 대시보드 ─────────────────────────────────────────────────────────
test('06_institution_dashboard', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await loginAs(page, ROLES.institution);
  await navigateTo(page, 'dashboardSection');
  await snap(page, '06_institution_dashboard');
});

// ─── 07. 기관 공고 관리 ────────────────────────────────────────────────────────
test('07_institution_postings', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await loginAs(page, ROLES.institution);
  await navigateTo(page, 'createPostingSection');
  await snap(page, '07_institution_create_posting');
});

// ─── 08. 기관 지원자 관리 ──────────────────────────────────────────────────────
test('08_institution_applicants', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await loginAs(page, ROLES.institution);
  await navigateTo(page, 'applicationsSection');
  await snap(page, '08_institution_applicants');
});

// ─── 09. 기관 정산 ─────────────────────────────────────────────────────────────
test('09_institution_settlements', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await loginAs(page, ROLES.institution);
  await navigateTo(page, 'taxSection');
  await snap(page, '09_institution_settlements');
});

// ─── 10. 기관 네트워크 ─────────────────────────────────────────────────────────
test('10_institution_network', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await loginAs(page, ROLES.institution);
  await navigateTo(page, 'networkSection');
  await snap(page, '10_institution_network');
});

// ─── 11. 교육청 대시보드 ──────────────────────────────────────────────────────
test('11_district_dashboard', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await loginAs(page, ROLES.district);
  await navigateTo(page, 'dashboardSection');
  await snap(page, '11_district_dashboard');
});

// ─── 12. 교육청 인사이트 ──────────────────────────────────────────────────────
test('12_district_insights', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await loginAs(page, ROLES.district);
  await navigateTo(page, 'adminInsightsSection');
  await snap(page, '12_district_insights');
});

// ─── 13. 관리자 대시보드 ──────────────────────────────────────────────────────
test('13_admin_dashboard', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await loginAs(page, ROLES.admin);
  await navigateTo(page, 'dashboardSection');
  await snap(page, '13_admin_dashboard');
});

// ─── 14. 관리자 인사이트 / 역할 매트릭스 ────────────────────────────────────
test('14_admin_role_matrix', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await loginAs(page, ROLES.admin);
  await navigateTo(page, 'roleFeatureMatrixSection');
  await snap(page, '14_admin_role_matrix');
});

// ─── 15. 모바일 뷰 (강사 대시보드) ───────────────────────────────────────────
test('15_mobile_instructor_dashboard', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await loginAs(page, ROLES.instructor);
  // On mobile, after login we are already at dashboardSection — just snap
  await expect(page.locator('#dashboardSection')).toBeVisible({ timeout: 10000 });
  await snap(page, '15_mobile_instructor_dashboard');
});
