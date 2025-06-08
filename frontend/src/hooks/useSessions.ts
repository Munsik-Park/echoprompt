import { useEffect, useState } from 'react';
import api from '../api/api';

export interface Session {
  id: number;
  name: string;
}

export function useSessions() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .get<Session[]>('/sessions/')
      .then((res) => setSessions(res.data))
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, []);

  return { sessions, loading, error };
}
