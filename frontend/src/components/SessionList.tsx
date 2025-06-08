import { useState, useEffect } from 'react';
import api from '../api/api';
import { useSessions } from '../hooks/useSessions';

interface Session {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
}

export default function SessionList() {
  const { sessions, loading, error, refetch } = useSessions();

  if (loading) {
    return (
      <aside className="w-64 border-r overflow-y-auto p-4" data-testid="session-list">
        <h2 className="text-lg font-semibold mb-4">Session List</h2>
        <div className="p-4" data-testid="loading-sessions">Loading sessions...</div>
      </aside>
    );
  }

  if (error) {
    return (
      <aside className="w-64 border-r overflow-y-auto p-4" data-testid="session-list">
        <h2 className="text-lg font-semibold mb-4">Session List</h2>
        <div className="p-4 text-red-500" data-testid="session-error">
          <p>Error: {error}</p>
          <button 
            onClick={refetch}
            className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            data-testid="retry-button"
          >
            Retry
          </button>
        </div>
      </aside>
    );
  }

  if (!sessions || sessions.length === 0) {
    return (
      <aside className="w-64 border-r overflow-y-auto p-4" data-testid="session-list">
        <h2 className="text-lg font-semibold mb-4">Session List</h2>
        <div className="p-4" data-testid="no-sessions">No sessions found</div>
      </aside>
    );
  }

  return (
    <aside className="w-64 border-r overflow-y-auto p-4" data-testid="session-list">
      <h2 className="text-lg font-semibold mb-4">Session List</h2>
      <div className="space-y-2">
        {sessions.map((session) => (
          <div
            key={session.id}
            data-testid={`session-${session.id}`}
            className="p-4 border rounded hover:bg-gray-50 cursor-pointer"
          >
            <h3 className="font-medium">{session.name}</h3>
            <p className="text-sm text-gray-500">
              Created: {new Date(session.created_at).toLocaleString()}
            </p>
          </div>
        ))}
      </div>
    </aside>
  );
}
