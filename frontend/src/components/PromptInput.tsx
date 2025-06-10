import React, { useState } from 'react';

interface PromptInputProps {
  onSend: (prompt: string) => void;
  loading?: boolean;
  disabled?: boolean;
  onCreateSession?: (prompt: string) => void;
}

const PromptInput: React.FC<PromptInputProps> = ({ 
  onSend, 
  loading = false, 
  disabled = false,
  onCreateSession 
}) => {
  const [prompt, setPrompt] = useState('');
  const [showSessionPrompt, setShowSessionPrompt] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && !loading && !disabled) {
      if (showSessionPrompt && onCreateSession) {
        onCreateSession(prompt.trim());
        setShowSessionPrompt(false);
      } else {
        onSend(prompt.trim());
      }
      setPrompt('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.shiftKey) {
      setShowSessionPrompt(true);
      e.preventDefault();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t p-4">
      <div className="flex flex-col gap-2">
        {showSessionPrompt && (
          <div className="text-sm text-blue-600 mb-2">
            새 세션을 생성합니다. Enter를 눌러 확인하세요.
          </div>
        )}
        <div className="flex gap-2">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={showSessionPrompt ? "새 세션 이름을 입력하세요..." : "메시지를 입력하세요... (Shift + Enter: 새 세션)"}
            className="flex-1 px-3 py-2 border rounded"
            disabled={loading || disabled}
            data-testid="prompt-input"
          />
          <button
            type="submit"
            disabled={!prompt.trim() || loading || disabled}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-blue-300"
            data-testid="send-button"
          >
            {loading ? '전송 중...' : showSessionPrompt ? '세션 생성' : '전송'}
          </button>
        </div>
      </div>
    </form>
  );
};

export default PromptInput;
