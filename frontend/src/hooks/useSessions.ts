import { useState, useEffect } from 'react';
import api from '../api/api';
import { API_PATHS } from '../api/constants';
import { Session } from '../types/session';

const MAX_RETRIES = 3;
const RETRY_DELAY = 2000; // 대기 시간 증가
const API_TIMEOUT = 10000; // 타임아웃 증가

export const useSessions = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = async (retryCount = 0) => {
    try {
      setLoading(true);
      console.log(`Fetching sessions... (attempt ${retryCount + 1}/${MAX_RETRIES})`);
      
      const response = await api.get<Session[]>(API_PATHS.SESSIONS, {
        timeout: API_TIMEOUT
      });
      
      console.log('Sessions response:', response.data);
      
      if (!response.data || !Array.isArray(response.data)) {
        throw new Error('Invalid response format');
      }
      
      setSessions(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
      
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
    
    // 주기적으로 세션 목록 갱신
    const intervalId = setInterval(() => {
      fetchSessions();
    }, 5000); // 5초마다 갱신
    
    return () => clearInterval(intervalId);
  }, []);

  return { sessions, loading, error, refetch: () => fetchSessions() };
};
