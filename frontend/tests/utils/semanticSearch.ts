import { Page } from '@playwright/test';
import { handleTestError, commonOperations } from './errorHandler';
import { waitForMessageHighlight, waitForSearchResultHighlight } from './waitForHighlight';

interface SemanticSearchOptions {
  page: Page;
  searchText: string;
}

export async function sendMessageAndWaitForResponse(page: Page, message: string) {
  console.log('메시지 전송 및 응답 대기 시작');
  
  // 1. 메시지 전송
  await commonOperations.fillInput(page, '[data-testid="prompt-input"]', message);
  await commonOperations.pressKey(page, 'Enter');
  console.log('메시지 전송 완료');

  // 2. 하이라이트 표시 확인
  await waitForMessageHighlight(page, message);
  console.log('하이라이트 표시 확인됨');

  // 3. 500ms 지연
  await page.waitForTimeout(500);
  console.log('500ms 지연 완료');

  // 4. 스피너 상태 확인 (실패해도 테스트는 계속 진행)
  try {
    const spinner = page.locator('[data-testid="loading-spinner"]');
    const isVisible = await spinner.isVisible();
    console.log('로딩 스피너 상태:', isVisible ? '표시됨' : '표시되지 않음');
  } catch (error) {
    console.log('로딩 스피너 확인 실패 (무시됨)');
  }

  // 5. LLM 응답 확인
  await commonOperations.waitForElement(page, '[data-testid="message-assistant-0"]');
  const assistantMessage = page.locator('[data-testid="message-assistant-0"]');
  const messageContent = await assistantMessage.textContent();
  
  if (!messageContent || messageContent.trim().length === 0) {
    throw new Error('응답 메시지 내용이 없습니다.');
  }
  console.log('응답 메시지 확인됨:', messageContent);
}

export async function verifySearchResults(page: Page, searchText: string) {
  console.log('검색 결과 확인 시작');
  
  try {
    // 검색 결과 컨테이너가 표시될 때까지 대기
    await page.waitForSelector('[data-testid="search-results"]', { 
      state: 'visible',
      timeout: 10000 
    });
    console.log('검색 결과 컨테이너 확인됨');

    // 검색 결과 항목이 있는지 확인
    const resultItems = page.locator('[data-testid="search-result-item"]');
    const count = await resultItems.count();
    console.log('검색 결과 항목 수:', count);
    
    if (count === 0) {
      throw new Error('검색 결과 항목이 없습니다.');
    }
    console.log('검색 결과 항목 확인됨');

    // 메타데이터 확인
    const metadata = page.locator('[data-testid="search-metadata"]');
    const isMetadataVisible = await metadata.isVisible();
    console.log('메타데이터 표시 여부:', isMetadataVisible);
    
    if (isMetadataVisible) {
      const metadataText = await metadata.textContent();
      console.log('메타데이터 내용:', metadataText);
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
    console.log('검색어 포함 확인 완료');

    // 하이라이트 적용 확인
    await waitForSearchResultHighlight(page, searchText);
    console.log('하이라이트 검증 완료');
  } catch (error) {
    console.log('검색 결과 확인 실패:', error.message);
    throw error;
  }
}

export async function performSemanticSearchAfterResponse(options: SemanticSearchOptions) {
  const { page, searchText } = options;
  console.log('의미 검색 수행 시작:', searchText);
  
  // 1. 검색 수행
  await commonOperations.fillInput(page, '[data-testid="search-input"]', searchText);
  await commonOperations.clickElement(page, '[data-testid="search-button"]');

  // 2. 검색 결과 검증 (통합된 로직)
  await verifySearchResults(page, searchText);
  console.log('의미 검색 수행 완료');
}

export async function resetTestState(page: Page) {
  console.log('테스트 상태 초기화 시작');
  
  // 입력 필드 초기화
  await page.fill('[data-testid="prompt-input"]', '');
  await page.fill('[data-testid="search-input"]', '');
  
  console.log('테스트 상태 초기화 완료');
} 