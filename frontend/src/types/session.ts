export type SessionId = number;

export interface Session {
  id: SessionId;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface SessionListProps {
  onSessionSelect: (sessionId: SessionId) => void;
  selectedSessionId: SessionId | null;
}

export interface SemanticSearchProps {
  sessionId: SessionId;
} 