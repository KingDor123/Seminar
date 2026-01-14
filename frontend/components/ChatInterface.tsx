"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { SCENARIOS } from '../constants/appConstants';
import { ChatMessage, Viseme } from '../types/chat';
import { useChatSession } from '../hooks/useChatSession';
import { useUserCamera } from '../hooks/useUserCamera';
import LobbyView from './LobbyView';
import FaceTimeView from './FaceTimeView';
import { useStreamingConversation } from "../hooks/useStreamingConversation";
import { AudioQueue } from "../utils/audioQueue";
import { he } from "../constants/he";

export default function ChatInterface() {
  const [isInCall, setIsInCall] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<"idle" | "listening" | "processing" | "speaking">("idle");
  const [language, setLanguage] = useState<"en-US" | "he-IL">("he-IL");
  const [selectedScenario, setSelectedScenario] = useState(SCENARIOS[0].id);

  // Database Session Hook
  const { sessionId, startSession } = useChatSession();

  // User Camera Hook
  const { userVideoRef, mediaStream, error: cameraError } = useUserCamera(isInCall);

  // Audio Playback
  const audioQueueRef = useRef<AudioQueue | null>(null);
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  const [visemes, setVisemes] = useState<Viseme[]>([]);

  useEffect(() => {
    audioQueueRef.current = new AudioQueue();
    return () => {
      // Cleanup audio queue on unmount
    };
  }, []);

  // --- Streaming Hook ---
  const handleNewMessage = useCallback((msg: ChatMessage) => {
    setMessages((prev) => {
        const lastMsg = prev[prev.length - 1];
        // If the last message is from AI and the new message is partial AI, append
        if (lastMsg && lastMsg.role === msg.role && msg.role === 'ai') {
             // Append content WITHOUT extra space for streaming tokens
             return [...prev.slice(0, -1), { ...lastMsg, content: lastMsg.content + msg.content }];
        }
        return [...prev, msg];
    });
  }, []);

  const handleAudioData = useCallback((base64: string) => {
    setIsAiSpeaking(true);
    audioQueueRef.current?.addChunk(base64);
  }, []);

  const handleError = useCallback((err: string) => {
    console.error("Streaming Error:", err);
    setStatus("idle");
  }, []);

  const { sendMessage: sendStreamMessage, isProcessing } = useStreamingConversation({
    sessionId,
    selectedScenario,
    language,
    onNewMessage: handleNewMessage,
    onThinkingStateChange: (thinking) => setStatus(thinking ? "processing" : "idle"),
    onAudioData: handleAudioData,
    onError: handleError
  });

  // --- Initial Greeting Trigger ---
  useEffect(() => {
    if (isInCall && sessionId && messages.length === 0) {
      sendStreamMessage("[START]", null);
    }
  }, [isInCall, sessionId, messages.length, sendStreamMessage]);

  // --- Recorder Logic ---
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const [isRecording, setIsRecording] = useState(false);

  const startRecording = useCallback(async () => {
    try {
      // Use existing stream from camera hook if available, else get audio only
      const stream = mediaStream || await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
            audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        sendStreamMessage(null, audioBlob);
        audioChunksRef.current = [];
      };

      audioChunksRef.current = [];
      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setStatus("listening");
    } catch (e) {
      console.error("Failed to start recording:", e);
    }
  }, [sendStreamMessage, mediaStream]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  const toggleListening = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // --- Handlers ---
  const handleStartCall = async () => {
    const id = await startSession(selectedScenario);
    if (id) {
      setIsInCall(true);
      audioQueueRef.current?.resume();
    } else {
      alert(he.errors.startChatSessionFailed);
    }
  };

  const sendMessage = (textOverride?: string) => {
      const textToSend = textOverride || input;
      if (!textToSend.trim()) return;

      // Note: useStreamingConversation handles the optimistic UI update for user messages
      sendStreamMessage(textToSend, null);
      setInput("");
  };

  const toggleLanguage = () => {
    setLanguage((prev) => (prev === "en-US" ? "he-IL" : "en-US"));
  };

  if (cameraError) {
      console.error("Camera Hook Error:", cameraError);
  }

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
      isThinking={isProcessing}
      audioElement={null}
      audioUrl={null}
      visemes={visemes}
      isGeneratingAudio={status === "speaking"}
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