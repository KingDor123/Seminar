// frontend/hooks/useChatSession.ts
import { useState, useCallback } from 'react';

export const useChatSession = () => {
  const [sessionId, setSessionId] = useState<number | null>(null);
  // Using hardcoded user ID 2 for demo purposes as per project context
  const userId = 2;

  // Robust API Base URL resolution
  let apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5001";
  apiBase = apiBase.replace(/\/$/, "");
  
  if (/^\d+$/.test(apiBase)) {
    apiBase = `http://localhost:${apiBase}`;
  } else if (!apiBase.startsWith("http")) {
    apiBase = `http://${apiBase}`;
  }

  const startSession = useCallback(async (scenarioId: string) => {
    try {
      const res = await fetch(`${apiBase}/api/chat/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId, scenarioId }),
      });
      if (!res.ok) throw new Error('Failed to start session');
      const data = await res.json();
      setSessionId(data.id);
      return data.id;
    } catch (err) {
      console.error('Error starting session:', err);
      return null;
    }
  }, [apiBase]);

  const saveMessage = useCallback(async (currentSessionId: number, role: 'user' | 'ai', content: string) => {
    if (!currentSessionId) return;
    try {
      await fetch(`${apiBase}/api/chat/sessions/${currentSessionId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role, content }),
      });
    } catch (err) {
      console.error('Error saving message:', err);
    }
  }, [apiBase]);

  const getSessions = useCallback(async () => {
    try {
      const res = await fetch(`${apiBase}/api/chat/users/${userId}/sessions`);
      if (!res.ok) throw new Error('Failed to fetch sessions');
      return await res.json();
    } catch (err) {
      console.error('Error fetching sessions:', err);
      return [];
    }
  }, [apiBase]);

  return { sessionId, startSession, saveMessage, getSessions };
};
