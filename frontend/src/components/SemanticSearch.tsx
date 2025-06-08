import React, { useState } from 'react';
import api from '../api/api';

interface SearchResult {
  id: string;
  score: number;
  payload: {
    role: 'user' | 'assistant';
    content: string;
  };
}

interface SearchMetadata {
  query: string;
  total: number;
  min_score?: number;
  max_score?: number;
}

interface SearchResponse {
  results: SearchResult[];
  metadata: SearchMetadata;
}

interface SemanticSearchProps {
  sessionId: number;
}

const SemanticSearch: React.FC<SemanticSearchProps> = ({ sessionId }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<SearchMetadata | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    setResults([]);
    setMetadata(null);
    
    try {
      console.log('Searching with query:', query);
      const response = await api.post<SearchResponse>('/query/semantic_search', {
        query: query.trim(),
        session_id: sessionId,
        limit: 5
      });
      console.log('Search response:', response.data);
      
      if (!response.data.results || response.data.results.length === 0) {
        console.log('No search results found');
        setError('검색 결과가 없습니다.');
        return;
      }
      
      setResults(response.data.results);
      setMetadata(response.data.metadata);
    } catch (err) {
      console.error('Search error:', err);
      setError(err instanceof Error ? err.message : '검색 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4">
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Semantic search..."
          className="flex-1 p-2 border rounded"
          data-testid="search-input"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
          data-testid="search-button"
        >
          검색
        </button>
      </div>

      {error && (
        <div className="p-4 mb-4 text-red-500 bg-red-50 rounded" data-testid="search-error">
          {error}
        </div>
      )}

      {metadata && (
        <div className="mb-4 text-sm text-gray-600" data-testid="search-metadata">
          <p>검색어: {metadata.query}</p>
          <p>검색 결과 수: {metadata.total}</p>
          {metadata.min_score !== undefined && metadata.max_score !== undefined && (
            <p>유사도 점수 범위: {metadata.min_score.toFixed(3)} ~ {metadata.max_score.toFixed(3)}</p>
          )}
        </div>
      )}

      {loading && (
        <div className="flex justify-center items-center p-4" data-testid="search-loading">
          <span className="animate-spin text-2xl">⌛</span>
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="search-results space-y-4" data-testid="search-results">
          {results.map((result) => (
            <div
              key={result.id}
              className="search-result p-4 bg-white rounded shadow cursor-pointer hover:bg-gray-50"
              data-testid={`search-result-${result.id}`}
              onClick={() => {
                const messageElement = document.querySelector(`[data-message-id="${result.id}"]`);
                if (messageElement) {
                  messageElement.classList.add('highlighted-message');
                  messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
              }}
            >
              <div className="flex justify-between items-start mb-2">
                <span className="text-sm font-medium text-gray-500">
                  {result.payload.role === 'user' ? '사용자' : '어시스턴트'}
                </span>
                <span className="text-sm text-gray-400">
                  유사도: {result.score.toFixed(3)}
                </span>
              </div>
              <p className="text-gray-800">{result.payload.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SemanticSearch;
