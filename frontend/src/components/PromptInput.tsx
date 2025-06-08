import { useState } from 'react';

interface PromptInputProps {
  onSend: (prompt: string) => void;
  loading: boolean;
  disabled?: boolean;
}

function PromptInput({ onSend, loading, disabled }: PromptInputProps) {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && !loading && !disabled) {
      onSend(prompt.trim());
      setPrompt('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t">
      <div className="flex gap-2">
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={disabled ? "세션을 선택해주세요" : "메시지를 입력하세요..."}
          className="flex-1 p-2 border rounded"
          disabled={loading || disabled}
          data-testid="message-input"
        />
        <button
          type="submit"
          disabled={!prompt.trim() || loading || disabled}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
          data-testid="send-button"
        >
          {loading ? '전송 중...' : '전송'}
        </button>
      </div>
    </form>
  );
}

export default PromptInput;
