// frontend/hooks/useChatWebSocket.ts
import { useState, useEffect, useRef, useCallback } from 'react';
import { SCENARIOS } from '../constants/appConstants';
import { useWebSocketUrl } from './useApi';

interface ChatMessage {
  role: "user" | "ai";
  content: string;
}

interface UseChatWebSocketProps {
  language: "en-US" | "he-IL";
  selectedScenario: string;
  messages: ChatMessage[]; // Add messages prop for history
  handleTTS: (chunk: string) => void;
  onNewAIMessage: (message: ChatMessage) => void;
  onThinkingStateChange: (isThinking: boolean) => void;
}

export const useChatWebSocket = ({
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  language,
  selectedScenario,
  messages,
  handleTTS,
  onNewAIMessage,
  onThinkingStateChange,
}: UseChatWebSocketProps) => {
  const wsRef = useRef<WebSocket | null>(null);
  const getWsUrl = useWebSocketUrl();
  
  // Track if we've started the conversation for this session
  const hasStartedRef = useRef(false);

  // States
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    let retryAttempt = 0;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let isUnmounted = false;

    const internalConnect = () => {
      if (isUnmounted) return;

      const wsUrl = getWsUrl('/api/chat');
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("Connected to Chat Server");
        retryAttempt = 0;
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        if (wsRef.current !== ws) return;

        const text = event.data;
        onThinkingStateChange(false);
        handleTTS(text);
        onNewAIMessage({ role: "ai", content: text });
      };

      ws.onclose = () => {
        if (isUnmounted) return;
        console.log("Chat Server Disconnected - retrying...");
        setIsConnected(false);
        const delay = Math.min(1000 * 2 ** retryAttempt, 10000);
        reconnectTimer = setTimeout(internalConnect, delay);
        retryAttempt += 1;
      };

      ws.onerror = (err) => {
        console.error("WebSocket Error:", err);
        ws.close();
      };
    };

    internalConnect();

    return () => {
      isUnmounted = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (wsRef.current) {
        wsRef.current.onmessage = null;
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.close();
      }
    };
  }, [getWsUrl, handleTTS, onNewAIMessage, onThinkingStateChange]);

  useEffect(() => {
    const disconnect = connect();
    return () => disconnect();
  }, [connect]);

  // Reset start flag when scenario changes
  useEffect(() => {
    hasStartedRef.current = false;
  }, [selectedScenario]);

  const sendPayload = useCallback((systemPrompt: string, history: ChatMessage[]) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        return;
    }
    const payload = {
        system_prompt: systemPrompt,
        history: history
    };
    wsRef.current.send(JSON.stringify(payload));
  }, []);

  const sendMessage = useCallback((textToSend: string) => {
    const scenario = SCENARIOS.find(s => s.id === selectedScenario);
    const systemPrompt = scenario?.prompt || "You are a helpful assistant.";
    
    // Construct history: current messages + new user message
    const history = [...messages, { role: "user", content: textToSend } as ChatMessage];
    
    sendPayload(systemPrompt, history);
  }, [selectedScenario, messages, sendPayload]);

  // Initial Greeting Logic
  useEffect(() => {
    if (isConnected && !hasStartedRef.current && messages.length === 0) {
        // Start the conversation automatically
        const scenario = SCENARIOS.find(s => s.id === selectedScenario);
        const systemPrompt = scenario?.prompt || "You are a helpful assistant.";
        
        let triggerContent = "(The user has entered. Please greet them professionally according to your role.)";
        
        if (selectedScenario === "bank") {
             triggerContent = "(User joins the video call)";
        }

        const triggerMessage = { role: "user", content: triggerContent } as ChatMessage;
        
        onThinkingStateChange(true);
        sendPayload(systemPrompt, [triggerMessage]);
        hasStartedRef.current = true;
    }
  }, [isConnected, messages.length, selectedScenario, sendPayload, onThinkingStateChange]);

  return { sendMessage, isConnected, wsRef };
};


