import { useEffect, useState } from 'react';
import api from '../api/api';

export interface Session {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
}

const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1초
const API_TIMEOUT = 5000; // 5초

export function useSessions() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = async (retryCount = 0) => {
    try {
      setLoading(true);
      const response = await api.get<Session[]>('/sessions', {
        timeout: API_TIMEOUT
      });
      setSessions(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch sessions:', err);
      
      if (retryCount < MAX_RETRIES) {
        console.log(`Retrying... (${retryCount + 1}/${MAX_RETRIES})`);
        setTimeout(() => fetchSessions(retryCount + 1), RETRY_DELAY);
      } else {
        setError(err.response?.data?.detail || err.message || 'Failed to fetch sessions');
      }
    } finally {
      setLoading(false);  // 모든 경우에 로딩 상태 해제
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  return { sessions, loading, error, refetch: () => fetchSessions() };
}
