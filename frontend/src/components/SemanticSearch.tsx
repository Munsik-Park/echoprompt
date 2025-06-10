import React, { useState } from 'react';
import api from '../api/api';
import { API_PATHS } from '../api/constants';

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
      const response = await api.post<SearchResponse>('query/semantic_search', {
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
    <div className="fixed bottom-20 right-0 w-96 bg-white shadow-lg border-t border-l p-4">
      <h3 className="text-lg font-semibold mb-4">의미 검색</h3>
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="검색어를 입력하세요..."
          className="flex-1 px-3 py-2 border rounded"
          data-testid="search-input"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-blue-300"
          data-testid="search-button"
        >
          {loading ? '검색 중...' : '검색'}
        </button>
      </div>

      {error && (
        <div className="text-red-500 text-sm mb-4">
          {error === 'Network Error' ? '서버 연결에 실패했습니다. 서버가 실행 중인지 확인해주세요.' : error}
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
        <div className="mt-4" data-testid="search-results">
          <h3 className="text-lg font-semibold mb-2">검색 결과</h3>
          <ul className="space-y-2">
            {results.map((result, index) => (
              <li key={index} className="p-3 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">{result.payload.content}</p>
                <p className="text-xs text-gray-400 mt-1">유사도: {(result.score * 100).toFixed(2)}%</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default SemanticSearch;
