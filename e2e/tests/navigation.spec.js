// @ts-check
const { test, expect } = require('@playwright/test');

const TEST_EMAIL = `nav.test.${Date.now()}@edulink.local`;
const TEST_PASSWORD = 'NavTest123!';

test.describe('사이드바 내비게이션', () => {
  // 테스트 계정을 describe 스코프에서 한 번만 생성 후 로그인
  test.beforeAll(async ({ request }) => {
    await request.post('/auth/register', {
      data: { email: TEST_EMAIL, password: TEST_PASSWORD, role: 'instructor' },
    });
  });

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.locator('#loginEmail').fill(TEST_EMAIL);
    await page.locator('#loginPassword').fill(TEST_PASSWORD);
    await page.locator('#loginBtn').click();
    await expect(page.locator('body')).toHaveClass(/view-webapp/, { timeout: 8_000 });
  });

  test('Overview(Dashboard) 탭 진입', async ({ page }) => {
    await page.locator('.rail-link[data-screen="dashboardSection"]').click();
    await expect(page.locator('#dashboardSection')).toBeVisible({ timeout: 6_000 });
  });

  test('Analytics(Postings) 탭 진입', async ({ page }) => {
    await page.locator('.rail-link[data-screen="postingsSection"]').click();
    await expect(page.locator('#postingsSection')).toBeVisible({ timeout: 6_000 });
  });

  test('Settlements(Tax) 탭 진입', async ({ page }) => {
    await page.locator('.rail-link[data-screen="taxSection"]').click();
    await expect(page.locator('#taxSection')).toBeVisible({ timeout: 6_000 });
  });

  test('Applicants 탭 진입', async ({ page }) => {
    await page.locator('.rail-link[data-screen="applicationsSection"]').click();
    await expect(page.locator('#applicationsSection')).toBeVisible({ timeout: 6_000 });
  });

  test('My Profile 탭 진입', async ({ page }) => {
    await page.locator('.rail-link[data-screen="instructorOnboardingSection"]').click();
    await expect(page.locator('#instructorOnboardingSection')).toBeVisible({ timeout: 6_000 });
  });

  test('Network 탭 진입', async ({ page }) => {
    await page.locator('.rail-link[data-screen="networkSection"]').click();
    await expect(page.locator('#networkSection')).toBeVisible({ timeout: 6_000 });
  });

  test('My Page 탭 진입', async ({ page }) => {
    await page.locator('.rail-link[data-screen="securitySection"]').click();
    await expect(page.locator('#securitySection')).toBeVisible({ timeout: 6_000 });
  });
});
