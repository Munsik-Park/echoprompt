export const API_PATHS = {
  HEALTH: '/health',
  SESSIONS: '/sessions',
  SESSION: (id: number) => `/sessions/${id}`,
  CHAT: '/chat',
  QUERY: '/query',
  MESSAGES: (sessionId: number) => `/sessions/${sessionId}/messages`,
} as const;

export type ApiPath = typeof API_PATHS[keyof typeof API_PATHS]; 