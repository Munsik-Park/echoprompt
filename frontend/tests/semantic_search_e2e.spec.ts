import { test, expect, request } from '@playwright/test';
import { setupTestEnvironment } from './utils/testCase';
import { verifySearchResults } from './utils/verification';
import { commonOperations } from './utils/errorHandler';

test.describe('Semantic search after sending message', () => {
  let apiContext: any;

  test.beforeAll(async () => {
    apiContext = await request.newContext({
      extraHTTPHeaders: {
        'Content-Type': 'application/json',
        Accept: 'application/json, text/plain, */*',
      }
    });
  });

  test.afterAll(async () => {
    await apiContext.dispose();
  });

  test.beforeEach(async ({ page }, testInfo) => {
    await setupTestEnvironment({ page, apiContext, testInfo });
  });

  test('semantic search highlights result', async ({ page }) => {
    function getRandomPair(arr: string[]) {
      const shuffled = [...arr].sort(() => 0.5 - Math.random());
      return [shuffled[0], shuffled[1]] as const;
    }

    const cities = [
      'New York', 'London', 'Tokyo', 'Paris', 'Cairo',
      'Sydney', 'Moscow', 'Toronto', 'Berlin', 'Seoul'
    ];

    const testCases = Array.from({ length: 3 }).map(() => {
      const [cityA, cityB] = getRandomPair(cities);
      return {
        city: cityB,
        message: `${cityA}에서 ${cityB}까지 거리는 얼마나 되나요?`,
      };
    });

    for (const { city, message } of testCases) {
      console.log(`테스트 케이스: ${message}`);
      
      // 1. 메시지 전송
      await commonOperations.fillInput(page, '[data-testid="prompt-input"]', message);
      await commonOperations.pressKey(page, 'Enter');
      console.log('메시지 전송 완료');

      // 2. 응답 대기
      await page.waitForTimeout(4500);

      // 3. 검색 수행
      await commonOperations.fillInput(page, '[data-testid="search-input"]', city);
      await commonOperations.pressKey(page, 'Enter');
      console.log('검색 수행 완료');

      // 4. 검색 결과 검증
      await verifySearchResults(page, city, message);
      console.log('검색 결과 검증 완료');
    }
  });
});
