import { test, expect, request, Page } from '@playwright/test';
import { API_PATHS } from '../src/api/constants';

const FRONTEND_URL = process.env.VITE_FRONTEND_URL as string;
const API_BASE_URL = process.env.VITE_API_URL as string;
const API_VERSION = process.env.VITE_API_VERSION as string;

const COMMON_HEADERS = {
  'Content-Type': 'application/json',
  Accept: 'application/json, text/plain, */*',
};

async function createSession(apiContext: any, testName: string) {
  const name = `세션 - ${testName} - ${Date.now()}`;
  const res = await apiContext.post(`${API_BASE_URL}/api/${API_VERSION}${API_PATHS.SESSIONS}`, {
    data: { name },
    headers: COMMON_HEADERS,
  });
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
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
  await expect(targetSession).toBeVisible({ timeout: 90000 });
  await targetSession.click();
  await expect(targetSession).toHaveClass(/bg-blue-50/);
  await expect(page.locator('[data-testid="prompt-input"]')).toBeEnabled();
}

test.describe('Semantic search after sending message', () => {
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

  test('message appears in semantic search results', async ({ page }) => {
    const cities = ['부산', '대구', '광주'];

    for (const city of cities) {
      const message = `서울에서 ${city}까지의 거리는 몇 km야?`;

      const input = page.locator('[data-testid="prompt-input"]');
      await input.fill(message);
      await input.press('Enter');

      // 충분한 대기 시간
      await page.waitForTimeout(2000);

      const searchInput = page.locator('[data-testid="search-input"]');
      await searchInput.fill(city);
      await searchInput.press('Enter');

      const results = page.locator('[data-testid="search-result-item"]');
      await expect(results).toContainText(message);
    }
  });
});
