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
 */
async function loginAs(page, email) {
  await page.goto('/');
  await expect(page.locator('#loginSection')).toBeVisible();
  await page.locator('#loginEmail').fill(email);
  await page.locator('#loginPassword').fill(QA_PASSWORD);
  await page.locator('#loginBtn').click();
  await expect(page.locator('body')).toHaveClass(/view-web(app)?/, { timeout: 15000 });
  await expect(page.locator('#userEmail')).toContainText(email);
  await expect(page.locator('#globalQuickbar')).toBeVisible();
  await expect(page.locator('#globalLogoutBtn')).toBeVisible();
}

/**
 * @param {import('@playwright/test').Page} page
 */
async function clickAllVisibleSideMenus(page) {
  const screenIds = await page.locator('.side-rail .rail-link[data-screen]').evaluateAll((nodes) => {
    return nodes
      .filter((node) => {
        const element = /** @type {HTMLElement} */ (node);
        const style = window.getComputedStyle(element);
        return style.display !== 'none' && style.visibility !== 'hidden';
      })
      .map((node) => node.getAttribute('data-screen'))
      .filter(Boolean);
  });

  for (const screenId of [...new Set(screenIds)]) {
    const link = page.locator(`.side-rail .rail-link[data-screen="${screenId}"]`).first();
    await expect(link).toBeVisible();
    await page.evaluate((id) => { if (typeof activateScreen === 'function') activateScreen(id); }, screenId);
    await page.waitForTimeout(500);
    await expect(page.locator(`#${screenId}`)).toBeVisible({ timeout: 10000 });
    await expect(page.locator('#globalLogoutBtn')).toBeVisible();
  }
}

test.describe('실사용자 메뉴 전수 점검', () => {
  for (const [role, email] of Object.entries(USERS)) {
    test(`${role}: 모든 메뉴 이동 후 글로벌 로그아웃 가능`, async ({ page }) => {
      await loginAs(page, email);
      await clickAllVisibleSideMenus(page);

      await page.evaluate(() => { if (typeof activateScreen === 'function') activateScreen('dashboardSection'); });
      await page.waitForTimeout(300);
      await expect(page.locator('#dashboardSection')).toBeVisible();

      await expect(page.locator('#globalLogoutBtn')).toBeVisible();
      await page.locator('#globalLogoutBtn').click();

      await expect(page.locator('#loginSection')).toBeVisible();
      await expect(page.locator('body')).not.toHaveClass(/view-webapp/);
    });
  }
});