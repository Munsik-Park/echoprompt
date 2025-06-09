import { useState, useEffect } from 'react';
import api from '../api/api';
import { useSessions } from '../hooks/useSessions';

interface Session {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
}

interface SessionListProps {
  onSessionSelect: (id: number) => void;
  selectedSessionId: number | null;
}

export default function SessionList({ onSessionSelect, selectedSessionId }: SessionListProps) {
  const { sessions, loading, error, refetch } = useSessions();

  useEffect(() => {
    // 세션 목록이 변경될 때마다 로그 출력
    console.log('Sessions updated:', sessions);
    console.log('Selected session:', selectedSessionId);
  }, [sessions, selectedSessionId]);

  if (loading) {
    return (
      <aside className="w-64 border-r overflow-y-auto p-4" data-testid="session-list">
        <h2 className="text-lg font-semibold mb-4">Session List</h2>
        <div className="p-4" data-testid="loading-sessions">Loading sessions...</div>
      </aside>
    );
  }

  if (error) {
    return (
      <aside className="w-64 border-r overflow-y-auto p-4" data-testid="session-list">
        <h2 className="text-lg font-semibold mb-4">Session List</h2>
        <div className="p-4 text-red-500" data-testid="session-error">
          <p>Error: {error}</p>
          <button 
            onClick={refetch}
            className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            data-testid="retry-button"
          >
            Retry
          </button>
        </div>
      </aside>
    );
  }

  if (!sessions || sessions.length === 0) {
    return (
      <aside className="w-64 border-r overflow-y-auto p-4" data-testid="session-list">
        <h2 className="text-lg font-semibold mb-4">Session List</h2>
        <div className="p-4" data-testid="no-sessions">No sessions found</div>
      </aside>
    );
  }

  return (
    <aside className="w-64 border-r overflow-y-auto p-4" data-testid="session-list">
      <h2 className="text-lg font-semibold mb-4">Session List</h2>
      <div className="space-y-2">
        {sessions.map((session) => (
          <div
            key={session.id}
            data-testid={`session-${session.id}`}
            onClick={() => {
              console.log('Session clicked:', session.id);
              onSessionSelect(session.id);
            }}
            className={`p-4 border rounded cursor-pointer transition-colors duration-200 ${
              session.id === selectedSessionId
                ? 'bg-blue-50 border-blue-500'
                : 'hover:bg-gray-50'
            }`}
          >
            <h3 className="font-medium">{session.name}</h3>
            <p className="text-sm text-gray-500">
              Created: {new Date(session.created_at).toLocaleString()}
            </p>
          </div>
        ))}
      </div>
    </aside>
  );
}
