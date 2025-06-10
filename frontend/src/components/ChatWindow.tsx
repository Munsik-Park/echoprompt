import { useState, useEffect } from 'react';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  id?: string;
  timestamp?: number;
}

interface ChatWindowProps {
  messages: ChatMessage[];
  isLoading?: boolean;
}

function ChatWindow({ messages, isLoading = false }: ChatWindowProps) {
  const [highlightedMessageId, setHighlightedMessageId] = useState<string | null>(null);

  // 새 메시지가 추가될 때 하이라이트 처리
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.id) {
        setHighlightedMessageId(lastMessage.id);
        // 2초 후 하이라이트 제거
        const timer = setTimeout(() => {
          setHighlightedMessageId(null);
        }, 2000);
        return () => clearTimeout(timer);
      }
    }
  }, [messages]);

  // 메시지를 타임스탬프와 role로 정렬
  const sortedMessages = [...messages].sort((a, b) => {
    // 타임스탬프가 없는 경우 현재 시간 사용
    const timeA = a.timestamp || Date.now();
    const timeB = b.timestamp || Date.now();
    const timeDiff = timeA - timeB;

    // 1초 이내의 메시지는 role로 정렬 (user가 먼저)
    if (Math.abs(timeDiff) < 1000) {
      return a.role === 'user' ? -1 : 1;
    }
    return timeDiff;
  });

  // 메시지 인덱스 계산 (role과 id 기반)
  const messageIndices = new Map<string, number>();
  const roleCounters = {
    user: 0,
    assistant: 0
  };
  
  sortedMessages.forEach((msg) => {
    const counter = msg.role === 'assistant' ? roleCounters.assistant++ : roleCounters.user++;
    messageIndices.set(`${msg.role}-${msg.id}`, counter);
  });

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-2">
      <style>
        {`
          .highlighted-message {
            animation: highlight 1s ease-out;
            background-color: rgba(255, 255, 0, 0.3);
          }
          @keyframes highlight {
            0% { 
              background-color: rgba(255, 255, 0, 0.8);
              transform: scale(1.05);
            }
            100% { 
              background-color: rgba(255, 255, 0, 0);
              transform: scale(1);
            }
          }
          .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
          }
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
      {sortedMessages.map((msg) => (
        <div
          key={`${msg.role}-${msg.id}-${msg.timestamp}`}
          data-message-id={msg.id}
          className={`max-w-sm p-2 rounded ${
            msg.role === 'assistant'
              ? 'bg-gray-100 text-gray-800'
              : 'bg-blue-600 text-white ml-auto'
          } ${msg.id === highlightedMessageId ? 'highlighted-message' : ''}`}
          data-testid={`message-${msg.role}-${messageIndices.get(`${msg.role}-${msg.id}`)}`}
        >
          {msg.content}
        </div>
      ))}
      {isLoading && (
        <div 
          className="flex justify-center items-center p-4"
          data-testid="loading-spinner"
        >
          <div className="loading-spinner" />
        </div>
      )}
    </div>
  );
}

export default ChatWindow;
