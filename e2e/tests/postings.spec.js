// @ts-check
const { test, expect } = require('@playwright/test');

const INST_EMAIL = `posting.inst.${Date.now()}@edulink.local`;
const INST_PASSWORD = 'PostInst123!';

/** 로그인 헬퍼 */
async function loginAs(page, email, password) {
  await page.goto('/');
  await page.locator('#loginEmail').fill(email);
  await page.locator('#loginPassword').fill(password);
  await page.locator('#loginBtn').click();
  await expect(page.locator('body')).toHaveClass(/view-web(app)?/, { timeout: 8_000 });
}

test.describe('Postings(공고) 섹션', () => {
  test.beforeAll(async ({ request }) => {
    // 기관 운영자 계정 생성
    await request.post('/auth/register', {
      data: { email: INST_EMAIL, password: INST_PASSWORD, role: 'institution' },
    });
  });

  test.beforeEach(async ({ page }) => {
    await loginAs(page, INST_EMAIL, INST_PASSWORD);
    // Postings 섹션으로 이동
    await page.locator('.rail-link[data-screen="postingsSection"]').click();
    await expect(page.locator('#postingsSection')).toBeVisible({ timeout: 6_000 });
  });

  test('공고 목록 섹션 렌더링', async ({ page }) => {
    await expect(page.locator('#postingsSection h2')).toBeVisible();
    // 필터 UI 노출 확인
    await expect(page.locator('#filterSubject')).toBeVisible();
    await expect(page.locator('#filterRegion')).toBeVisible();
  });

  test('과목 필터 선택', async ({ page }) => {
    await page.locator('#filterSubject').selectOption('math');
    // 필터 변경 후 선택값 유지 확인
    await expect(page.locator('#filterSubject')).toHaveValue('math');
  });

  test('지역 필터 입력', async ({ page }) => {
    await page.locator('#filterRegion').fill('Seoul');
    await expect(page.locator('#filterRegion')).toHaveValue('Seoul');
  });

  test('최소 급여 필터 입력', async ({ page }) => {
    await page.locator('#filterMinRate').fill('50000');
    await expect(page.locator('#filterMinRate')).toHaveValue('50000');
  });
});

// ─────────────────────────────────────────────
// Dashboard 통계 섹션
// ─────────────────────────────────────────────
test.describe('Dashboard 섹션', () => {
  const DASH_EMAIL = `dash.test.${Date.now()}@edulink.local`;
  const DASH_PASSWORD = 'DashTest123!';

  test.beforeAll(async ({ request }) => {
    await request.post('/auth/register', {
      data: { email: DASH_EMAIL, password: DASH_PASSWORD, role: 'instructor' },
    });
  });

  test.beforeEach(async ({ page }) => {
    await loginAs(page, DASH_EMAIL, DASH_PASSWORD);
    await page.locator('.rail-link[data-screen="dashboardSection"]').click();
    await expect(page.locator('#dashboardSection')).toBeVisible({ timeout: 6_000 });
  });

  test('대시보드 섹션 마운트 확인', async ({ page }) => {
    await expect(page.locator('#dashboardSection')).toBeVisible();
  });

  test('대시보드 API 응답 정상 (네트워크 확인)', async ({ page }) => {
    const token = await page.evaluate(() => localStorage.getItem('token'));
    expect(token).toBeTruthy();
    const response = await page.request.get('/dashboard/stats', {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 10_000,
    });
    expect(response.status()).toBe(200);
  });
});

// ─────────────────────────────────────────────
// Security(My Page) 섹션
// ─────────────────────────────────────────────
test.describe('보안 / My Page 섹션', () => {
  const SEC_EMAIL = `sec.test.${Date.now()}@edulink.local`;
  const SEC_PASSWORD = 'SecTest123!';

  test.beforeAll(async ({ request }) => {
    await request.post('/auth/register', {
      data: { email: SEC_EMAIL, password: SEC_PASSWORD, role: 'instructor' },
    });
  });

  test.beforeEach(async ({ page }) => {
    await loginAs(page, SEC_EMAIL, SEC_PASSWORD);
    await page.locator('.rail-link[data-screen="securitySection"]').click();
    await expect(page.locator('#securitySection')).toBeVisible({ timeout: 6_000 });
  });

  test('비밀번호 변경 폼 렌더링', async ({ page }) => {
    await expect(page.locator('#currentPassword')).toBeVisible();
    await expect(page.locator('#newPassword')).toBeVisible();
    await expect(page.locator('#changePasswordBtn')).toBeVisible();
  });

  test('계정 복구 폼 렌더링', async ({ page }) => {
    await expect(page.locator('#resetEmail')).toBeVisible();
    await expect(page.locator('#resetRequestBtn')).toBeVisible();
  });

  test('비밀번호 변경 - 현재 비밀번호 불일치 오류', async ({ page }) => {
    await page.locator('#currentPassword').fill('wrongCurrentPass!');
    await page.locator('#newPassword').fill('NewPass456!');
    await page.locator('#changePasswordBtn').click();

    await expect(page.locator('#securityStatus')).not.toBeEmpty({ timeout: 5_000 });
  });
});
