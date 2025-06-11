import { useState, useEffect } from 'react';
import Header from './components/Header';
import SessionList from './components/SessionList';
import ChatWindow, { ChatMessage } from './components/ChatWindow';
import PromptInput from './components/PromptInput';
import SemanticSearch from './components/SemanticSearch';
import api from './api/api';
import { API_PATHS } from './api/constants';
import axios from 'axios';

function App() {
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessageTimestamp, setLastMessageTimestamp] = useState<number>(0);

  // 세션 변경 시 메시지 목록 초기화 및 가져오기
  useEffect(() => {
    if (selectedSessionId) {
      fetchMessages(selectedSessionId);
    } else {
      setMessages([]);
    }
  }, [selectedSessionId]);

  const fetchMessages = async (sessionId: number) => {
    try {
      const response = await api.get(API_PATHS.SESSION_MESSAGES(sessionId));
      if (response.data && Array.isArray(response.data)) {
        const formattedMessages = response.data.map((msg: any) => ({
          role: msg.role,
          content: msg.content,
          id: msg.id,
          timestamp: new Date(msg.created_at).getTime()
        }));
        setMessages(formattedMessages);
        
        // 마지막 메시지 타임스탬프 업데이트
        if (formattedMessages.length > 0) {
          const lastTimestamp = Math.max(...formattedMessages.map(msg => msg.timestamp));
          setLastMessageTimestamp(lastTimestamp);
        }
      }
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!selectedSessionId) return;

    try {
      setIsLoading(true);
      
      // 1. 사용자 메시지 먼저 추가
      const userMessage = {
        id: Date.now(), // 임시 ID
        content: content,
        role: 'user' as const,
        timestamp: Date.now()
      };
      setMessages(prevMessages => [...prevMessages, userMessage]);

      // 2. LLM 응답 요청
      const response = await api.post(`/sessions/${selectedSessionId}/messages`, {
        content,
        role: 'user'
      });

      // 3. LLM 응답이 있는지 확인
      if (!response.data || (!response.data.message?.content && !response.data.content)) {
        throw new Error('LLM 응답이 없습니다.');
      }

      // 4. LLM 응답 메시지 생성
      const assistantMessage = {
        id: response.data.message?.id || response.data.id,
        content: response.data.message?.content || response.data.content,
        role: 'assistant' as const,
        timestamp: response.data.message?.created_at || response.data.created_at || Date.now()
      };

      // 5. 메시지 목록 업데이트
      setMessages(prevMessages => {
        // 이전 메시지 중 사용자 메시지 ID 업데이트
        const updatedMessages = prevMessages.map(msg => 
          msg.id === userMessage.id 
            ? { ...msg, id: response.data.message?.id || response.data.id }
            : msg
        );
        
        // 어시스턴트 메시지 추가
        return [...updatedMessages, assistantMessage];
      });

      // 6. 메시지 목록 새로고침
      await fetchMessages(selectedSessionId);

    } catch (error) {
      console.error('메시지 전송 실패:', error);
      setError('메시지 전송 중 오류가 발생했습니다.');
      
      // 7. 오류 발생 시 사용자 메시지 제거
      setMessages(prevMessages => 
        prevMessages.filter(msg => msg.id !== userMessage.id)
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateSession = async (prompt: string) => {
    try {
      const response = await api.post(API_PATHS.SESSIONS, {
        name: prompt
      });
      
      if (response.data && response.data.id) {
        setSelectedSessionId(response.data.id);
        // 새 세션의 첫 메시지로 사용자 프롬프트 추가
        await handleSendMessage(prompt);
      }
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  // 주기적으로 새 메시지 확인 (30초마다)
  useEffect(() => {
    if (selectedSessionId) {
      const interval = setInterval(async () => {
        try {
          const response = await api.get(API_PATHS.SESSION_MESSAGES(selectedSessionId));
          if (response.data && Array.isArray(response.data)) {
            const newMessages = response.data
              .map((msg: any) => ({
                role: msg.role,
                content: msg.content,
                id: msg.id,
                timestamp: new Date(msg.created_at).getTime()
              }))
              .filter(msg => msg.timestamp > lastMessageTimestamp);
            
            if (newMessages.length > 0) {
              setMessages(prevMessages => [...prevMessages, ...newMessages]);
              const newTimestamp = Math.max(...newMessages.map(msg => msg.timestamp));
              setLastMessageTimestamp(newTimestamp);
            }
          }
        } catch (error) {
          console.error('Failed to check for new messages:', error);
        }
      }, 30000);

      return () => clearInterval(interval);
    }
  }, [selectedSessionId, lastMessageTimestamp]);

  // 메시지 검색 시 기존 메시지 유지
  const handleSearch = async (query: string) => {
    if (!selectedSessionId) return;

    try {
      const response = await api.get(`/sessions/${selectedSessionId}/messages/search`, {
        params: { query }
      });

      // 검색 결과를 기존 메시지와 병합
      setMessages(prevMessages => {
        const existingIds = new Set(prevMessages.map(msg => msg.id));
        const newMessages = response.data.filter((msg: Message) => !existingIds.has(msg.id));
        return [...prevMessages, ...newMessages];
      });
    } catch (error) {
      console.error('메시지 검색 실패:', error);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <SessionList
          onSessionSelect={setSelectedSessionId}
          selectedSessionId={selectedSessionId}
        />
        <div className="flex-1 flex flex-col">
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
          />
          <PromptInput
            onSend={handleSendMessage}
            loading={isLoading}
            disabled={!selectedSessionId}
            onCreateSession={handleCreateSession}
          />
        </div>
        {selectedSessionId && (
          <SemanticSearch sessionId={selectedSessionId} />
        )}
      </div>
    </div>
  );
}

export default App;
