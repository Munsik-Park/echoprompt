import { test, expect, request } from '@playwright/test';
import { setupTestEnvironment } from './utils/testCase';
import { verifyElementState } from './utils/verification';
import { waitForHighlight } from './utils/waitForHighlight';
import { commonOperations } from './utils/errorHandler';

test.describe('EchoPrompt E2E', () => {
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

  test('send message and receive response', async ({ page }) => {
    const cities = [
      'New York', 'London', 'Tokyo', 'Paris', 'Cairo',
      'Sydney', 'Moscow', 'Toronto', 'Berlin', 'Seoul',
    ];
    const [cityA, cityB] = [...cities].sort(() => 0.5 - Math.random()).slice(0, 2);
    const message = `${cityA}에서 ${cityB}까지의 거리는 얼마인가요?`;

    // 메시지 전송
    await commonOperations.fillInput(page, '[data-testid="prompt-input"]', message);
    await commonOperations.pressKey(page, 'Enter');
    console.log('사용자 메시지 입력 및 전송');

    // 응답 대기
    await page.waitForTimeout(4500);

    // 하이라이트 확인
    console.log('하이라이팅 감지 시작');
    await waitForHighlight(page, {
      elementType: 'message',
      text: message
    });

    // 응답 메시지 확인
    await verifyElementState(page, {
      selector: '[data-testid^="message-assistant-"]',
      state: 'visible'
    });
  });

  test('semantic search highlights result', async ({ page }) => {
    const msg = '하이라이트 테스트 메시지';

    // 메시지 전송
    await commonOperations.fillInput(page, '[data-testid="prompt-input"]', msg);
    await commonOperations.pressKey(page, 'Enter');
    console.log('사용자 메시지 입력 및 전송');

    // 응답 대기
    await page.waitForTimeout(4500);
    await verifyElementState(page, {
      selector: '[data-testid="message-assistant-0"]',
      state: 'visible'
    });

    // 검색 수행
    await commonOperations.fillInput(page, '[data-testid="search-input"]', '하이라이트');
    await commonOperations.clickElement(page, '[data-testid="search-button"]');
    await page.waitForTimeout(1500);

    // 검색 결과 확인
    await verifyElementState(page, {
      selector: '[data-testid^="search-result-"]',
      expectedCount: 1
    });

    // 하이라이트 확인
    console.log('하이라이팅 감지 시작');
    await waitForHighlight(page, {
      elementType: 'search-result',
      text: '하이라이트'
    });
  });
});
