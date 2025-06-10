import { useState, useEffect } from 'react';
import api from '../api/api';
import { useSessions } from '../hooks/useSessions';
import { API_PATHS } from '../api/constants';
import SessionDebug from './SessionDebug';

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
  const [isCreating, setIsCreating] = useState(false);
  const [newSessionPrompt, setNewSessionPrompt] = useState('');
  const [isDeleting, setIsDeleting] = useState<number | null>(null);
  const [debugInfo, setDebugInfo] = useState({
    sessionId: null as number | null,
    apiResponse: null as any,
    browserResponse: null as any
  });

  const handleCreateSession = async () => {
    if (!newSessionPrompt.trim()) return;
    
    try {
      console.log('Creating session with name:', newSessionPrompt);
      const response = await api.post(API_PATHS.SESSIONS, {
        name: newSessionPrompt.trim()
      });

      console.log('API Response:', response);

      if (response.data && response.data.id) {
        // 디버그 정보 업데이트
        setDebugInfo({
          sessionId: response.data.id,
          apiResponse: response.data,
          browserResponse: {
            status: response.status,
            headers: response.headers,
            url: response.config.url
          }
        });

        await refetch();
        onSessionSelect(response.data.id);
        setIsCreating(false);
        setNewSessionPrompt('');
      }
    } catch (err) {
      console.error('Error creating session:', err);
      // 에러 메시지를 콘솔에만 출력
    }
  };

  const handleDeleteSession = async (sessionId: number) => {
    try {
      setIsDeleting(sessionId);
      await api.delete(API_PATHS.SESSION(sessionId));
      await refetch();
      if (selectedSessionId === sessionId) {
        onSessionSelect(null as unknown as number);
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    } finally {
      setIsDeleting(null);
    }
  };

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

  return (
    <aside className="w-64 border-r overflow-y-auto p-4" data-testid="session-list">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Session List</h2>
        <button
          onClick={() => setIsCreating(true)}
          className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
          data-testid="create-session-button"
        >
          New
        </button>
      </div>

      {isCreating && (
        <div className="mb-4 p-4 border rounded bg-gray-50" data-testid="create-session-form">
          <h3 className="text-sm font-medium mb-2">새 세션 생성</h3>
          <input
            type="text"
            value={newSessionPrompt}
            onChange={(e) => setNewSessionPrompt(e.target.value)}
            placeholder="세션 이름을 입력하세요..."
            className="w-full px-3 py-2 border rounded mb-2"
            data-testid="new-session-input"
          />
          <div className="flex gap-2">
            <button
              onClick={handleCreateSession}
              disabled={!newSessionPrompt.trim()}
              className="flex-1 px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-blue-300"
              data-testid="confirm-create-button"
            >
              생성
            </button>
            <button
              onClick={() => {
                setIsCreating(false);
                setNewSessionPrompt('');
              }}
              className="px-3 py-2 border rounded hover:bg-gray-100"
              data-testid="cancel-create-button"
            >
              취소
            </button>
          </div>
        </div>
      )}

      {(!sessions || sessions.length === 0) && !isCreating ? (
        <div className="p-4" data-testid="no-sessions">No sessions found</div>
      ) : (
        <div className="space-y-2">
          {sessions.map((session) => (
            <div
              key={session.id}
              data-testid={`session-${session.id}`}
              className={`p-4 border rounded transition-colors duration-200 ${
                session.id === selectedSessionId
                  ? 'bg-blue-50 border-blue-500'
                  : 'hover:bg-gray-50'
              }`}
            >
              <div className="flex justify-between items-start">
                <div 
                  className="flex-1 cursor-pointer"
                  onClick={() => {
                    console.log('Session clicked:', session.id);
                    onSessionSelect(session.id);
                  }}
                >
                  <h3 className="font-medium">{session.name}</h3>
                  <p className="text-sm text-gray-500">
                    Created: {new Date(session.created_at).toLocaleString()}
                  </p>
                </div>
                <button
                  onClick={() => handleDeleteSession(session.id)}
                  disabled={isDeleting === session.id}
                  className="ml-2 px-2 py-1 text-red-500 hover:text-red-700 disabled:opacity-50"
                  data-testid={`delete-session-${session.id}`}
                >
                  {isDeleting === session.id ? '삭제 중...' : '삭제'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <SessionDebug 
        sessionId={debugInfo.sessionId}
        apiResponse={debugInfo.apiResponse}
        browserResponse={debugInfo.browserResponse}
      />
    </aside>
  );
}
