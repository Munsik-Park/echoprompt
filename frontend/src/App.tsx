import Header from './components/Header';
import SessionList from './components/SessionList';
import ChatWindow from './components/ChatWindow';
import PromptInput from './components/PromptInput';
import SemanticSearch from './components/SemanticSearch';

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <div className="flex flex-1">
        <SessionList />
        <div className="flex-1 flex flex-col">
          <ChatWindow />
          <PromptInput />
        </div>
      </div>
      <SemanticSearch />
    </div>
  );
}

export default App;
