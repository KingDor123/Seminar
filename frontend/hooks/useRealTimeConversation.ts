import { useState, useEffect, useRef, useCallback } from 'react';
import { SCENARIOS } from '../constants/appConstants';

interface ConversationMessage {
  role: "user" | "assistant";
  text: string;
  partial?: boolean;
}

interface UseRealTimeConversationProps {
  selectedScenario: string;
  onTranscript: (message: ConversationMessage) => void;
  onAudioData: (audioChunk: ArrayBuffer) => void;
  onStatusChange: (status: "idle" | "listening" | "processing" | "speaking") => void;
}

export const useRealTimeConversation = ({
  selectedScenario,
  onTranscript,
  onAudioData,
  onStatusChange
}: UseRealTimeConversationProps) => {
  const wsRef = useRef<WebSocket | null>(null);
  const activeConnection = useRef(false); // Track if we essentially WANT to be connected
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    if (activeConnection.current) {
        // Already active or connecting?
        if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
            return; // Skip if already connected/connecting
        }
    }
    
    activeConnection.current = true;

    // Connect directly to AI Service
    const wsUrl = "ws://localhost:8000/ai/stream"; 
    console.log("Connecting to:", wsUrl);
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
      if (!activeConnection.current) {
          ws.close();
          return;
      }
      console.log("Connected to AI Conversation Service");
      setIsConnected(true);
      onStatusChange("idle");

      // --- INITIALIZE SCENARIO ---
      const scenario = SCENARIOS.find(s => s.id === selectedScenario);
      const systemPrompt = scenario?.prompt || "You are a helpful, empathetic, and professional conversational partner. Keep your responses concise and natural, like a real phone call.";
      
      let triggerContent = "(The user has entered. Please greet them professionally according to your role.)";
      if (selectedScenario === "bank") {
           triggerContent = "(User joins the video call)";
      }

      const configPayload = {
          mode: "audio",
          system_prompt: systemPrompt,
          history: [
              { role: "user", content: triggerContent }
          ]
      };
      
      ws.send(JSON.stringify(configPayload));
      onStatusChange("processing");
    };

    ws.onmessage = (event) => {
      if (!activeConnection.current) return;
      const data = event.data;

      if (data instanceof ArrayBuffer) {
        onAudioData(data);
        onStatusChange("speaking");
      } 
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

    ws.onclose = (event) => {
      console.log(`AI Service Disconnected (Code: ${event.code}, Reason: ${event.reason})`);
      setIsConnected(false);
      onStatusChange("idle");
      
      // Only retry if we are still "active" (component mounted)
      if (activeConnection.current && !event.wasClean) {
          console.log("Connection died unexpectedly. Retrying in 3s...");
          setTimeout(() => {
              if (activeConnection.current) connect(); 
          }, 3000);
      }
    };

    ws.onerror = (err) => {
      if (activeConnection.current) {
          console.error("AI Service WebSocket Error:", err);
      }
    };

    return () => {
      // Intentionally left empty here, cleanup is handled by the useEffect return
    };
  }, [selectedScenario, onTranscript, onAudioData, onStatusChange]);

  useEffect(() => {
    connect();
    return () => {
      console.log("Cleaning up WebSocket connection...");
      activeConnection.current = false; // Prevent retries
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  const sendAudioChunk = useCallback((data: ArrayBuffer) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    }
  }, []);

  return { isConnected, sendAudioChunk };
};
