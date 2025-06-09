import api from './api';
import { API_PATHS } from './constants';
import { Session } from '../types/session';

export const getSessions = () => api.get<Session[]>(API_PATHS.SESSIONS);
export const createSession = (data: { name: string }) => api.post<Session>(API_PATHS.SESSIONS, data);
export const getSession = (id: number) => api.get<Session>(API_PATHS.SESSION(id));
export const deleteSession = (id: number) => api.delete(API_PATHS.SESSION(id)); 