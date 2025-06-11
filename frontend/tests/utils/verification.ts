import { Page } from '@playwright/test';
import { handleTestError, commonOperations } from './errorHandler';

export interface VerificationOptions {
  selector: string;
  state?: 'visible' | 'hidden';
  timeout?: number;
  expectedText?: string;
  expectedCount?: number;
}

export async function verifyElementState(
  page: Page,
  options: VerificationOptions
) {
  return handleTestError(
    async () => {
      const { selector, state = 'visible', timeout, expectedText, expectedCount } = options;
      
      // 요소 상태 확인
      await commonOperations.waitForElement(page, selector, { state, timeout });
      
      // 텍스트 검증
      if (expectedText) {
        const element = page.locator(selector);
        const text = await element.textContent();
        if (!text?.includes(expectedText)) {
          throw new Error(`요소에 예상 텍스트 "${expectedText}"가 포함되어 있지 않습니다. 실제 텍스트: "${text}"`);
        }
      }
      
      // 개수 검증
      if (expectedCount !== undefined) {
        const elements = page.locator(selector);
        const count = await elements.count();
        if (count !== expectedCount) {
          throw new Error(`예상 요소 개수 ${expectedCount}와 실제 개수 ${count}가 일치하지 않습니다.`);
        }
      }
    },
    {
      page,
      step: 'verifyElementState',
      context: options
    }
  );
}

export async function verifySearchResults(
  page: Page,
  searchText: string,
  expectedMessage?: string
) {
  return handleTestError(
    async () => {
      // 검색 결과 컨테이너 확인
      await verifyElementState(page, {
        selector: '[data-testid="search-results"]',
        state: 'visible',
        timeout: 10000
      });
      
      // 검색 결과 항목 확인
      const resultItems = page.locator('[data-testid="search-result-item"]');
      const count = await resultItems.count();
      if (count === 0) {
        throw new Error('검색 결과 항목이 없습니다.');
      }
      
      // 메시지 포함 여부 확인
      if (expectedMessage) {
        const results = await resultItems.allTextContents();
        if (!results.some(r => r.includes(expectedMessage))) {
          throw new Error(`검색 결과에 예상 메시지 "${expectedMessage}"가 포함되어 있지 않습니다.`);
        }
      }
      
      // 검색어 포함 여부 확인
      const hasSearchText = await page.evaluate(
        ({ searchText }) => {
          const results = Array.from(document.querySelectorAll('[data-testid="search-result-item"]'));
          return results.some(result => result.textContent?.includes(searchText));
        },
        { searchText }
      );
      
      if (!hasSearchText) {
        throw new Error(`검색 결과에 "${searchText}"가 포함되어 있지 않습니다.`);
      }
    },
    {
      page,
      step: 'verifySearchResults',
      context: { searchText, expectedMessage }
    }
  );
} 