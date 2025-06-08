import Header from './components/Header';
import SessionList from './components/SessionList';
import ChatWindow, { ChatMessage } from './components/ChatWindow';
import PromptInput from './components/PromptInput';
import SemanticSearch from './components/SemanticSearch';
import api from './api/api';
import { useState } from 'react';

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const sessionId = 1;

  const sendPrompt = async (prompt: string) => {
    setMessages((prev) => [...prev, { role: 'user', content: prompt }]);
    setLoading(true);
    try {
      const res = await api.post<{ message: string }>('/chat', {
        session_id: sessionId,
        prompt,
      });
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: res.data.message },
      ]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <div className="flex flex-1">
        <SessionList />
        <div className="flex-1 flex flex-col">
          <ChatWindow messages={messages} />
          <PromptInput onSend={sendPrompt} loading={loading} />
        </div>
      </div>
      <SemanticSearch />
    </div>
  );
}

export default App;
