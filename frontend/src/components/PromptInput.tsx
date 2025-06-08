import { useState } from 'react';

interface PromptInputProps {
  onSend: (text: string) => void;
  loading?: boolean;
}

function PromptInput({ onSend, loading = false }: PromptInputProps) {
  const [text, setText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    onSend(text);
    setText('');
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t flex items-center space-x-2">
      <input
        type="text"
        className="w-full border rounded p-2"
        placeholder="Type your message..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={loading}
      />
      {loading && (
        <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
      )}
    </form>
  );
}

export default PromptInput;
