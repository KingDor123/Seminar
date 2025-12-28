"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { SCENARIOS } from '../constants/appConstants';
import { ChatMessage, Viseme } from '../types/chat';
import { useChatSession } from '../hooks/useChatSession';
import LobbyView from './LobbyView';
import FaceTimeView from './FaceTimeView';
import { useStreamingConversation } from "../hooks/useStreamingConversation";
import { AudioQueue } from "../utils/audioQueue";

export default function ChatInterface() {
  const [isInCall, setIsInCall] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  
  const [input, setInput] = useState(""); 
  const [status, setStatus] = useState<"idle" | "listening" | "processing" | "speaking">("idle");
  const [language, setLanguage] = useState<"en-US" | "he-IL">("he-IL");
  const [selectedScenario, setSelectedScenario] = useState(SCENARIOS[0].id);

  // Database Session Hook
  const { sessionId, startSession } = useChatSession();

  // User Camera
  const userVideoRef = useRef<HTMLVideoElement>(null);
  const localStreamRef = useRef<MediaStream | null>(null);

  // Audio Playback
  const audioQueueRef = useRef<AudioQueue | null>(null);
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  const [visemes] = useState<Viseme[]>([]); 

  useEffect(() => {
    // Initialize AudioQueue
    audioQueueRef.current = new AudioQueue();
  }, []);

  // --- Streaming Hook ---
  const handleNewMessage = useCallback((msg: ChatMessage) => {
    setMessages((prev) => {
        // If the last message is from AI, append to it (simple heuristic for streaming)
        // However, the backend might send full sentences or partials.
        // My SSE implementation sends "partial: true" for chunks.
        // The hook I wrote in `useStreamingConversation` sends { role, content }.
        // Let's assume the hook sends what we need.
        // If it's a new message event from SSE, we append.
        
        // *Correction*: The SSE hook logic I wrote earlier:
        // onmessage: if (transcript) -> onNewMessage({ role, content })
        // It doesn't distinguish partials in the callback *signature*, but the logic inside `useStreamingConversation` was:
        // `onNewMessage({ role: ..., content: data.text })`
        // We need to handle appending here if we want smooth streaming text.
        
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.role === msg.role && msg.role === 'ai') {
             // If we assume the backend sends *chunks* (words/sentences) and not the *full text so far*:
             return [...prev.slice(0, -1), { ...lastMsg, content: lastMsg.content + " " + msg.content }];
        }
        return [...prev, msg];
    });
  }, []);

  const handleAudioData = useCallback((base64: string) => {
    setIsAiSpeaking(true);
    // Add to queue
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
    onThinkingStateChange: (thinking) => setStatus(thinking ? "processing" : "idle"), // naive status mapping
    onAudioData: handleAudioData,
    onError: handleError
  });

  // --- Recorder Logic (Simple Manual Implementation for Blob) ---
  // Since we need a blob to send *after* recording, not a stream of chunks.
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const [isRecording, setIsRecording] = useState(false);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
            audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' }); // or 'audio/webm' depending on browser
        // Send to API
        sendStreamMessage(null, audioBlob);
        
        // Cleanup
        audioChunksRef.current = [];
        stream.getTracks().forEach(t => t.stop());
      };

      audioChunksRef.current = [];
      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setStatus("listening");
    } catch (e) {
      console.error("Failed to start recording:", e);
    }
  }, [sendStreamMessage]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      // Status will flip to "processing" when `sendStreamMessage` is called in onstop
    }
  }, []);

  const toggleListening = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // --- Cleanup ---
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


  // --- Handlers ---
  const handleStartCall = async () => {
    const id = await startSession(selectedScenario);
    if (id) {
      setIsInCall(true);
      // Resume audio context just in case
      audioQueueRef.current?.resume();
    } else {
      alert("Failed to start chat session. Check console/backend.");
    }
  };

  const sendMessage = (textOverride?: string) => {
      const textToSend = textOverride || input;
      if (!textToSend.trim()) return;
      
      // Update UI immediately for user message
      setMessages(prev => [...prev, { role: "user", content: textToSend }]);
      setInput("");
      
      // Send
      sendStreamMessage(textToSend, null);
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
      isThinking={isProcessing}
      audioElement={null}
      audioUrl={null}
      visemes={visemes}
      isGeneratingAudio={status === "speaking"} // Adjust logic as needed
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
