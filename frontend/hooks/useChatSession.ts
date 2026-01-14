import { useState, useCallback, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { ensureHebrew, he } from '../constants/he';

interface ChatSession {
  id: number;
  user_id: number;
  scenario_id: string;
  start_time: string;
  end_time?: string;
}

type SessionStatus = 'idle' | 'creating' | 'active' | 'error';

export const useChatSession = () => {
  const { user } = useAuth();
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [sessionStatus, setSessionStatus] = useState<SessionStatus>('idle'); // New state
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(false); // loading is now redundant with sessionStatus but kept for existing API
  const [error, setError] = useState<string | null>(null);

  console.log(`[useChatSession] Current State: sessionId=${sessionId}, sessionStatus=${sessionStatus}, user=${user?.id}`);

  const sessionIdRef = useRef<number | null>(null); // Ref to hold latest sessionId
  const sessionStatusRef = useRef<SessionStatus>('idle'); // Ref to hold latest sessionStatus

  // Update refs when state changes
  useEffect(() => {
    sessionIdRef.current = sessionId;
    sessionStatusRef.current = sessionStatus;
  }, [sessionId, sessionStatus]);

  const startSession = useCallback(async (scenarioId: string) => {
    console.log(`[useChatSession:startSession] Attempting to start session for scenarioId=${scenarioId}. Refs: status=${sessionStatusRef.current}, id=${sessionIdRef.current}`);
    if (!user) {
        console.warn("[useChatSession:startSession] Called without a user.");
        setSessionStatus('error');
        setError(he.errors.userNotAuthenticated);
        return null;
    }

    // Block if already creating or active (using refs for immediate check)
    if (sessionStatusRef.current === 'creating' || sessionStatusRef.current === 'active') {
        console.warn(`[useChatSession:startSession] Already in ${sessionStatusRef.current} state, ignoring duplicate call.`);
        return sessionIdRef.current; // Return current sessionId if active/creating
    }

    // IMMEDIATE UPDATE to prevent race conditions (e.g. double clicks)
    sessionStatusRef.current = 'creating';
    setSessionStatus('creating'); // Update state, will trigger re-render
    setLoading(true); // Keep loading for external components
    setError(null);
    console.log("[useChatSession:startSession] Setting status to 'creating'. Making API call...");
    try {
      const res = await api.post<{ id: number }>('/chat/sessions', {
        userId: user.id,
        scenarioId
      });
      console.log(`[useChatSession:startSession] API call success. New Session ID: ${res.data.id}`);
      setSessionId(res.data.id);
      setSessionStatus('active'); // Set status to active on success
      return res.data.id;
    } catch (err: unknown) {
      let message = he.errors.startSessionFailed;
      if (err && typeof err === 'object' && 'response' in err) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          message = (err as any).response?.data?.message || message;
      } else if (err instanceof Error) {
          message = err.message;
      }
      console.error("[useChatSession:startSession] API call failed:", message);
      setError(ensureHebrew(message, he.errors.startSessionFailed)||null);
      setSessionStatus('error'); // Set status to error on failure
      return null;
    } finally {
      console.log("[useChatSession:startSession] Finally block: Resetting loading.");
      setLoading(false); // Reset loading
    }
  }, [user]); // Only 'user' is a dependency for useCallback now

  const saveMessage = useCallback(async (currentSessionId: number, role: 'user' | 'ai', content: string) => {
    try {
      await api.post(`/chat/sessions/${currentSessionId}/messages`, {
        role,
        content
      });
    } catch (err) {
      console.error('[useChatSession:saveMessage] Failed to save message', err);
    }
  }, []);

  const loadSessions = useCallback(async () => {
    if (!user) {
        console.warn("[useChatSession:loadSessions] Called without user.");
        return;
    }
    setLoading(true);
    console.log(`[useChatSession:loadSessions] Loading sessions for user ${user.id}...`);
    try {
      const res = await api.get<ChatSession[]>(`/chat/users/${user.id}/sessions`);
      console.log(`[useChatSession:loadSessions] Fetched ${res.data.length} sessions.`);
      setSessions(res.data);
    } catch (err) {
      console.error('[useChatSession:loadSessions] Failed to load sessions', err);
      setError(he.errors.loadPastSessionsFailed);
    } finally {
      setLoading(false);
    }
  }, [user]);

  const loadMessages = useCallback(async (currentSessionId: number) => {
    console.log(`[useChatSession:loadMessages] Loading messages for session ${currentSessionId}...`);
    try {
        const res = await api.get(`/chat/sessions/${currentSessionId}/messages`);
        console.log(`[useChatSession:loadMessages] Fetched ${res.data.length} messages for session ${currentSessionId}.`);
        return res.data;
    } catch (err) {
        console.error("[useChatSession:loadMessages] Failed to load messages", err);
        setError(he.errors.loadSessionMessagesFailed);
        return [];
    }
  }, []);

  return {
    sessionId,
    sessionStatus, // Expose new status
    sessions,
    loading,
    error,
    startSession,
    saveMessage,
    loadSessions,
    loadMessages
  };
};
