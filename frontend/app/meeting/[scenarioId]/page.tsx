"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useRouter } from 'next/navigation';
import FaceTimeView from '../../../components/FaceTimeView';
import { SCENARIOS } from '../../../constants/appConstants';
import { ChatMessage } from '../../../types/chat';
import { useUserCamera } from '../../../hooks/useUserCamera';
import { useChatSession } from '../../../hooks/useChatSession';
import { useAudioRecorder } from "../../../hooks/useAudioRecorder";
import { useRealTimeConversation } from "../../../hooks/useRealTimeConversation";

export default function MeetingPage() {
  const params = useParams();
  const router = useRouter();
  const scenarioId = params.scenarioId as string;
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesRef = useRef<ChatMessage[]>([]);
  
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const [input, setInput] = useState("");
  const [status, setStatus] = useState<"idle" | "listening" | "processing" | "speaking">("idle");
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  
  // Database Session Hook
  const { startSession } = useChatSession();

  // User Camera
  const userVideoRef = useRef<HTMLVideoElement>(null);
  const localStreamRef = useRef<MediaStream | null>(null);

  // Audio Context & Queue
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueue = useRef<ArrayBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const [visemes, setVisemes] = useState<any[]>([]); 

  // --- Session Start Logic ---
  useEffect(() => {
    if (scenarioId) {
      startSession(scenarioId).then(id => {
        console.log(`Session started: ${id} for scenario: ${scenarioId}`);
      });
    }
  }, [scenarioId, startSession]);

  // --- Audio Playback Logic ---
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
      playNextChunk();
    }
  }, []);

  const handleAudioData = useCallback((data: ArrayBuffer) => {
    const bufferCopy = data.slice(0); 
    audioQueue.current.push(bufferCopy);
    
    if (!isPlayingRef.current) {
      playNextChunk();
    }
  }, [playNextChunk]);

  // --- Real-Time Conversation Hook ---
  const handleTranscript = useCallback((msg: { role: "user" | "assistant", text: string, partial?: boolean }) => {
    setMessages((prev) => {
      if (msg.partial) {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.role === "ai") { 
             return [
                ...prev.slice(0, -1),
                { ...lastMsg, content: lastMsg.content + " " + msg.text } 
             ];
        } else {
             return [...prev, { role: "ai", content: msg.text }];
        }
      } 
      const role = msg.role === "assistant" ? "ai" : "user";
      return [...prev, { role: role as "user" | "ai", content: msg.text }];
    });
  }, []);

  const handleStatusChange = useCallback((newStatus: "idle" | "listening" | "processing" | "speaking") => {
    setStatus(newStatus);
  }, []);

  const { isConnected, sendAudioChunk } = useRealTimeConversation({
    selectedScenario: scenarioId,
    onTranscript: handleTranscript,
    onAudioData: handleAudioData,
    onStatusChange: handleStatusChange
  });

  // --- Audio Recorder ---
  const { isRecording, startRecording, stopRecording } = useAudioRecorder({
    onAudioData: sendAudioChunk,
    onError: (err) => console.error("Recorder error:", err)
  });

  // --- Cleanup Audio Context ---
  useEffect(() => {
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // --- Camera Logic ---
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

    if (userVideoRef.current) {
      navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        .then(stream => {
          if (userVideoRef.current) userVideoRef.current.srcObject = stream;
          localStreamRef.current = stream;
        })
        .catch(err => console.error("Camera Error:", err));
    }
    
    return stopLocalStream;
  }, []);

  const toggleListening = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const sendMessage = (text: string) => {
      console.warn("Text sending not yet implemented in new pipeline");
  };

  const handleEndCall = () => {
    router.push('/home');
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-black font-sans">
        <main className="flex flex-col items-center w-full max-w-6xl p-4">
            <FaceTimeView
            messages={messages}
            isThinking={status === "processing"}
            audioElement={null}
            audioUrl={null}
            visemes={visemes}
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
