import { useState, useEffect, useRef, useCallback } from 'react';

interface ConversationMessage {
  role: "user" | "assistant";
  text: string;
  partial?: boolean;
}

interface UseRealTimeConversationProps {
  onTranscript: (message: ConversationMessage) => void;
  onAudioData: (audioChunk: ArrayBuffer) => void;
  onStatusChange: (status: "idle" | "listening" | "processing" | "speaking") => void;
}

export const useRealTimeConversation = ({
  onTranscript,
  onAudioData,
  onStatusChange
}: UseRealTimeConversationProps) => {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    // Connect directly to AI Service
    // In a real deploy, this should be an env var or proxied
    const wsUrl = "ws://localhost:8000/ws/conversation"; 
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.binaryType = "arraybuffer"; // Important for receiving audio

    ws.onopen = () => {
      console.log("Connected to AI Conversation Service");
      setIsConnected(true);
      onStatusChange("idle");
    };

    ws.onmessage = (event) => {
      const data = event.data;

      // Binary Data = Audio Chunk (TTS)
      if (data instanceof ArrayBuffer) {
        onAudioData(data);
        onStatusChange("speaking");
      } 
      // Text Data = JSON Control Messages
      else if (typeof data === "string") {
        try {
          const msg = JSON.parse(data);
          
          if (msg.type === "transcript") {
            onTranscript({ 
              role: msg.role, 
              text: msg.text, 
              partial: msg.partial 
            });
          } else if (msg.type === "status") {
            onStatusChange(msg.status);
          }
        } catch (e) {
          console.error("Failed to parse WebSocket message:", e);
        }
      }
    };

    ws.onclose = () => {
      console.log("AI Service Disconnected");
      setIsConnected(false);
      onStatusChange("idle");
    };

    ws.onerror = (err) => {
      console.error("AI Service WebSocket Error:", err);
    };

    return () => {
      ws.close();
    };
  }, [onTranscript, onAudioData, onStatusChange]);

  useEffect(() => {
    const cleanup = connect();
    return cleanup;
  }, [connect]);

  const sendAudioChunk = useCallback((data: ArrayBuffer) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    }
  }, []);

  return { isConnected, sendAudioChunk };
};
