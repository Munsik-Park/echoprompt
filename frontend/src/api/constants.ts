export const API_PATHS = {
  BASE_URL: 'http://localhost:8000/api/v1',
  HEALTH: '/health',
  SESSIONS: '/sessions',
  SESSION: (id: number) => `/sessions/${id}`,
  CHAT: '/chat',
  QUERY: '/query',
  MESSAGES: '/messages',
  SESSION_MESSAGES: (sessionId: number) => `/sessions/${sessionId}/messages`,
  SESSION_UPDATE: (id: number) => `/sessions/${id}`,
  MESSAGE: (id: number) => `/messages/${id}`,
  MESSAGE_UPDATE: (id: number) => `/messages/${id}`,
} as const;

export type ApiPath = typeof API_PATHS[keyof typeof API_PATHS]; 