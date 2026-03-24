// @ts-check
const { test, expect } = require('@playwright/test');

const QA_PASSWORD = 'QaPass123!';

const USERS = {
  instructor: 'qa.instructor@edulink.local',
  institution: 'qa.institution@edulink.local',
  district: 'qa.district@edulink.local',
  admin: 'qa.admin@edulink.local',
};

/**
 * @param {import('@playwright/test').Page} page
 * @param {string} email
 * @param {string} password
 */
async function loginAs(page, email, password = QA_PASSWORD) {
  await page.goto('/');
  await expect(page.locator('#loginSection')).toBeVisible();
  await page.locator('#loginEmail').fill(email);
  await page.locator('#loginPassword').fill(password);
  await page.locator('#loginBtn').click();
  await expect(page.locator('body')).toHaveClass(/view-web(app)?/, { timeout: 10000 });
  await expect(page.locator('#userEmail')).toContainText(email);
}

test.describe('역할별 로그인 + 핵심 기능 플로우', () => {
  test('강사: 가용일정 저장 + 핀테크 진입', async ({ page }) => {
    await loginAs(page, USERS.instructor);

    await page.locator('.rail-link[data-screen="availabilitySection"]').click();
    await expect(page.locator('#availabilitySection')).toBeVisible();

    await page.locator('#availDay').selectOption('Wed');
    await page.locator('#availStart').fill('18:00');
    await page.locator('#availEnd').fill('19:00');
    await page.locator('#availabilitySection button:has-text("가용 슬롯 저장")').click();
    await expect(page.locator('#availabilityStatus')).toContainText(/저장|saved/i);

    await page.locator('.rail-link[data-screen="fintechSection"]').click();
    await expect(page.locator('#fintechSection')).toBeVisible();
    await page.locator('#fintechSection button:has-text("선정산 시뮬레이션")').click();
    await expect(page.locator('#fintechStatus')).not.toBeEmpty();
  });

  test('기관: 즉시예약 + 강사비교 진입', async ({ page }) => {
    await loginAs(page, USERS.institution);

    await page.locator('.rail-link[data-screen="instantBookingSection"]').click();
    await expect(page.locator('#instantBookingSection')).toBeVisible();
    await expect(page.locator('#instantBookingStatus')).not.toBeEmpty();

    await page.locator('.rail-link[data-screen="compareSection"]').first().click();
    await expect(page.locator('#compareSection')).toBeVisible();
    await page.locator('#compareSection button:has-text("비교표 생성")').click();
    await expect(page.locator('#compareStatus')).not.toBeEmpty();
  });

  test('교육청: 커버리지 맵 진입', async ({ page }) => {
    await loginAs(page, USERS.district);

    await page.locator('.rail-link[data-screen="coverageMapSection"]').first().click();
    await expect(page.locator('#coverageMapSection')).toBeVisible();
    await page.locator('#coverageMapSection button:has-text("맵/리스트 로드")').click();
    await expect(page.locator('#coverageMapStatus')).not.toBeEmpty();
  });

  test('운영자: MLM 게이지 + 핀테크 진입', async ({ page }) => {
    await loginAs(page, USERS.admin);

    await page.locator('.rail-link[data-screen="mlmGaugeSection"]').first().click();
    await expect(page.locator('#mlmGaugeSection')).toBeVisible();
    await page.locator('#mlmGaugeSection button:has-text("게이지 새로고침")').click();
    await expect(page.locator('#mlmGaugeStatus')).not.toBeEmpty();

    await page.locator('.rail-link[data-screen="fintechSection"]').click();
    await expect(page.locator('#fintechSection')).toBeVisible();
  });
});
