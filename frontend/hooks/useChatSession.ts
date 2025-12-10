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
      const res = await api.post<{ id: number }>('/chat/start', {
        userId: user.id,
        scenarioId
      });
      setSessionId(res.data.id);
    } catch (err: any) {
      setError(err.response?.data?.message || err.message || 'Failed to start session');
    } finally {
      setLoading(false);
    }
  }, [user]);

  const saveMessage = useCallback(async (currentSessionId: number, role: 'user' | 'ai', content: string) => {
    try {
      await api.post('/chat/message', {
        sessionId: currentSessionId,
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

  return {
    sessionId,
    sessions,
    loading,
    error,
    startSession,
    saveMessage,
    loadSessions
  };
};