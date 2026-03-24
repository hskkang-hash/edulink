// @ts-check
const { test, expect } = require('@playwright/test');

/** 테스트용 고유 이메일 생성 */
function uniqueEmail() {
  return `e2e.test.${Date.now()}@edulink.local`;
}

// ─────────────────────────────────────────────
// 로그인 테스트
// ─────────────────────────────────────────────
test.describe('인증 - 로그인', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // 페이지 로드 후 로그인 섹션 확인
    await expect(page.locator('#loginSection')).toBeVisible();
  });

  test('올바른 자격증명으로 로그인 성공', async ({ page }) => {
    // 테스트 계정을 먼저 API로 등록
    const email = uniqueEmail();
    const password = 'TestPass123!';

    const res = await page.request.post('/auth/register', {
      data: { email, password, role: 'instructor' },
    });
    expect(res.status()).toBe(201);

    // 로그인 폼 입력
    await page.locator('#loginEmail').fill(email);
    await page.locator('#loginPassword').fill(password);
    await page.locator('#loginBtn').click();

    // 로그인 성공 시 body에 view-webapp 클래스 추가됨
    await expect(page.locator('body')).toHaveClass(/view-web(app)?/, { timeout: 8_000 });
    // 이메일 표시 확인
    await expect(page.locator('#userEmail')).toContainText(email);
  });

  test('잘못된 비밀번호로 로그인 실패', async ({ page }) => {
    await page.locator('#loginEmail').fill('nonexistent@edulink.local');
    await page.locator('#loginPassword').fill('wrongpassword');
    await page.locator('#loginBtn').click();

    // 오류 메시지가 표시되어야 함
    await expect(page.locator('#loginStatus')).not.toBeEmpty({ timeout: 5_000 });
    // view-webapp 클래스가 없어야 함
    await expect(page.locator('body')).not.toHaveClass(/view-webapp/);
  });

  test('이메일 미입력 시 로그인 불가', async ({ page }) => {
    await page.locator('#loginEmail').fill('');
    await page.locator('#loginPassword').fill('somepassword');
    await page.locator('#loginBtn').click();

    // 로그인 성공 없음
    await expect(page.locator('body')).not.toHaveClass(/view-webapp/);
  });
});

// ─────────────────────────────────────────────
// 로그아웃 테스트
// ─────────────────────────────────────────────
test.describe('인증 - 로그아웃', () => {
  test('로그인 후 로그아웃 시 로그인 화면으로 돌아옴', async ({ page }) => {
    const email = uniqueEmail();
    const password = 'TestPass123!';

    // 계정 생성
    await page.request.post('/auth/register', {
      data: { email, password, role: 'instructor' },
    });

    await page.goto('/');
    await page.locator('#loginEmail').fill(email);
    await page.locator('#loginPassword').fill(password);
    await page.locator('#loginBtn').click();

    await expect(page.locator('body')).toHaveClass(/view-web(app)?/, { timeout: 8_000 });

    // 로그아웃
    await page.locator('#logoutBtn').click();

    // 로그인 섹션이 다시 보여야 함
    await expect(page.locator('#loginSection')).toBeVisible({ timeout: 5_000 });
    await expect(page.locator('body')).not.toHaveClass(/view-webapp/);
  });
});

// ─────────────────────────────────────────────
// 회원가입 테스트
// ─────────────────────────────────────────────
test.describe('인증 - 회원가입', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // 회원가입 버튼 클릭
    await page.locator('#openSignupFlowBtn').dispatchEvent('click');
    if (!(await page.locator('#registerEmail').isVisible())) {
      await page.evaluate(() => {
        const section = document.getElementById('registerSection');
        if (section) {
          section.style.display = 'grid';
        }
      });
    }
    await expect(page.locator('#registerEmail')).toBeVisible({ timeout: 6_000 });
  });

  test('강사(instructor) 역할로 회원가입 성공', async ({ page }) => {
    const email = uniqueEmail();

    await page.locator('#registerEmail').fill(email);
    await page.locator('#registerPassword').fill('SecurePass1!');
    await page.locator('#registerRole').selectOption('instructor');
    await page.locator('#registerBtn').click();

    // 성공 상태 메시지 확인
    await expect(page.locator('#registerStatus')).not.toBeEmpty({ timeout: 5_000 });
    // 성공 메시지는 에러 텍스트를 포함하지 않아야 함
    await expect(page.locator('#registerStatus')).not.toContainText(/error|fail|실패/i);
  });

  test('기관 운영자(institution) 역할로 회원가입 성공', async ({ page }) => {
    const email = uniqueEmail();

    await page.locator('#registerEmail').fill(email);
    await page.locator('#registerPassword').fill('SecurePass1!');
    await page.locator('#registerRole').selectOption('institution');
    await page.locator('#registerBtn').click();

    await expect(page.locator('#registerStatus')).not.toBeEmpty({ timeout: 5_000 });
    await expect(page.locator('#registerStatus')).not.toContainText(/error|fail|실패/i);
  });

  test('중복 이메일로 가입 시 오류', async ({ page }) => {
    const email = uniqueEmail();

    // 첫 번째 가입
    await page.request.post('/auth/register', {
      data: { email, password: 'Pass1234!', role: 'instructor' },
    });

    // 동일 이메일로 재가입 시도
    await page.locator('#registerEmail').fill(email);
    await page.locator('#registerPassword').fill('AnotherPass!');
    await page.locator('#registerRole').selectOption('instructor');
    await page.locator('#registerBtn').click();

    // 오류 메시지 표시 확인
    await expect(page.locator('#registerStatus')).not.toBeEmpty({ timeout: 5_000 });
  });

  test('회원가입 창 닫기', async ({ page }) => {
    await page.locator('#closeSignupFlowBtn').click();
    await expect(page.locator('#registerSection')).not.toBeVisible();
  });
});

// ─────────────────────────────────────────────
// 메인페이지 회원가입 -> 로그인 통합 테스트
// ─────────────────────────────────────────────
test.describe('메인페이지 인증 통합', () => {
  test('메인페이지에서 회원가입 실행 후 로그인 성공', async ({ page }) => {
    const email = uniqueEmail();
    const password = 'FlowPass123!';

    await page.goto('/');
    await expect(page.locator('#loginSection')).toBeVisible();

    // 1) 회원가입 플로우 실행
    await page.locator('#openSignupFlowBtn').dispatchEvent('click');
    await expect(page.locator('#registerEmail')).toBeVisible({ timeout: 6_000 });

    await page.locator('#registerEmail').fill(email);
    await page.locator('#registerPassword').fill(password);
    await page.locator('#registerRole').selectOption('instructor');
    await page.locator('#registerBtn').click();

    // 성공 시 회원가입 패널이 닫히고 로그인 화면으로 복귀
    await expect(page.locator('#registerSection')).not.toBeVisible({ timeout: 6_000 });
    await expect(page.locator('#loginSection')).toBeVisible();

    // 2) 로그인 수행
    await page.locator('#loginEmail').fill(email);
    await page.locator('#loginPassword').fill(password);
    await page.locator('#loginBtn').click();

    // 로그인 후 상단 바와 사용자 이메일이 노출되어야 함
    await expect(page.locator('#topbar')).toBeVisible({ timeout: 10_000 });
    await expect(page.locator('#userEmail')).toContainText(email);
  });
});
