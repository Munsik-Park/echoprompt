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

const FRONTEND_URL = process.env.VITE_FRONTEND_URL;
const API_BASE_URL = process.env.VITE_API_URL;
const API_VERSION = process.env.VITE_API_VERSION;

// API 요청에 사용할 공통 헤더
const COMMON_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json, text/plain, */*',
  'Origin': 'http://localhost:3000',
  'Referer': 'http://localhost:3000/'
};

// 서버 상태 확인 함수
async function checkServerStatus(retries = 5, delay = 2000) {
  for (let i = 0; i < retries; i++) {
    try {
      // 백엔드 서버 확인
      const backendResponse = await api.get(`${API_BASE_URL}/api/${API_VERSION}${API_PATHS.HEALTH}`, {
        headers: COMMON_HEADERS
      });
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
    const response = await apiContext.post(`${API_BASE_URL}/api/${API_VERSION}${API_PATHS.SESSIONS}`, {
      data: {
        name: sessionName
      },
      headers: COMMON_HEADERS
    });
    
    if (!response.ok()) {
      const responseText = await response.text();
      console.error('세션 생성 실패 응답:', responseText);
      throw new Error(`세션 생성 실패: ${response.status()}`);
    }
    
    const responseBody = await response.json();
    console.log(`테스트 세션이 생성되었습니다: ${sessionName}`, responseBody);
    
    // 세션 생성 후 검증 전 1초 대기
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 세션 생성 확인
    const verifyResponse = await apiContext.get(`${API_BASE_URL}/api/${API_VERSION}${API_PATHS.SESSION(responseBody.id)}`, {
      headers: COMMON_HEADERS
    });
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

// 기존 세션 정리 함수
async function cleanupSessions(apiContext: any) {
  try {
    console.log('=== 세션 정리 시작 ===');
    
    // 삭제 전 세션 목록 확인
    const beforeResponse = await apiContext.get(`${API_BASE_URL}/api/${API_VERSION}${API_PATHS.SESSIONS}`, {
      headers: COMMON_HEADERS
    });
    
    if (beforeResponse.ok()) {
      const beforeSessions = await beforeResponse.json();
      console.log('삭제 전 세션 목록:', beforeSessions);
      
      if (beforeSessions.length === 0) {
        console.log('삭제할 세션이 없습니다.');
        return;
      }
      
      // 각 세션 삭제
      for (const session of beforeSessions) {
        console.log(`세션 ${session.id} 삭제 시도 중...`);
        const deleteResponse = await apiContext.delete(`${API_BASE_URL}/api/${API_VERSION}${API_PATHS.SESSION(session.id)}`, {
          headers: COMMON_HEADERS
        });
        
        if (deleteResponse.ok()) {
          console.log(`세션 ${session.id} 삭제 완료`);
        } else {
          console.error(`세션 ${session.id} 삭제 실패:`, await deleteResponse.text());
        }
      }
      
      // 삭제 후 세션 목록 확인
      const afterResponse = await apiContext.get(`${API_BASE_URL}/api/${API_VERSION}${API_PATHS.SESSIONS}`, {
        headers: COMMON_HEADERS
      });
      
      if (afterResponse.ok()) {
        const afterSessions = await afterResponse.json();
        console.log('삭제 후 세션 목록:', afterSessions);
        
        if (afterSessions.length === 0) {
          console.log('모든 세션이 성공적으로 삭제되었습니다.');
        } else {
          console.warn(`${afterSessions.length}개의 세션이 남아있습니다.`);
        }
      }
    }
    
    console.log('=== 세션 정리 완료 ===');
  } catch (error) {
    console.error('세션 정리 중 오류 발생:', error);
  }
}

test.describe('EchoPrompt Frontend Tests', () => {
  let apiContext: any;

  test.beforeAll(async () => {
    // 서버 상태 확인
    await checkServerStatus();
    
    // API 컨텍스트 생성 (기본 헤더 설정)
    apiContext = await request.newContext({
      extraHTTPHeaders: COMMON_HEADERS
    });
    
    // 기존 세션 정리
    await cleanupSessions(apiContext);
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

  test('1.2 새 세션 생성', async ({ page }) => {
    // ... existing code ...
  });

  test('1.3 새 메시지 입력 및 LLM 응답 확인', async ({ page }) => {
    const cities = ['뉴욕', '도쿄', '런던', '파리', '베이징', '시드니', '로마', '베를린', '모스크바', '두바이'];
    const randomCity = cities[Math.floor(Math.random() * cities.length)];
    const testMessage = `서울에서 ${randomCity}까지의 거리는 몇킬로인가요?`;
    
    // 입력 필드 활성화 대기
    const input = page.locator('[data-testid="prompt-input"]');
    await expect(input).toBeEnabled({ timeout: 10000 });
    
    // 메시지 입력
    await input.fill(testMessage);
    console.log('메시지 입력 완료:', testMessage);
    
    // 입력 후 잠시 대기 (사용자가 입력을 확인하는 시간)
    await page.waitForTimeout(1000);
    
    // 메시지 전송
    await input.press('Enter');
    console.log('메시지 전송 완료');

    // 하이라이트가 적용될 때까지 기다림
    console.log('하이라이트 체크 시작');
    await expect(page.locator('.highlighted-message')).toBeVisible({ timeout: 10000 });
    console.log('하이라이트 확인됨');

    // LLM 응답 대기
    console.log('LLM 응답 대기 시작');
    await expect(page.locator('[data-testid="message-assistant-0"]')).toBeVisible({ timeout: 10000 });
    console.log('LLM 응답 확인됨');

    // 로딩 스피너가 사라질 때까지 대기
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeHidden({ timeout: 10000 });
    console.log('로딩 스피너 사라짐');

    // 2. LLM 응답이 오는지 확인
    const assistantMessages = page.locator('[data-testid^="message-assistant-"]');
    console.log('LLM 응답 메시지 확인 중...');
    await expect(assistantMessages).toHaveCount(1, { timeout: 10000 });
    console.log('LLM 응답 메시지 확인됨');
    const assistantMessage = assistantMessages.first();
    await expect(assistantMessage).toBeVisible();

    // LLM 응답 내용 검증
    const responseText = await assistantMessage.textContent();
    console.log('LLM 응답 내용:', responseText);
    expect(responseText).toBeTruthy();
    expect(responseText?.length).toBeGreaterThan(0);
    expect(responseText).not.toBe(testMessage);
    
    // LLM 응답이 적절한 형식인지 확인 (거리 질문에 대한 일반적인 응답)
    const responseLower = responseText?.toLowerCase() || '';
    const hasAppropriateResponse = 
      responseLower.includes('킬로') || 
      responseLower.includes('거리') || 
      responseLower.includes('km') || 
      responseLower.includes('약') || 
      responseLower.includes('대략');
    expect(hasAppropriateResponse).toBeTruthy();
    console.log('LLM 응답 형식 검증 완료');
  });

  test('1.3 세션 삭제 테스트', async ({ page }) => {
    // 세션 목록이 로드될 때까지 대기
    await page.waitForSelector('[data-testid="session-list"]', { state: 'visible', timeout: 30000 });
    
    // 첫 번째 세션의 삭제 버튼이 표시될 때까지 대기
    const deleteButton = page.locator('[data-testid^="delete-session-"]').first();
    await expect(deleteButton).toBeVisible({ timeout: 30000 });
    
    // 삭제 버튼 클릭
    await deleteButton.click();
    
    // 삭제 버튼이 비활성화되고 "삭제 중..." 텍스트가 표시되는지 확인
    await expect(deleteButton).toBeDisabled();
    await expect(deleteButton).toHaveText('삭제 중...');
    
    // 삭제 완료 후 세션 목록이 업데이트될 때까지 대기
    await page.waitForTimeout(2000);
    
    // 삭제된 세션이 목록에서 사라졌는지 확인
    const sessionCount = await page.locator('[data-testid^="session-"]').count();
    expect(sessionCount).toBe(0);
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
    const highlightedText = page.locator('.highlighted-message');
    await expect(highlightedText).toBeVisible({ timeout: 30000 });
    await expect(highlightedText).toContainText('하이라이트');
  });

  test('3.1 TailwindCSS 레이아웃 확인', async ({ page }) => {
    // 페이지 로드 상태 확인
    console.log('페이지 URL:', await page.url());
    
    // 페이지 로드 완료 대기
    await page.waitForLoadState('networkidle');
    console.log('페이지 로드 완료');
    
    // 실제 UI 요소들 확인
    const sessionList = page.locator('[data-testid="session-list"]');
    const newButton = page.locator('[data-testid="new-session-button"]');
    const messageInput = page.locator('[data-testid="prompt-input"]');
    const sendButton = page.locator('[data-testid="send-button"]');
    const sessionDebug = page.locator('[data-testid="session-debug"]');
    
    // 각 요소의 존재 여부 확인
    console.log('세션 리스트 존재 여부:', await sessionList.count());
    console.log('New 버튼 존재 여부:', await newButton.count());
    console.log('메시지 입력창 존재 여부:', await messageInput.count());
    console.log('전송 버튼 존재 여부:', await sendButton.count());
    console.log('세션 디버그 존재 여부:', await sessionDebug.count());
    
    // 메인 레이아웃 확인
    const layoutElement = page.locator('.min-h-screen.flex.flex-col');
    console.log('레이아웃 요소 존재 여부:', await layoutElement.count());
    
    // New 버튼은 항상 보여야 함
    await expect(newButton).toBeVisible({ timeout: 30000 });
    
    // 세션이 없는 경우 세션 리스트는 비어있어야 함
    const sessionCount = await page.locator('[data-testid^="session-"]').count();
    expect(sessionCount).toBe(0);
    
    // 메시지 입력 관련 요소들은 세션이 선택된 경우에만 보여야 함
    if (sessionCount > 0) {
        await expect(messageInput).toBeVisible({ timeout: 30000 });
        await expect(sendButton).toBeVisible({ timeout: 30000 });
        await expect(sessionDebug).toBeVisible({ timeout: 30000 });
    }
    
    // 레이아웃은 항상 보여야 함
    await expect(layoutElement).toBeVisible({ timeout: 30000 });
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