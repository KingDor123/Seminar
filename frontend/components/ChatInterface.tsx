"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Avatar3D from "./Avatar3D";
import { SCENARIOS } from '../constants/appConstants';
import { ChatMessage } from '../types/chat';
import { useUserCamera } from '../hooks/useUserCamera';
import { useChatSession } from '../hooks/useChatSession';
import LobbyView from './LobbyView';
import FaceTimeView from './FaceTimeView';
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import { useRealTimeConversation } from "../hooks/useRealTimeConversation";

export default function ChatInterface() {
  const [isInCall, setIsInCall] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesRef = useRef<ChatMessage[]>([]);
  
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const [input, setInput] = useState(""); // Kept for fallback manual entry if needed
  const [status, setStatus] = useState<"idle" | "listening" | "processing" | "speaking">("idle");
  const [language, setLanguage] = useState<"en-US" | "he-IL">("he-IL");
  const [selectedScenario, setSelectedScenario] = useState(SCENARIOS[0].id);

  // Debug logging
  useEffect(() => {
    console.log("Current Selected Scenario:", selectedScenario);
  }, [selectedScenario]);

  // Database Session Hook
  const { sessionId, startSession, saveMessage } = useChatSession();

  // User Camera
  const userVideoRef = useRef<HTMLVideoElement>(null);
  const localStreamRef = useRef<MediaStream | null>(null);

  // --- Audio Playback Logic (Queue System) ---
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueue = useRef<ArrayBuffer[]>([]);
  const isPlayingRef = useRef(false);
  // We expose this for the UI to know if AI is speaking
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  // Visemes placeholder (since raw audio pipeline doesn't return visemes yet)
  const [visemes, setVisemes] = useState<any[]>([]); 

  const playNextChunk = useCallback(async () => {
    if (audioQueue.current.length === 0) {
      isPlayingRef.current = false;
      setIsAiSpeaking(false);
      return;
    }

    isPlayingRef.current = true;
    setIsAiSpeaking(true);

    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }

    const ctx = audioContextRef.current;
    const chunk = audioQueue.current.shift();
    
    if (!chunk) return;

    try {
      // Decode the audio data (MP3/WAV from EdgeTTS)
      // Note: decodeAudioData separates the decoding from the main thread usually
      const audioBuffer = await ctx.decodeAudioData(chunk);
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);
      
      source.onended = () => {
        playNextChunk();
      };
      
      source.start(0);
    } catch (err) {
      console.error("Error decoding audio chunk:", err);
      playNextChunk(); // Skip bad chunk
    }
  }, []);

  const handleAudioData = useCallback((data: ArrayBuffer) => {
    // Clone buffer because decodeAudioData detaches it
    const bufferCopy = data.slice(0); 
    audioQueue.current.push(bufferCopy);
    
    if (!isPlayingRef.current) {
      playNextChunk();
    }
  }, [playNextChunk]);

  // --- Real-Time Hook Integration ---
  const handleTranscript = useCallback((msg: { role: "user" | "assistant", text: string, partial?: boolean }) => {
    setMessages((prev) => {
      // If it's a partial update (streaming token), update the last message if it matches role
      if (msg.partial) {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.role === "ai") { 
            // Note: msg.role from hook is "assistant", we use "ai" in frontend types usually
            // If the hook sends entire chunks (sentences), we might append. 
            // The backend sends full sentences in 'text' field when partial=True currently? 
            // Let's assume 'text' is the chunk to append or replace.
            // Looking at backend: "transcript" with partial=True sends the NEW sentence.
            
            // Logic: If the last message is "ai", append.
             return [
                ...prev.slice(0, -1),
                { ...lastMsg, content: lastMsg.content + " " + msg.text } // simplistic append
             ];
        } else {
             return [...prev, { role: "ai", content: msg.text }];
        }
      } 
      
      // Standard full message (User or final AI)
      const role = msg.role === "assistant" ? "ai" : "user";
      return [...prev, { role: role as "user" | "ai", content: msg.text }];
    });
  }, []);

  const handleStatusChange = useCallback((newStatus: "idle" | "listening" | "processing" | "speaking") => {
    setStatus(newStatus);
  }, []);

  const { isConnected, sendAudioChunk } = useRealTimeConversation({
    selectedScenario: selectedScenario,
    onTranscript: handleTranscript,
    onAudioData: handleAudioData,
    onStatusChange: handleStatusChange
  });

  // --- Audio Recording ---
  const { isRecording, startRecording, stopRecording } = useAudioRecorder({
    onAudioData: sendAudioChunk,
    onError: (err) => console.error("Recorder error:", err)
  });

  // --- Lifecycle & Cleanup ---
  useEffect(() => {
    // Cleanup AudioContext
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Cleanup camera stream
  useEffect(() => {
    const stopLocalStream = () => {
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => track.stop());
        localStreamRef.current = null;
      }
      if (userVideoRef.current) {
        userVideoRef.current.srcObject = null;
      }
    };

    if (isInCall && userVideoRef.current) {
      navigator.mediaDevices.getUserMedia({ video: true, audio: false }) // Audio handled by recorder
        .then(stream => {
          if (userVideoRef.current) userVideoRef.current.srcObject = stream;
          localStreamRef.current = stream;
        })
        .catch(err => console.error("Camera Error:", err));
    } else {
      stopLocalStream();
    }
    return stopLocalStream;
  }, [isInCall]);


  // --- Handlers ---
  const handleStartCall = async () => {
    const id = await startSession(selectedScenario);
    if (id) {
      setIsInCall(true);
    } else {
      alert("Failed to start chat session. Check console/backend.");
    }
  };

  const toggleListening = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };
  
  const sendMessage = (textOverride?: string) => {
      // Use textOverride if provided, otherwise use input state
      const textToSend = textOverride || input;
      console.warn("Text sending not yet implemented in new pipeline. Would send:", textToSend);
  };

  const toggleLanguage = () => {
    setLanguage((prev) => (prev === "en-US" ? "he-IL" : "en-US"));
  };

  if (!isInCall) {
    return (
      <LobbyView
        selectedScenario={selectedScenario}
        setSelectedScenario={setSelectedScenario}
        language={language}
        toggleLanguage={toggleLanguage}
        onStartCall={handleStartCall}
      />
    );
  }

  return (
    <FaceTimeView
      messages={messages}
      isThinking={status === "processing"}
      audioElement={null} // Not using HTMLAudioElement anymore
      audioUrl={null}     // Not using blob URLs anymore
      visemes={visemes}
      isGeneratingAudio={status === "processing" || status === "speaking"}
      isAiSpeaking={isAiSpeaking}
      userVideoRef={userVideoRef}
      isSpeechRecognitionListening={isRecording}
      startListening={toggleListening}
      onEndCall={() => setIsInCall(false)}
      input={input}
      setInput={setInput}
      sendMessage={sendMessage}
      selectedScenario={selectedScenario}
      audioRef={() => {}} 
    />
  );
}