import { useState } from 'react';

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
  // 메시지를 타임스탬프로 정렬
  const sortedMessages = [...messages].sort((a, b) => 
    (a.timestamp || 0) - (b.timestamp || 0)
  );

  // 메시지 인덱스 계산
  const messageIndices = new Map<string, number>();
  const roleCounters = {
    user: 0,
    assistant: 0
  };
  
  sortedMessages.forEach((msg, idx) => {
    const counter = msg.role === 'assistant' ? roleCounters.assistant++ : roleCounters.user++;
    messageIndices.set(`${msg.role}-${idx}`, counter);
  });

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-2">
      <style>
        {`
          .highlighted-message {
            animation: highlight 2s ease-out;
          }
          @keyframes highlight {
            0% { background-color: yellow; }
            100% { background-color: transparent; }
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
      {sortedMessages.map((msg, idx) => (
        <div
          key={msg.id || msg.timestamp}
          data-message-id={msg.id}
          className={`max-w-sm p-2 rounded ${
            msg.role === 'assistant'
              ? 'bg-gray-100 text-gray-800'
              : 'bg-blue-600 text-white ml-auto'
          }`}
          data-testid={`message-${msg.role}-${messageIndices.get(`${msg.role}-${idx}`)}`}
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
