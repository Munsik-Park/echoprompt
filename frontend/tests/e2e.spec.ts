import { test, expect, request } from '@playwright/test';
import axios from 'axios';
import { Page } from '@playwright/test';
import api from '../src/api/api';
import { API_PATHS } from '../src/api/constants';
import { SessionId } from '../src/types/session';

if (!process.env.VITE_API_URL) {
  throw new Error('VITE_API_URL environment variable is not set');
}

if (!process.env.VITE_FRONTEND_URL) {
  throw new Error('VITE_FRONTEND_URL environment variable is not set');
}

if (!process.env.VITE_API_VERSION) {
  throw new Error('VITE_API_VERSION environment variable is not set');
}

const FRONTEND_URL = process.env.VITE_FRONTEND_URL || 'http://localhost:3000';
const API_BASE_URL = process.env.VITE_API_URL;
const API_VERSION = process.env.VITE_API_VERSION;

// 서버 상태 확인 함수
async function checkServerStatus(retries = 5, delay = 2000) {
  for (let i = 0; i < retries; i++) {
    try {
      // 백엔드 서버 확인
      const backendResponse = await api.get(API_PATHS.HEALTH);
      if (backendResponse.status === 200) {
        console.log('백엔드 서버가 실행 중입니다.');
        
        // 프론트엔드 서버 확인
        const frontendResponse = await axios.get(FRONTEND_URL);
        if (frontendResponse.status === 200) {
          console.log('프론트엔드 서버가 실행 중입니다.');
          return true;
        }
      }
    } catch (error) {
      console.log(`서버 상태 확인 시도 ${i + 1}/${retries} 실패:`, error.message);
      if (i < retries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  throw new Error('테스트를 실행하기 전에 백엔드와 프론트엔드 서버가 실행 중인지 확인해주세요.');
}

// 세션 생성 함수
async function createSession(apiContext: any, testName: string) {
  try {
    const sessionName = `테스트 세션 - ${testName} - ${Date.now()}`;
    const response = await apiContext.post(API_PATHS.SESSIONS, {
      name: sessionName
    });
    
    if (!response.ok()) {
      throw new Error(`세션 생성 실패: ${response.status()}`);
    }
    
    const responseBody = await response.json();
    console.log(`테스트 세션이 생성되었습니다: ${sessionName}`, responseBody);
    
    // 세션 생성 후 검증 전 1초 대기
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 세션 생성 확인
    const verifyResponse = await apiContext.get(`${API_PATHS.SESSIONS}/${responseBody.id}`);
    if (!verifyResponse.ok()) {
      throw new Error('세션 생성 확인 실패');
    }
    
    return responseBody;
  } catch (error) {
    console.error('세션 생성 중 오류 발생:', error);
    throw error;
  }
}

// 세션 선택 및 상태 업데이트 대기 함수
async function selectSessionAndWait(page: Page, sessionId: SessionId) {
  // 페이지 새로고침
  await page.reload();
  
  // 세션 목록이 로드될 때까지 대기
  await page.waitForSelector('[data-testid="session-list"]', { state: 'visible', timeout: 30000 });
  
  // 세션 목록이 비어있지 않은지 확인
  const sessionList = await page.locator('[data-testid="session-list"]');
  const sessionCount = await sessionList.locator('[data-testid^="session-"]').count();
  if (sessionCount === 0) {
    throw new Error('세션 목록이 비어있습니다.');
  }

  // 특정 세션 선택
  const sessionSelector = `[data-testid="session-${sessionId}"]`;
  await page.waitForSelector(sessionSelector, { state: 'visible', timeout: 30000 });
  
  // 세션이 선택 가능한 상태가 될 때까지 대기
  await page.waitForFunction(
    (selector) => {
      const element = document.querySelector(selector);
      return element && !element.classList.contains('opacity-50');
    },
    sessionSelector,
    { timeout: 30000 }
  );
  
  // 세션 클릭 전 추가 대기
  await page.waitForTimeout(2000);
  
  // 세션 클릭
  await page.click(sessionSelector);
  
  // 클릭 후 상태 업데이트 대기
  await page.waitForFunction(
    (selector) => {
      const element = document.querySelector(selector);
      return element && element.classList.contains('bg-blue-50');
    },
    sessionSelector,
    { timeout: 30000 }
  );

  // 메시지 입력 필드가 활성화될 때까지 대기
  const inputField = page.locator('[data-testid="prompt-input"]');
  await expect(inputField).toBeEnabled({ timeout: 30000 });
  
  // 세션 선택 후 추가 대기 시간
  await page.waitForTimeout(2000);
}

test.describe('EchoPrompt Frontend Tests', () => {
  let apiContext: any;

  test.beforeAll(async () => {
    // 서버 상태 확인
    await checkServerStatus();
    
    // API 컨텍스트 생성
    apiContext = await request.newContext();
  });

  test.afterAll(async () => {
    // API 컨텍스트 정리
    await apiContext.dispose();
  });

  test.beforeEach(async ({ page }, testInfo) => {
    // 페이지 로드
    await page.goto(FRONTEND_URL);
    
    // 세션 목록이 로드될 때까지 대기
    await page.waitForSelector('[data-testid="session-list"]', { state: 'visible', timeout: 30000 });
    
    // 세션 생성
    const session = await createSession(apiContext, testInfo.title);
    const sessionId = session.id;
    
    // 세션 선택
    await selectSessionAndWait(page, sessionId);
  });

  test('1.1 메인 페이지 로딩 및 세션 리스트 확인', async ({ page }) => {
    await expect(page.locator('[data-testid="session-list"]')).toBeVisible({ timeout: 30000 });
  });

  test('1.2 세션 선택 및 메시지 리스트 확인', async ({ page }) => {
    // 채팅 윈도우가 표시되는지 확인
    await expect(page.locator('.flex-1.overflow-y-auto')).toBeVisible({ timeout: 30000 });
  });

  test('1.3 새 메시지 입력 및 LLM 응답 확인', async ({ page }) => {
    const testMessage = '테스트 프롬프트입니다.';
    
    // 입력 필드 활성화 대기
    const input = page.locator('[data-testid="prompt-input"]');
    await expect(input).toBeEnabled({ timeout: 30000 });
    
    // 메시지 입력
    await input.fill(testMessage);
    
    // 로딩 스피너가 아직 보이지 않는지 확인
    const spinner = page.locator('[data-testid="loading-spinner"]');
    await expect(spinner).not.toBeVisible();
    
    // 메시지 전송
    await input.press('Enter');
    
    // 로딩 스피너가 표시되는지 확인
    await expect(spinner).toBeVisible({ timeout: 5000 });
    
    // 사용자 메시지가 표시되는지 확인
    const userMessage = page.locator('[data-testid="message-user-0"]');
    await expect(userMessage).toBeVisible({ timeout: 30000 });
    await expect(userMessage).toContainText(testMessage);
    
    // LLM 응답이 표시되는지 확인
    const assistantMessage = page.locator('[data-testid="message-assistant-0"]');
    await expect(assistantMessage).toBeVisible({ timeout: 30000 });
    
    // LLM 응답 내용 검증
    const responseText = await assistantMessage.textContent();
    expect(responseText).toBeTruthy();
    expect(responseText?.length).toBeGreaterThan(0);
    expect(responseText).not.toBe(testMessage);
    
    // 에러 메시지가 표시되지 않는지 확인
    await expect(page.locator('[data-testid="error-message"]')).not.toBeVisible({ timeout: 10000 });
    
    // 로딩 스피너가 사라지는지 확인
    await expect(spinner).toBeHidden({ timeout: 30000 });
  });

  test('2.1 의미 기반 검색 기능', async ({ page }) => {
    // 입력 필드 활성화 대기
    const input = page.locator('[data-testid="prompt-input"]');
    await expect(input).toBeEnabled({ timeout: 30000 });
    
    // 테스트 메시지 입력 및 전송
    const testMessage = '테스트 메시지입니다.';
    await input.fill(testMessage);
    await input.press('Enter');
    
    // LLM 응답 대기
    const assistantMessage = page.locator('[data-testid="message-assistant-0"]');
    await expect(assistantMessage).toBeVisible({ timeout: 30000 });
    
    // Qdrant 저장 확인
    const saveIndicator = page.locator('[data-testid="save-indicator"]');
    await expect(saveIndicator).toBeVisible({ timeout: 10000 });
    await expect(saveIndicator).toHaveText('저장 완료', { timeout: 30000 });
    
    // 저장 완료 후 추가 대기
    await page.waitForTimeout(5000);
    
    // 검색 기능이 활성화될 때까지 대기
    const searchInput = page.locator('[data-testid="search-input"]');
    await expect(searchInput).toBeVisible({ timeout: 30000 });
    await expect(searchInput).toBeEnabled({ timeout: 30000 });
    
    // 검색 수행
    const testQuery = '테스트';
    await searchInput.fill(testQuery);
    
    const searchButton = page.locator('[data-testid="search-button"]');
    await searchButton.click();
    
    // 검색 결과 확인
    const searchResults = page.locator('[data-testid="search-results"]');
    await expect(searchResults).toBeVisible({ timeout: 30000 });
    
    const results = page.locator('[data-testid^="search-result-"]');
    await expect(results).toHaveCount(1, { timeout: 30000 });
  });

  test('2.2 검색 결과 하이라이트', async ({ page }) => {
    // 입력 필드 활성화 대기
    const input = page.locator('[data-testid="prompt-input"]');
    await expect(input).toBeEnabled({ timeout: 30000 });
    
    // 테스트 메시지 추가
    const testMessage = '하이라이트 테스트 메시지입니다.';
    await input.fill(testMessage);
    
    // 로딩 스피너가 아직 보이지 않는지 확인
    const spinner = page.locator('[data-testid="loading-spinner"]');
    await expect(spinner).not.toBeVisible();
    
    // 메시지 전송
    await input.press('Enter');
    
    // 로딩 스피너가 표시되는지 확인
    await expect(spinner).toBeVisible({ timeout: 5000 });
    
    // LLM 응답이 표시되는지 확인
    const assistantMessage = page.locator('[data-testid="message-assistant-0"]');
    await expect(assistantMessage).toBeVisible({ timeout: 30000 });
    
    // 에러 메시지가 표시되지 않는지 확인
    await expect(page.locator('[data-testid="error-message"]')).not.toBeVisible({ timeout: 10000 });
    
    // 로딩 스피너가 사라지는지 확인
    await expect(spinner).toBeHidden({ timeout: 30000 });
    
    // Qdrant 저장 확인
    const saveIndicator = page.locator('[data-testid="save-indicator"]');
    await expect(saveIndicator).toBeVisible({ timeout: 10000 });
    await expect(saveIndicator).toHaveText('저장 완료', { timeout: 30000 });
    
    // 저장 완료 후 추가 대기
    await page.waitForTimeout(5000);
    
    // 검색 기능이 활성화될 때까지 대기
    const searchInput = page.locator('[data-testid="search-input"]');
    await expect(searchInput).toBeVisible({ timeout: 30000 });
    await expect(searchInput).toBeEnabled({ timeout: 30000 });
    
    // 검색 수행
    const testQuery = '하이라이트';
    await searchInput.fill(testQuery);
    
    const searchButton = page.locator('[data-testid="search-button"]');
    await searchButton.click();
    
    // 검색 결과 확인
    const searchResults = page.locator('[data-testid="search-results"]');
    await expect(searchResults).toBeVisible({ timeout: 30000 });
    
    const results = page.locator('[data-testid^="search-result-"]');
    await expect(results).toHaveCount(1, { timeout: 30000 });
    
    // 검색어 하이라이트 확인
    const highlightedText = page.locator('.highlight');
    await expect(highlightedText).toBeVisible({ timeout: 30000 });
    await expect(highlightedText).toContainText('하이라이트');
  });

  test('3.1 TailwindCSS 레이아웃 확인', async ({ page }) => {
    // 헤더 확인
    await expect(page.locator('header.bg-blue-600')).toBeVisible();
    
    // 메인 레이아웃 확인
    await expect(page.locator('.min-h-screen.flex.flex-col')).toBeVisible();
  });

  test('3.2 로딩 및 에러 상태 확인', async ({ page }) => {
    // 입력 필드 활성화 대기
    const input = page.locator('[data-testid="prompt-input"]');
    await expect(input).toBeEnabled({ timeout: 30000 });
    
    // 테스트 메시지 입력
    const testMessage = '에러 테스트 메시지입니다.';
    await input.fill(testMessage);
    
    // 메시지 전송
    await input.press('Enter');
    
    // 로딩 스피너가 표시되는지 확인
    const spinner = page.locator('[data-testid="loading-spinner"]');
    await expect(spinner).toBeVisible({ timeout: 5000 });
    
    // 에러 메시지가 표시되지 않는지 확인
    await expect(page.locator('[data-testid="error-message"]')).not.toBeVisible({ timeout: 10000 });
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