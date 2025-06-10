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

    // Reload to verify session persistence
    await page.reload();
    await page.waitForTimeout(1000);
    const sessionItems = page.locator('[data-testid="session-item"]');
    const sessionCount = await sessionItems.count();
    if (sessionCount === 0) {
      throw new Error('세션 생성 실패로 테스트를 중단합니다.');
    }

    await selectSession(page, session.id);
  });

  test('message appears in semantic search results', async ({ page }) => {
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

    function getRandomPair(arr: string[]) {
      const shuffled = [...arr].sort(() => 0.5 - Math.random());
      return [shuffled[0], shuffled[1]] as const;
    }

    const testCases = Array.from({ length: 3 }).map(() => {
      const [cityA, cityB] = getRandomPair(cities);
      return {
        city: cityB,
        message: `${cityA}에서 ${cityB}까지 거리는 얼마나 되나요?`,
      };
    });

    for (const { city, message } of testCases) {
      const input = page.locator('[data-testid="prompt-input"]');
      await input.fill(message);
      await input.press('Enter');

      // 임베딩/저장 대기
      await page.waitForTimeout(4000);

      const searchInput = page.locator('[data-testid="search-input"]');
      await searchInput.fill(city);
      await searchInput.press('Enter');

      await page.waitForTimeout(1500);
      const results = await page
        .locator('[data-testid="search-result-item"]')
        .allTextContents();
      console.log('검색 결과:', results);
      if (results.length === 0) {
        throw new Error(
          `검색 결과 없음 - 입력 메시지: "${message}" / 검색어: "${city}"`
        );
      }
      expect(results.some((r) => r.includes(message))).toBe(true);
    }
  });
});
