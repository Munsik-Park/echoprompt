export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatWindowProps {
  messages: ChatMessage[];
}

function ChatWindow({ messages }: ChatWindowProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-2">
      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={`max-w-sm p-2 rounded ${
            msg.role === 'assistant'
              ? 'bg-gray-100 text-gray-800'
              : 'bg-blue-600 text-white ml-auto'
          }`}
        >
          {msg.content}
        </div>
      ))}
    </div>
  );
}

export default ChatWindow;
