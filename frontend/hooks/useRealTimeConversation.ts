import { useState, useEffect, useRef, useCallback } from 'react';
import { SCENARIOS } from '../constants/appConstants';

interface ConversationMessage {
  role: "user" | "assistant";
  text: string;
  partial?: boolean;
}

interface UseRealTimeConversationProps {
  selectedScenario: string;
  sessionId: number | null;
  onTranscript: (message: ConversationMessage) => void;
  onAudioData: (audioChunk: ArrayBuffer) => void;
  onStatusChange: (status: "idle" | "listening" | "processing" | "speaking") => void;
}

export const useRealTimeConversation = ({
  selectedScenario,
  sessionId,
  onTranscript,
  onAudioData,
  onStatusChange
}: UseRealTimeConversationProps) => {
  const wsRef = useRef<WebSocket | null>(null);
  const activeConnection = useRef(false); // Flag to indicate if connection should be active
  const [isConnected, setIsConnected] = useState(false);
  const hasSentFirstChunk = useRef(false);

  useEffect(() => {
    // Wait for sessionId before connecting
    if (!sessionId) return;

    // Set activeConnection to true when component mounts, false when it unmounts
    activeConnection.current = true;
    console.log("Conversational Hook: Initializing...");

    const connect = () => {
        // Only connect if the component is still active AND not already connecting/open
        if (!activeConnection.current || (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING))) {
            return;
        }

        const wsUrl = process.env.NEXT_PUBLIC_AI_SERVICE_URL || "ws://localhost:8000/ai/stream"; 
        console.log("Connecting to:", wsUrl);
        
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;
        ws.binaryType = "arraybuffer";

        ws.onopen = () => {
            if (!activeConnection.current) { // Check if we should still be connected
                ws.close();
                return;
            }
            console.log("✅ AI Service Connected");
            setIsConnected(true);
            onStatusChange("idle");

            const scenario = SCENARIOS.find(s => s.id === selectedScenario);
            const systemPrompt = scenario?.prompt || "You are a helpful, empathetic, and professional conversational partner. Keep your responses concise and natural, like a real phone call.";
            
            let triggerContent = "The user has just entered the call. Greet them immediately and professionally according to your role.";
            if (selectedScenario === "bank") {
                triggerContent = "The user has joined the video call. You are Dana, the bank representative. Introduce yourself and ask how you can help.";
            }

            const configPayload = {
                session_id: sessionId,
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
                } else if (msg.type === "token") {
                    // New: Handle streaming tokens for immediate feedback
                    onTranscript({ 
                        role: msg.role, 
                        text: msg.text, 
                        partial: true // Treat tokens as partial updates
                    });
                } else if (msg.type === "status") {
                    if (msg.status === "listening") {
                        hasSentFirstChunk.current = false; // Reset for next turn
                    }
                    onStatusChange(msg.status);
                }
                } catch (e) {
                console.error("Failed to parse WebSocket message:", e);
                }
            }
        };

        ws.onclose = (event) => {
            if (!activeConnection.current) {
                console.log("Conversational Hook: WebSocket closed cleanly due to unmount.");
                return;
            }
            console.log(`❌ AI Service Disconnected (Code: ${event.code}, Reason: ${event.reason})`);
            setIsConnected(false);
            onStatusChange("idle");
            
            // Retry connection if component is still active
            const delay = 1000 + Math.random() * 2000; // 1-3s delay
            console.log(`Connection dropped. Retrying in ${Math.round(delay)}ms...`);
            setTimeout(() => {
                if (activeConnection.current) connect(); 
            }, delay);
        };

        ws.onerror = (err) => {
            if (activeConnection.current) { // Only log if we still care about this connection
                console.error("⚠️ AI Service WebSocket Error:", err);
            }
        };
    };

    connect();

    // Cleanup function
    return () => {
      console.log("Conversational Hook: Cleaning up WebSocket...");
      activeConnection.current = false; // Prevent further auto-reconnects
      if (wsRef.current) {
        wsRef.current.close(1000, "Component unmounted"); // Close cleanly
        wsRef.current = null;
      }
      setIsConnected(false);
      onStatusChange("idle");
    };
  }, [selectedScenario, sessionId, onTranscript, onAudioData, onStatusChange]);

  const sendAudioChunk = useCallback((data: ArrayBuffer) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      if (!hasSentFirstChunk.current) {
         // Send audio_start metadata before the first audio chunk of a turn
         wsRef.current.send(JSON.stringify({
             type: "user_started_speaking",
             timestamp: Date.now()
         }));
         hasSentFirstChunk.current = true;
      }
      wsRef.current.send(data);
    } else {
       console.warn("Cannot send audio, socket not open (State: " + wsRef.current?.readyState + ")");
    }
  }, []);

  const notifyAiFinishedSpeaking = useCallback(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
              type: "ai_stopped_speaking",
              timestamp: Date.now()
          }));
      }
  }, []);

  return { isConnected, sendAudioChunk, notifyAiFinishedSpeaking };
};