import React, { useState } from 'react';

interface PromptInputProps {
  onSend: (prompt: string) => void;
  loading?: boolean;
  disabled?: boolean;
}

const PromptInput: React.FC<PromptInputProps> = ({ onSend, loading = false, disabled = false }) => {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && !loading && !disabled) {
      onSend(prompt.trim());
      setPrompt('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t p-4">
      <div className="flex gap-2">
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="메시지를 입력하세요..."
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
          {loading ? '전송 중...' : '전송'}
        </button>
      </div>
    </form>
  );
};

export default PromptInput;
