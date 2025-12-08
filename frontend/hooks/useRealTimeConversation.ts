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

  useEffect(() => {
    console.log("Mounted useRealTimeConversation effect");
    activeConnection.current = true;

    const connect = () => {
        // Check if we already have a valid connection or are connecting
        if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
            return; 
        }

        // Connect directly to AI Service
        const wsUrl = process.env.NEXT_PUBLIC_AI_SERVICE_URL || "ws://localhost:8000/ai/stream"; 
        console.log("Connecting to:", wsUrl);
        
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;
        ws.binaryType = "arraybuffer";

        ws.onopen = () => {
            console.log("Connected to AI Conversation Service");
            setIsConnected(true);
            onStatusChange("idle");

            // --- INITIALIZE SCENARIO ---
            const scenario = SCENARIOS.find(s => s.id === selectedScenario);
            const systemPrompt = scenario?.prompt || "You are a helpful, empathetic, and professional conversational partner. Keep your responses concise and natural, like a real phone call.";
            
            let triggerContent = "The user has just entered the call. Greet them immediately and professionally according to your role.";
            if (selectedScenario === "bank") {
                triggerContent = "The user has joined the video call. You are Dana, the bank representative. Introduce yourself and ask how you can help.";
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
            console.log(`AI Service Disconnected (Code: ${event.code}, Reason: ${event.reason}, Clean: ${event.wasClean})`);
            setIsConnected(false);
            onStatusChange("idle");
            
            // Retry if we are still "active"
            if (activeConnection.current) {
                const delay = 1000 + Math.random() * 2000; // 1-3s delay
                console.log(`Connection dropped. Retrying in ${Math.round(delay)}ms...`);
                setTimeout(() => {
                    if (activeConnection.current) connect(); 
                }, delay);
            }
        };

        ws.onerror = (err) => {
            if (activeConnection.current) {
                console.error("AI Service WebSocket Error:", err);
            }
        };
    };

    connect();

    return () => {
      console.log("Unmounting useRealTimeConversation effect - Cleaning up WebSocket...");
      activeConnection.current = false; // Prevent retries
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [selectedScenario, onTranscript, onAudioData, onStatusChange]);

  const sendAudioChunk = useCallback((data: ArrayBuffer) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    } else {
       console.warn("Cannot send audio, socket not open (State: " + wsRef.current?.readyState + ")");
    }
  }, []);

  return { isConnected, sendAudioChunk };
};
