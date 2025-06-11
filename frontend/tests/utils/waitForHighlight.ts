import { Page, expect } from '@playwright/test';

// 하이라이트 가능한 요소의 타입 정의
export type HighlightableElement = 'message' | 'search-result';

// 하이라이트 검증을 위한 공통 인터페이스
interface HighlightOptions {
  elementType: HighlightableElement;
  text: string;
  timeout?: number;
}

// 요소 타입별 선택자 매핑
const SELECTORS = {
  message: '[data-testid^="message-"]',
  'search-result': '[data-testid="search-result-item"]'
} as const;

// 요소 타입별 하이라이트 클래스 매핑
const HIGHLIGHT_CLASSES = {
  message: 'highlighted-message',
  'search-result': 'highlighted-result'
} as const;

/**
 * 하이라이트 검증을 위한 공통 함수
 * @param page Playwright Page 객체
 * @param options 하이라이트 검증 옵션
 */
export async function waitForHighlight(page: Page, options: HighlightOptions) {
  const { elementType, text, timeout = 10000 } = options;
  const selector = SELECTORS[elementType];
  const highlightClass = HIGHLIGHT_CLASSES[elementType];

  console.log(`Waiting for highlight on ${elementType} with text: ${text}`);
  
  await page.waitForFunction(
    ({ selector, text, highlightClass }) => {
      const nodes = Array.from(document.querySelectorAll(selector));
      return nodes.some(node => 
        node.textContent?.includes(text) && 
        node.classList.contains(highlightClass)
      );
    },
    { selector, text, highlightClass },
    { timeout }
  );
  
  console.log(`Highlight found for ${elementType}`);
}

// 기존 함수와의 호환성을 위한 래퍼 함수
export async function waitForMessageHighlight(page: Page, messageText: string) {
  return waitForHighlight(page, {
    elementType: 'message',
    text: messageText
  });
}

// 검색 결과 하이라이트를 위한 래퍼 함수
export async function waitForSearchResultHighlight(page: Page, searchText: string) {
  return waitForHighlight(page, {
    elementType: 'search-result',
    text: searchText
  });
}
