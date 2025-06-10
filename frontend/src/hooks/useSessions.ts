import { useState, useEffect } from 'react';
import api from '../api/api';
import { API_PATHS } from '../api/constants';
import { Session } from '../types/session';
import { AxiosError } from 'axios';

const MAX_RETRIES = 2;  // 재시도 횟수 감소
const RETRY_DELAY = 1000;  // 재시도 대기 시간 감소
const API_TIMEOUT = 5000;  // API 타임아웃 감소

export const useSessions = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = async (retryCount = 0) => {
    try {
      setLoading(true);
      console.log(`Fetching sessions... (attempt ${retryCount + 1}/${MAX_RETRIES})`);
      
      // 캐시를 완전히 무시하기 위해 타임스탬프 추가
      const timestamp = new Date().getTime();
      const response = await api.get<Session[]>(`${API_PATHS.SESSIONS}?_t=${timestamp}`, {
        timeout: API_TIMEOUT,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
          'If-None-Match': '',
          'If-Modified-Since': ''
        }
      });
      
      console.log('Sessions response:', response.data);
      
      if (!response.data || !Array.isArray(response.data)) {
        throw new Error('Invalid response format');
      }
      
      setSessions(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
      
      // 404 에러나 빈 응답은 정상적인 초기 상태로 처리
      if (err instanceof AxiosError && (err.response?.status === 404 || !err.response)) {
        setSessions([]);
        setError(null);
        return;
      }
      
      // 다른 에러의 경우에만 재시도
      if (retryCount < MAX_RETRIES - 1) {
        console.log(`Retrying... (${retryCount + 1}/${MAX_RETRIES})`);
        setTimeout(() => fetchSessions(retryCount + 1), RETRY_DELAY);
      } else {
        setError('세션 목록을 불러오는데 실패했습니다.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  return { sessions, loading, error, refetch: () => fetchSessions() };
};
