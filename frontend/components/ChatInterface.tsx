"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Image from "next/image";
import Avatar3D from "./Avatar3D";
import { useTTS, useWebSocketUrl } from '../hooks/useApi';
import { SCENARIOS } from '../constants/appConstants';
import { useChatWebSocket } from '../hooks/useChatWebSocket';
import { ChatMessage } from '../types/chat';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useUserCamera } from '../hooks/useUserCamera';
import { useChatSession } from '../hooks/useChatSession';
import LobbyView from './LobbyView';
import FaceTimeView from './FaceTimeView';

export default function ChatInterface() {
  const [isInCall, setIsInCall] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]); // Using ChatMessage type
  const messagesRef = useRef<ChatMessage[]>([]); // Ref to access latest messages in effects
  
  // Sync ref with state
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [isListening, setIsListening] = useState(false); // This state will be managed by useSpeechRecognition
  const [language, setLanguage] = useState<"en-US" | "he-IL">("he-IL");
  const [selectedScenario, setSelectedScenario] = useState(SCENARIOS[0].id);
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);

  // Database Session Hook
  const { sessionId, startSession, saveMessage } = useChatSession();

  // User Camera
  const userVideoRef = useRef<HTMLVideoElement>(null);
  const localStreamRef = useRef<MediaStream | null>(null);

  // Audio / TTS
  const ttsBuffer = useRef("");
  // Use state for audio element to ensure re-renders when ref updates
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);

  // Use the new API hooks
  const { speak, isGeneratingAudio, audioUrl, updateAudioUrl, visemes } = useTTS();

  const handleTTS = useCallback((chunk: string) => {
    ttsBuffer.current += chunk;
    // Speak on sentence endings or long pauses
    if (/[.?!](\s|$)/.test(ttsBuffer.current) || ttsBuffer.current.length > 150) {
      speak(ttsBuffer.current, language);
      ttsBuffer.current = "";
    }
  }, [language, speak]);

  const onNewAIMessage = useCallback((newMessage: ChatMessage) => {
    setMessages((prev) => {
      const lastMsg = prev[prev.length - 1];
      // Check if last AI message exists and is not empty, then append
      if (lastMsg && lastMsg.role === "ai" && lastMsg.content !== "") {
        return [
          ...prev.slice(0, -1),
          { ...lastMsg, content: lastMsg.content + newMessage.content },
        ];
      } else {
        // Otherwise, add new message
        return [...prev, newMessage];
      }
    });
  }, []);

  // Use the new WebSocket hook
  const { sendMessage: sendWebSocketMessage, wsRef } = useChatWebSocket({
    language,
    selectedScenario,
    messages,
    handleTTS,
    onNewAIMessage,
    onThinkingStateChange: setIsThinking,
  });

  const sendMessage = useCallback((textOverride?: string) => {
    const textToSend = textOverride || input;
    if (!textToSend.trim()) return;

    // Add User Message locally
    setMessages((prev) => [...prev, { role: "user", content: textToSend }]);
    setIsThinking(true);

    // Save to DB
    if (sessionId) {
      saveMessage(sessionId, 'user', textToSend);
    }

    sendWebSocketMessage(textToSend); // Use the sendMessage from the hook
    setInput("");
  }, [input, sendWebSocketMessage, sessionId, saveMessage]);

  const onSpeechTranscript = useCallback((transcript: string) => {
    sendMessage(transcript);
  }, [sendMessage]);

  const onSpeechError = useCallback((error: any) => {
    console.error("ChatInterface Speech Recognition Error:", error);
  }, []);

  const {
    isListening: isSpeechRecognitionListening,
    startListening: startSpeechRecognition,
  } = useSpeechRecognition({
    language,
    onTranscript: onSpeechTranscript,
    onError: onSpeechError,
  });

  // Handle AI speaking state when audio is generating or plays
  useEffect(() => {
    setIsAiSpeaking(isGeneratingAudio || (audioUrl !== null));
  }, [isGeneratingAudio, audioUrl]);

  // Save AI message when speaking finishes
  useEffect(() => {
    if (!isAiSpeaking && sessionId && messagesRef.current.length > 0) {
      const lastMsg = messagesRef.current[messagesRef.current.length - 1];
      // Determine if this was an AI turn that just finished
      if (lastMsg.role === 'ai') {
         saveMessage(sessionId, 'ai', lastMsg.content);
      }
    }
  }, [isAiSpeaking, sessionId, saveMessage]);

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
      navigator.mediaDevices.getUserMedia({ video: true, audio: false })
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

  const startListening = () => {
    startSpeechRecognition();
  };

  const handleStartCall = async () => {
    const id = await startSession(selectedScenario);
    if (id) {
      setIsInCall(true);
    } else {
      alert("Failed to start chat session. Check console/backend.");
    }
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
      isThinking={isThinking}
      audioElement={audioElement}
      audioUrl={audioUrl}
      visemes={visemes}
      isGeneratingAudio={isGeneratingAudio}
      isAiSpeaking={isAiSpeaking}
      userVideoRef={userVideoRef}
      isSpeechRecognitionListening={isSpeechRecognitionListening}
      startListening={startListening}
      onEndCall={() => setIsInCall(false)}
      input={input}
      setInput={setInput}
      sendMessage={sendMessage}
      selectedScenario={selectedScenario}
      audioRef={setAudioElement} // Pass setter as ref callback
    />
  );
}