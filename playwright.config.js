// @ts-check
const { defineConfig, devices } = require('@playwright/test');

const baseURL = process.env.E2E_BASE_URL || 'http://localhost:8000';
const useRemoteServer = /^https?:\/\//.test(baseURL) && !/localhost|127\.0\.0\.1/.test(new URL(baseURL).hostname);
const actionTimeout = Number(process.env.E2E_ACTION_TIMEOUT || (useRemoteServer ? 30000 : 10000));
const navigationTimeout = Number(process.env.E2E_NAV_TIMEOUT || (useRemoteServer ? 45000 : 15000));

/**
 * EduLink Playwright E2E 설정
 * 백엔드 서버(Flask, port 8000)가 실행 중이어야 합니다.
 * 서버 기동: cd backend && python run.py
 */
module.exports = defineConfig({
  testDir: './e2e/tests',
  fullyParallel: false,           // SPA 단일 DB이므로 순차 실행
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'e2e/report', open: 'never' }],
  ],
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout,
    navigationTimeout,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],

  // Flask 서버 자동 기동 (이미 실행 중이면 재사용)
  webServer: useRemoteServer
    ? undefined
    : {
        command: 'python backend/run.py',
        url: 'http://localhost:8000/health',
        reuseExistingServer: true,
        timeout: 15_000,
        stdout: 'pipe',
        stderr: 'pipe',
      },
});
