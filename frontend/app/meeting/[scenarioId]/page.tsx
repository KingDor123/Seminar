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

  // User Camera (now handles both Video & Audio request to avoid race conditions)
  const { userVideoRef, mediaStream } = useUserCamera(true);

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
  const processQueueRef = useRef<() => Promise<void>>(null);

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

    // Ensure context is running (Fix for Autoplay Policy)
    if (ctx.state === 'suspended') {
      try {
        await ctx.resume();
        console.log("Resumed AudioContext for playback");
      } catch (e) {
        console.error("Failed to resume AudioContext during playback:", e);
      }
    }

    const chunk = audioQueue.current.shift();
    
    if (!chunk) return;

    try {
      const audioBuffer = await ctx.decodeAudioData(chunk);
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);
      
      source.onended = () => {
        if (processQueueRef.current) processQueueRef.current();
      };
      
      source.start(0);
    } catch (err) {
      console.error("Error decoding audio chunk:", err);
      if (processQueueRef.current) processQueueRef.current();
    }
  }, []);

  useEffect(() => {
      // @ts-ignore
      processQueueRef.current = playNextChunk;
  }, [playNextChunk]);

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

  // --- Sound Effects ---
  const playListeningCue = useCallback(() => {
     if (!audioContextRef.current) {
         audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
     }
     const ctx = audioContextRef.current;
     if (ctx.state === 'suspended') ctx.resume();

     const oscillator = ctx.createOscillator();
     const gainNode = ctx.createGain();

     oscillator.connect(gainNode);
     gainNode.connect(ctx.destination);

     // Gentle "ping" sound (Sine wave, high pitch, quick decay)
     oscillator.type = "sine";
     oscillator.frequency.setValueAtTime(880, ctx.currentTime); // A5
     gainNode.gain.setValueAtTime(0.05, ctx.currentTime); // Low volume
     gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);

     oscillator.start();
     oscillator.stop(ctx.currentTime + 0.3);
  }, []);

  useEffect(() => {
      if (status === "listening") {
          playListeningCue();
      }
  }, [status, playListeningCue]);

  const { isConnected, sendAudioChunk } = useRealTimeConversation({
    selectedScenario: scenarioId,
    onTranscript: handleTranscript,
    onAudioData: handleAudioData,
    onStatusChange: handleStatusChange
  });

  // --- Audio Recorder ---
  // Now uses the shared mediaStream from useUserCamera to avoid race conditions
  const { isRecording, startRecording, stopRecording } = useAudioRecorder({
    onAudioData: sendAudioChunk,
    onError: (err) => console.error("Recorder error:", err),
    externalStream: mediaStream
  });

  // --- Cleanup Audio Context ---
  useEffect(() => {
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  const toggleListening = async () => {
    // Resume AudioContext on user interaction to fix "no sound" issue
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    if (audioContextRef.current.state === 'suspended') {
      try {
        await audioContextRef.current.resume();
      } catch (err) {
        console.error("Failed to resume AudioContext:", err);
      }
    }

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
