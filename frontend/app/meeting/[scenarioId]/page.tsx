"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useRouter } from 'next/navigation';
import FaceTimeView from '../../../components/FaceTimeView';
import { ChatMessage } from '../../../types/chat';
import { useUserCamera } from '../../../hooks/useUserCamera';
import { useChatSession } from '../../../hooks/useChatSession';
import { useAuth } from "../../../context/AuthContext";
import { useStreamingConversation } from "../../../hooks/useStreamingConversation";
import { AudioQueue } from "../../../utils/audioQueue";

export default function MeetingPage() {
  const { user, isLoading } = useAuth();
  const params = useParams();
  const router = useRouter();
  const scenarioId = params.scenarioId as string;
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<"idle" | "listening" | "processing" | "speaking">("idle");
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  
  // Database Session Hook
  const { startSession, sessionId, loadMessages } = useChatSession();

  // User Camera
  const { userVideoRef, mediaStream } = useUserCamera(!!user);

  // Audio Queue
  const audioQueueRef = useRef<AudioQueue | null>(null);

  useEffect(() => {
    audioQueueRef.current = new AudioQueue();
  }, []);

  // --- Session Start Logic ---
  useEffect(() => {
    if (scenarioId && user) {
      startSession(scenarioId).then(id => {
        console.log(`Session started: ${id} for scenario: ${scenarioId}`);
        if (id) {
            loadMessages(id).then(msgs => {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const formattedMsgs = msgs.map((m: any) => ({
                    role: m.role === 'ai' ? 'ai' : 'user',
                    content: m.content
                }));
                setMessages(formattedMsgs);
            });
            // Resume audio context if needed
            audioQueueRef.current?.resume();
        }
      });
    }
  }, [scenarioId, startSession, loadMessages, user]);


  // --- Streaming Conversation Hook ---
  const handleNewMessage = useCallback((msg: ChatMessage) => {
    setMessages((prev) => {
        // Simple append logic for now. 
        // If we want smooth partial updates, we check if last msg is AI and append.
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.role === msg.role && msg.role === 'ai') {
             return [...prev.slice(0, -1), { ...lastMsg, content: lastMsg.content + " " + msg.content }];
        }
        return [...prev, msg];
    });
  }, []);

  const handleAudioData = useCallback((base64: string) => {
    setIsAiSpeaking(true);
    audioQueueRef.current?.addChunk(base64);
    // Note: We might want a way to know when playback *finishes* to set isAiSpeaking=false.
    // The AudioQueue logic I wrote is simple fire-and-forget for the UI state in this version.
    // Ideally AudioQueue would accept a callback for "onEmpty".
    // For now, let's leave it as is or improve AudioQueue later.
  }, []);

  const handleError = useCallback((err: string) => {
    console.error("Streaming Error:", err);
    setStatus("idle");
  }, []);

  const { sendMessage: sendStreamMessage, isProcessing } = useStreamingConversation({
    sessionId,
    selectedScenario: scenarioId,
    onNewMessage: handleNewMessage,
    onThinkingStateChange: (thinking) => setStatus(thinking ? "processing" : "idle"),
    onAudioData: handleAudioData,
    onError: handleError
  });


  // --- Audio Recording Logic (Manual Blob Accumulation) ---
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const [isRecording, setIsRecording] = useState(false);

  const startRecording = useCallback(async () => {
    try {
        // Use the existing mediaStream if available (from useUserCamera), else request audio
        let stream = mediaStream;
        if (!stream) {
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        }

        // Check if stream has audio tracks
        if (stream.getAudioTracks().length === 0) {
            console.warn("No audio tracks in stream, requesting new audio stream...");
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        }

        const recorder = new MediaRecorder(stream);
        
        recorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
                audioChunksRef.current.push(e.data);
            }
        };

        recorder.onstop = () => {
            const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
            console.log("Sending Audio Blob:", audioBlob.size);
            sendStreamMessage(null, audioBlob);
            
            audioChunksRef.current = [];
            // If we created a temporary stream (not from camera), stop it?
            // If it's from `mediaStream`, we shouldn't stop tracks as it kills the camera audio too.
            // But MediaRecorder doesn't kill tracks on stop.
        };

        audioChunksRef.current = [];
        recorder.start();
        mediaRecorderRef.current = recorder;
        setIsRecording(true);
        setStatus("listening");
    } catch (e) {
      console.error("Failed to start recording:", e);
    }
  }, [mediaStream, sendStreamMessage]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      // Status will flip to processing via hook
    }
  }, []);

  const toggleListening = async () => {
    // Resume AudioContext context just in case
    audioQueueRef.current?.resume();

    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const sendMessage = (textOverride?: string) => {
      const textToSend = textOverride || input;
      if (!textToSend.trim()) return;
      
      setMessages(prev => [...prev, { role: "user", content: textToSend }]);
      setInput("");
      
      sendStreamMessage(textToSend, null);
  };

  const handleEndCall = () => {
    router.push('/home');
  };

  if (isLoading) {
      return <div className="flex h-screen items-center justify-center bg-black text-white">Initializing Meeting...</div>;
  }

  if (!user) {
      return null;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-black font-sans">
        <main className="flex flex-col items-center w-full max-w-6xl p-4">
            <FaceTimeView
            messages={messages}
            isThinking={isProcessing}
            audioElement={null}
            audioUrl={null}
            visemes={[]}
            isGeneratingAudio={status === "processing" || status === "speaking"}
            isAiSpeaking={isAiSpeaking}
            userVideoRef={userVideoRef}
            isSpeechRecognitionListening={isRecording}
            startListening={toggleListening}
            onEndCall={handleEndCall}
            input={input}
            setInput={setInput}
            sendMessage={sendMessage}
            selectedScenario={scenarioId}
            audioRef={() => {}} 
            />
        </main>
    </div>
  );
}