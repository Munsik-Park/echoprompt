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
  const res = await apiContext.post(`${API_BASE_URL}/api/${API_VERSION}${API_PATHS.SESSIONS}`, {
    data: { name },
    headers: COMMON_HEADERS,
  });
  expect(res.ok()).toBeTruthy();
  return res.json();
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
  await page.waitForSelector(sessionSelector, { state: 'visible' });
  await page.click(sessionSelector);
  await expect(page.locator(sessionSelector)).toHaveClass(/bg-blue-50/);
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
    await selectSession(page, session.id);
  });

  test('send message and receive response', async ({ page }) => {
    const input = page.locator('[data-testid="prompt-input"]');
    const message = '서울에서 뉴욕까지 몇 km인가요?';

    await input.fill(message);
    await input.press('Enter');

    await waitForHighlight(page, message);
    const assistant = page.locator('[data-testid^="message-assistant-"]').first();
    await expect(assistant).toBeVisible();
  });

  test('semantic search highlights result', async ({ page }) => {
    const input = page.locator('[data-testid="prompt-input"]');
    const msg = '하이라이트 테스트 메시지';

    await input.fill(msg);
    await input.press('Enter');
    await expect(page.locator('[data-testid="message-assistant-0"]')).toBeVisible();
    await expect(page.locator('[data-testid="save-indicator"]')).toHaveText('저장 완료');

    const searchInput = page.locator('[data-testid="search-input"]');
    await searchInput.fill('하이라이트');
    await page.locator('[data-testid="search-button"]').click();
    await expect(page.locator('[data-testid^="search-result-"]')).toHaveCount(1);
    await waitForHighlight(page, '하이라이트');
  });
});
