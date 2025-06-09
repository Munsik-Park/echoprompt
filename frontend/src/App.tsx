import Header from './components/Header';
import SessionList from './components/SessionList';
import ChatWindow, { ChatMessage } from './components/ChatWindow';
import PromptInput from './components/PromptInput';
import SemanticSearch from './components/SemanticSearch';
import api from './api/api';
import { API_PATHS } from './api/constants';
import { useState } from 'react';

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');

  const handleSessionSelect = async (sessionId: number) => {
    setSelectedSessionId(sessionId);
    setMessages([]); // 세션 변경 시 메시지 초기화
    setError(null);
    setSaveStatus('idle');
    
    try {
      // 세션의 메시지 목록 가져오기
      const response = await api.get<ChatMessage[]>(API_PATHS.MESSAGES(sessionId));
      setMessages(response.data);
    } catch (err) {
      console.error('Error loading session messages:', err);
      setError('세션 메시지를 불러오는 중 오류가 발생했습니다.');
    }
  };

  const sendPrompt = async (prompt: string) => {
    if (!selectedSessionId) {
      setError('세션을 선택해주세요.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSaveStatus('saving');

      // 사용자 메시지 추가
      const userMessage: ChatMessage = {
        role: 'user',
        content: prompt,
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, userMessage]);

      // API 호출
      const res = await api.post<{ message: string }>(API_PATHS.CHAT, {
        prompt: prompt,
        session_id: selectedSessionId
      });

      if (!res.data || !res.data.message) {
        throw new Error('Invalid response from server');
      }

      // 어시스턴트 메시지 추가
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: res.data.message,
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Qdrant 저장 완료 표시
      setSaveStatus('saved');

    } catch (err) {
      console.error('Error sending message:', err);
      setError('메시지 전송 중 오류가 발생했습니다.');
      setSaveStatus('idle');
      
      // 에러 메시지 추가
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: '죄송합니다. 메시지를 처리하는 중에 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <div className="flex flex-1">
        <SessionList onSessionSelect={handleSessionSelect} selectedSessionId={selectedSessionId} />
        <div className="flex-1 flex flex-col">
          <ChatWindow messages={messages} isLoading={loading} />
          {error && (
            <div className="p-2 bg-red-100 text-red-700 text-sm" data-testid="error-message">
              {error}
            </div>
          )}
          {saveStatus === 'saving' && (
            <div className="p-2 bg-blue-100 text-blue-700 text-sm" data-testid="save-indicator">
              저장 중...
            </div>
          )}
          {saveStatus === 'saved' && (
            <div className="p-2 bg-green-100 text-green-700 text-sm" data-testid="save-indicator">
              저장 완료
            </div>
          )}
          <PromptInput onSend={sendPrompt} loading={loading} disabled={!selectedSessionId} />
        </div>
      </div>
      {selectedSessionId && <SemanticSearch sessionId={selectedSessionId} />}
    </div>
  );
}

export default App;
