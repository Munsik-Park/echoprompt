import { test, expect } from '@playwright/test';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';
const FRONTEND_URL = 'http://localhost:3000';

// 서버 상태 확인 함수
async function checkServerStatus() {
  try {
    // 백엔드 서버 확인
    const backendResponse = await axios.get(`${API_BASE_URL}/`);
    if (backendResponse.status !== 200) {
      throw new Error('백엔드 서버가 응답하지 않습니다.');
    }
    console.log('백엔드 서버가 실행 중입니다.');
    
    // 프론트엔드 서버 확인
    const frontendResponse = await axios.get(FRONTEND_URL);
    if (frontendResponse.status !== 200) {
      throw new Error('프론트엔드 서버가 응답하지 않습니다.');
    }
    console.log('프론트엔드 서버가 실행 중입니다.');
  } catch (error) {
    console.error('서버 상태 확인 중 오류 발생:', error);
    throw new Error('테스트를 실행하기 전에 백엔드와 프론트엔드 서버가 실행 중인지 확인해주세요.');
  }
}

test.describe('EchoPrompt Frontend Tests', () => {
  test.beforeEach(async ({ page }) => {
    // 서버 상태 확인
    await checkServerStatus();
    
    // 테스트 시작 전 페이지 로드
    await page.goto(FRONTEND_URL);
    
    // 세션 리스트가 로드될 때까지 대기
    await expect(page.locator('aside')).toBeVisible();
    
    // 세션이 하나 이상 존재하는지 확인
    const sessions = page.locator('[data-testid^="session-"]');
    const count = await sessions.count();
    
    // 세션이 없으면 API를 통해 새 세션 생성
    if (count === 0) {
      try {
        const response = await axios.post(`${API_BASE_URL}/sessions`, {
          name: '테스트 세션'  // title -> name으로 수정
        });
        
        if (response.status !== 201) {  // 200 -> 201로 수정 (Created)
          throw new Error('세션 생성 실패');
        }
        
        // 페이지 새로고침하여 새 세션 로드
        await page.reload();
        await expect(page.locator('aside')).toBeVisible();
      } catch (error) {
        console.error('세션 생성 중 오류 발생:', error);
        throw new Error('테스트를 실행하기 위한 세션 생성에 실패했습니다.');
      }
    }
  });

  test('1.1 메인 페이지 로딩 및 세션 리스트 확인', async ({ page }) => {
    // 세션 리스트가 로딩되는지 확인
    await expect(page.locator('text=Session List')).toBeVisible();
  });

  test('1.2 세션 선택 및 메시지 리스트 확인', async ({ page }) => {
    // 첫 번째 세션 클릭
    await page.locator('aside').first().click();
    
    // 채팅 윈도우가 표시되는지 확인
    await expect(page.locator('.flex-1.overflow-y-auto')).toBeVisible();
  });

  test('1.3 새 메시지 입력 및 LLM 응답 확인', async ({ page }) => {
    // 세션 선택
    await page.locator('aside').first().click();
    
    const testMessage = '테스트 프롬프트입니다.';
    
    // 메시지 입력
    const input = page.locator('[data-testid="message-input"]');
    await input.fill(testMessage);
    
    // 로딩 스피너가 아직 보이지 않는지 확인
    const spinner = page.locator('[data-testid="loading-spinner"]');
    await expect(spinner).not.toBeVisible();
    
    // 메시지 전송
    await input.press('Enter');
    
    // 로딩 스피너가 표시되는지 확인 (타임아웃 2초)
    await expect(spinner).toBeVisible({ timeout: 2000 });
    
    // 사용자 메시지가 표시되는지 확인
    const userMessage = page.locator('[data-testid="message-user-0"]');
    await expect(userMessage).toBeVisible({ timeout: 5000 });
    await expect(userMessage).toContainText(testMessage);
    
    // LLM 응답이 표시되는지 확인 (타임아웃 15초)
    const assistantMessage = page.locator('[data-testid="message-assistant-0"]');
    await expect(assistantMessage).toBeVisible({ timeout: 15000 });
    
    // LLM 응답 내용 검증
    const responseText = await assistantMessage.textContent();
    expect(responseText).toBeTruthy(); // 응답이 비어있지 않은지 확인
    expect(responseText?.length).toBeGreaterThan(0); // 응답 길이가 0보다 큰지 확인
    expect(responseText).not.toBe(testMessage); // 사용자 메시지와 다른지 확인
    
    // 에러 메시지가 표시되지 않는지 확인
    await expect(page.locator('[data-testid="error-message"]')).not.toBeVisible({ timeout: 5000 });
    
    // 로딩 스피너가 사라지는지 확인 (타임아웃 20초)
    await expect(spinner).toBeHidden({ timeout: 20000 });
  });

  test('2.1 의미 기반 검색 기능', async ({ page }) => {
    // 1. 첫 번째 세션 선택
    const sessionList = page.locator('[data-testid="session-list"]');
    await expect(sessionList).toBeVisible();
    const firstSession = page.locator('[data-testid^="session-"]').first();
    await expect(firstSession).toBeVisible();
    await firstSession.click();
    
    // 2. 메시지 입력 및 전송
    const testMessage = '테스트 메시지입니다.';
    const input = page.locator('[data-testid="message-input"]');
    await input.fill(testMessage);
    await input.press('Enter');
    
    // 3. LLM 응답 대기
    const assistantMessage = page.locator('[data-testid="message-assistant-0"]');
    await expect(assistantMessage).toBeVisible({ timeout: 15000 });
    
    // 4. Qdrant 저장 확인
    const saveIndicator = page.locator('[data-testid="save-indicator"]');
    await expect(saveIndicator).toBeVisible({ timeout: 5000 });
    await expect(saveIndicator).toHaveText('저장 완료', { timeout: 10000 });
    
    // 5. 검색 기능 테스트
    const searchInput = page.locator('[data-testid="search-input"]');
    await expect(searchInput).toBeVisible();
    
    const testQuery = '테스트';
    await searchInput.fill(testQuery);
    
    const searchButton = page.locator('[data-testid="search-button"]');
    await searchButton.click();
    
    // 6. 검색 결과 확인
    const searchResults = page.locator('[data-testid="search-results"]');
    await expect(searchResults).toBeVisible({ timeout: 20000 });
    
    const results = page.locator('[data-testid^="search-result-"]');
    await expect(results).toHaveCount(1, { timeout: 20000 });
    
    // 7. 검색 결과 내용 검증
    const firstResult = results.first();
    await expect(firstResult).toContainText(testMessage);
    
    // 8. 검색 메타데이터 확인
    const metadata = page.locator('[data-testid="search-metadata"]');
    await expect(metadata).toBeVisible();
    await expect(metadata).toContainText(testQuery);
    await expect(metadata).toContainText('검색 결과 수: 1');
  });

  test('2.2 검색 결과 하이라이트', async ({ page }) => {
    // 세션 선택
    await page.locator('aside').first().click();
    
    // 테스트 메시지 추가
    const testMessage = '하이라이트 테스트 메시지입니다.';
    const input = page.locator('[data-testid="message-input"]');
    await input.fill(testMessage);
    
    // 로딩 스피너가 아직 보이지 않는지 확인
    const spinner = page.locator('[data-testid="loading-spinner"]');
    await expect(spinner).not.toBeVisible();
    
    // 메시지 전송
    await input.press('Enter');
    
    // 로딩 스피너가 표시되는지 확인 (타임아웃 2초)
    await expect(spinner).toBeVisible({ timeout: 2000 });
    
    // LLM 응답이 표시되는지 확인 (타임아웃 15초)
    const assistantMessage = page.locator('[data-testid="message-assistant-0"]');
    await expect(assistantMessage).toBeVisible({ timeout: 15000 });
    
    // 에러 메시지가 표시되지 않는지 확인
    await expect(page.locator('[data-testid="error-message"]')).not.toBeVisible({ timeout: 5000 });
    
    // 로딩 스피너가 사라지는지 확인 (타임아웃 20초)
    await expect(spinner).toBeHidden({ timeout: 20000 });
    
    // 메시지가 Qdrant에 저장될 때까지 대기
    await page.waitForTimeout(5000);
    
    // 검색 수행
    const searchInput = page.locator('[data-testid="search-input"]');
    await searchInput.fill('하이라이트');
    await page.locator('[data-testid="search-button"]').click();
    
    // 검색 결과 대기
    const searchResults = page.locator('[data-testid="search-results"]');
    await expect(searchResults).toBeVisible({ timeout: 20000 });
    
    // 검색 결과 클릭
    await page.locator('.search-result').first().click();
    
    // 해당 메시지가 하이라이트되는지 확인
    await expect(page.locator('.highlighted-message')).toBeVisible();
  });

  test('3.1 TailwindCSS 레이아웃 확인', async ({ page }) => {
    // 헤더 확인
    await expect(page.locator('header.bg-blue-600')).toBeVisible();
    
    // 메인 레이아웃 확인
    await expect(page.locator('.min-h-screen.flex.flex-col')).toBeVisible();
  });

  test('3.2 로딩 및 에러 상태 확인', async ({ page }) => {
    // 세션 선택
    await page.locator('aside').first().click();
    
    // 메시지 입력 시 로딩 상태 확인
    const input = page.locator('[data-testid="message-input"]');
    await input.fill('테스트 메시지');
    
    // 로딩 스피너가 아직 보이지 않는지 확인
    const spinner = page.locator('[data-testid="loading-spinner"]');
    await expect(spinner).not.toBeVisible();
    
    // 메시지 전송
    await input.press('Enter');
    
    // 로딩 스피너가 표시되는지 확인 (타임아웃 2초)
    await expect(spinner).toBeVisible({ timeout: 2000 });
    
    // 에러 메시지가 표시되지 않는지 확인
    await expect(page.locator('[data-testid="error-message"]')).not.toBeVisible({ timeout: 5000 });
    
    // 로딩 스피너가 사라지는지 확인 (타임아웃 20초)
    await expect(spinner).toBeHidden({ timeout: 20000 });
  });

  test('4.1 모바일 반응형 테스트', async ({ page }) => {
    // 모바일 뷰포트 설정
    await page.setViewportSize({ width: 375, height: 667 });
    
    // 모바일 레이아웃 확인
    await expect(page.locator('.min-h-screen.flex.flex-col')).toBeVisible();
  });

  test('4.2 태블릿 반응형 테스트', async ({ page }) => {
    // 태블릿 뷰포트 설정
    await page.setViewportSize({ width: 768, height: 1024 });
    
    // 태블릿 레이아웃 확인
    await expect(page.locator('.min-h-screen.flex.flex-col')).toBeVisible();
  });
}); 