// frontend/hooks/useChatSession.ts
import { useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';

interface ChatSession {
  id: number;
  user_id: number;
  scenario_id: string;
  start_time: string;
  end_time?: string;
}

export const useChatSession = () => {
  const { user } = useAuth();
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startSession = useCallback(async (scenarioId: string) => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      // api is axios instance with baseURL set to /api
      const res = await api.post<{ id: number }>('/chat/sessions', {
        userId: user.id,
        scenarioId
      });
      setSessionId(res.data.id);
      return res.data.id;
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const message = (err as any).response?.data?.message || (err as Error).message || 'Failed to start session';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [user]);

  const saveMessage = useCallback(async (currentSessionId: number, role: 'user' | 'ai', content: string) => {
    try {
      await api.post(`/chat/sessions/${currentSessionId}/messages`, {
        role,
        content
      });
    } catch (err) {
      console.error('Failed to save message', err);
    }
  }, []);

  const loadSessions = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const res = await api.get<ChatSession[]>(`/chat/users/${user.id}/sessions`);
      setSessions(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [user]);

  const loadMessages = useCallback(async (currentSessionId: number) => {
    try {
        const res = await api.get(`/chat/sessions/${currentSessionId}/messages`);
        return res.data;
    } catch (err) {
        console.error("Failed to load messages", err);
        return [];
    }
  }, []);

  return {
    sessionId,
    sessions,
    loading,
    error,
    startSession,
    saveMessage,
    loadSessions,
    loadMessages
  };
};