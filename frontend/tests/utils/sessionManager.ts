import { Page } from '@playwright/test';
import { API_PATHS } from '../../src/api/constants';
import { handleTestError } from './errorHandler';

const FRONTEND_URL = process.env.VITE_FRONTEND_URL as string;
const API_BASE_URL = process.env.VITE_API_URL as string;
const API_VERSION = process.env.VITE_API_VERSION as string;

const COMMON_HEADERS = {
  'Content-Type': 'application/json',
  Accept: 'application/json, text/plain, */*',
};

export async function createSession(apiContext: any, testName: string) {
  return handleTestError(
    async () => {
      const name = `세션 - ${testName} - ${Date.now()}`;
      console.log('세션 생성 요청:', {
        url: `${API_BASE_URL}/api/${API_VERSION}${API_PATHS.SESSIONS}`,
        name,
        headers: COMMON_HEADERS
      });

      const res = await apiContext.post(`${API_BASE_URL}/api/${API_VERSION}${API_PATHS.SESSIONS}`, {
        data: { name },
        headers: COMMON_HEADERS,
      });

      console.log('세션 생성 응답:', {
        status: res.status(),
        statusText: res.statusText(),
        headers: res.headers()
      });

      if (!res.ok()) {
        const errorText = await res.text();
        console.error('세션 생성 실패:', errorText);
        throw new Error(`세션 생성 실패: ${res.statusText()} - ${errorText}`);
      }

      const data = await res.json();
      console.log('세션 생성 완료. ID:', data.id);
      return data;
    },
    {
      page: null,
      step: 'createSession',
      context: { testName }
    }
  );
}

export async function deleteAllSessions(apiContext: any) {
  return handleTestError(
    async () => {
      const res = await apiContext.get(`${API_BASE_URL}/api/${API_VERSION}${API_PATHS.SESSIONS}`, {
        headers: COMMON_HEADERS,
      });
      if (!res.ok()) return;
      const sessions = await res.json();
      for (const session of sessions) {
        await apiContext.delete(`${API_BASE_URL}/api/${API_VERSION}${API_PATHS.SESSIONS}/${session.id}`, {
          headers: COMMON_HEADERS,
        });
      }
      console.log('모든 세션 삭제 완료');
    },
    {
      page: null,
      step: 'deleteAllSessions'
    }
  );
}

export async function selectSession(page: Page, id: number) {
  return handleTestError(
    async () => {
      const sessionSelector = `[data-testid="session-${id}"]`;
      const sessionList = page.locator('[data-testid="session-list"]');
      const targetSession = sessionList.locator(sessionSelector);

      console.log('세션 목록에서 세션 대기 중:', sessionSelector);
      await targetSession.waitFor({ state: 'visible', timeout: 90000 });

      await targetSession.click();
      console.log(`세션 ${id} 선택 완료`);
      
      await page.locator('[data-testid="prompt-input"]').waitFor({ state: 'enabled' });
    },
    {
      page,
      step: 'selectSession',
      context: { sessionId: id }
    }
  );
} 