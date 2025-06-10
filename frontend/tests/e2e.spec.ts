import { test, expect, request, Page } from '@playwright/test';
import { API_PATHS } from '../src/api/constants';
import { waitForHighlight } from './utils/waitForHighlight';

const FRONTEND_URL = process.env.VITE_FRONTEND_URL as string;
const API_BASE_URL = process.env.VITE_API_URL as string;
const API_VERSION = process.env.VITE_API_VERSION as string;

const COMMON_HEADERS = {
  'Content-Type': 'application/json',
  Accept: 'application/json, text/plain, */*',
};

async function createSession(apiContext: any, testName: string) {
  const name = `테스트 세션 - ${testName} - ${Date.now()}`;
  console.log('세션 생성 요청 시작');
  const res = await apiContext.post(`${API_BASE_URL}/api/${API_VERSION}${API_PATHS.SESSIONS}`, {
    data: { name },
    headers: COMMON_HEADERS,
  });
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  console.log('세션 생성 완료. ID:', data.id);
  return data;
}

async function deleteAllSessions(apiContext: any) {
  const res = await apiContext.get(`${API_BASE_URL}/api/${API_VERSION}${API_PATHS.SESSIONS}`, {
    headers: COMMON_HEADERS,
  });
  if (!res.ok()) return;
  const sessions = await res.json();
  for (const s of sessions) {
    await apiContext.delete(`${API_BASE_URL}/api/${API_VERSION}${API_PATHS.SESSION(s.id)}`, {
      headers: COMMON_HEADERS,
    });
  }
}

async function selectSession(page: Page, id: number) {
  const sessionSelector = `[data-testid="session-${id}"]`;
  const sessionList = page.locator('[data-testid="session-list"]');
  const targetSession = sessionList.locator(sessionSelector);

  console.log('Waiting for session to appear in session list:', sessionSelector);
  await expect(targetSession).toBeVisible({ timeout: 90000 });

  await targetSession.click();
  console.log('session-' + id + ' 선택 완료');
  await expect(targetSession).toHaveClass(/bg-blue-50/);
  await expect(page.locator('[data-testid="prompt-input"]')).toBeEnabled();
}

test.describe('EchoPrompt E2E', () => {
  let apiContext: any;

  test.beforeAll(async () => {
    apiContext = await request.newContext({ extraHTTPHeaders: COMMON_HEADERS });
    await deleteAllSessions(apiContext);
  });

  test.afterAll(async () => {
    await apiContext.dispose();
  });

  test.beforeEach(async ({ page }, testInfo) => {
    await page.goto(FRONTEND_URL);
    const session = await createSession(apiContext, testInfo.title);
    await page.waitForTimeout(1500);
    await page.reload();
    await page.waitForTimeout(1000);
    await selectSession(page, session.id);
  });

  test('send message and receive response', async ({ page }) => {
    const input = page.locator('[data-testid="prompt-input"]');
    const cities = [
      'New York',
      'London',
      'Tokyo',
      'Paris',
      'Cairo',
      'Sydney',
      'Moscow',
      'Toronto',
      'Berlin',
      'Seoul',
    ];
    const [cityA, cityB] = [...cities].sort(() => 0.5 - Math.random()).slice(0, 2);
    const message = `${cityA}에서 ${cityB}까지의 거리는 얼마인가요?`;

    await input.fill(message);
    console.log('사용자 메시지 입력 및 전송');
    await input.press('Enter');

    await page.waitForTimeout(4500);

    console.log('하이라이팅 감지 시작');
    await waitForHighlight(page, message);
    const assistant = page.locator('[data-testid^="message-assistant-"]').first();
    await expect(assistant).toBeVisible();
  });

  test('semantic search highlights result', async ({ page }) => {
    const input = page.locator('[data-testid="prompt-input"]');
    const msg = '하이라이트 테스트 메시지';

    await input.fill(msg);
    console.log('사용자 메시지 입력 및 전송');
    await input.press('Enter');
    await page.waitForTimeout(4500);
    await expect(page.locator('[data-testid="message-assistant-0"]')).toBeVisible();

    const searchInput = page.locator('[data-testid="search-input"]');
    await searchInput.fill('하이라이트');
    await page.locator('[data-testid="search-button"]').click();
    await page.waitForTimeout(1500);
    await expect(page.locator('[data-testid^="search-result-"]')).toHaveCount(1);
    console.log('하이라이팅 감지 시작');
    await waitForHighlight(page, '하이라이트');
  });
});
