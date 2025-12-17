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
        if (id) {
            loadMessages(id).then(msgs => {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const formattedMsgs = msgs.map((m: any) => ({
                    role: m.role === 'ai' ? 'ai' : 'user',
                    content: m.content
                }));
                setMessages(formattedMsgs);
            });
            audioQueueRef.current?.resume();
        }
      });
    }
  }, [scenarioId, startSession, loadMessages, user]);


  // --- Streaming Conversation Hook ---
  const handleNewMessage = useCallback((msg: ChatMessage) => {
    setMessages((prev) => {
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


  // --- Recording & VAD State ---
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  
  // VAD Refs to avoid re-renders
  const vadContextRef = useRef<{
      audioCtx: AudioContext | null;
      source: MediaStreamAudioSourceNode | null;
      analyser: AnalyserNode | null;
      animationFrameId: number | null;
      silenceStart: number | null;
      hasSpoken: boolean;
  }>({
      audioCtx: null,
      source: null,
      analyser: null,
      animationFrameId: null,
      silenceStart: null,
      hasSpoken: false
  });

  const stopVAD = useCallback(() => {
      const vad = vadContextRef.current;
      if (vad.animationFrameId) cancelAnimationFrame(vad.animationFrameId);
      if (vad.source) {
          vad.source.disconnect();
          vad.source = null;
      }
      if (vad.analyser) {
          vad.analyser.disconnect();
          vad.analyser = null;
      }
      if (vad.audioCtx && vad.audioCtx.state !== 'closed') {
          vad.audioCtx.close().catch(e => console.error("VAD Close error:", e));
          vad.audioCtx = null;
      }
      vad.animationFrameId = null;
      vad.hasSpoken = false;
      vad.silenceStart = null;
  }, []);

  const stopRecording = useCallback(() => {
    // Stop VAD first
    stopVAD();

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, [stopVAD]);

  const startVAD = useCallback((stream: MediaStream) => {
      try {
          const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
          const source = audioCtx.createMediaStreamSource(stream);
          const analyser = audioCtx.createAnalyser();
          analyser.fftSize = 512;
          analyser.smoothingTimeConstant = 0.1; // Respond quickly
          source.connect(analyser);

          const bufferLength = analyser.frequencyBinCount;
          const dataArray = new Uint8Array(bufferLength);

          // Update Ref
          vadContextRef.current = {
              audioCtx,
              source,
              analyser,
              animationFrameId: null,
              silenceStart: null,
              hasSpoken: false
          };

          const checkVolume = () => {
              if (!vadContextRef.current.analyser) return;

              vadContextRef.current.analyser.getByteFrequencyData(dataArray);
              let sum = 0;
              for(let i = 0; i < bufferLength; i++) sum += dataArray[i];
              const average = sum / bufferLength;

              // Thresholds
              const SPEECH_THRESHOLD = 15; // Volume threshold (0-255)
              const SILENCE_DURATION = 1500; // ms

              if (average > SPEECH_THRESHOLD) {
                  vadContextRef.current.hasSpoken = true;
                  vadContextRef.current.silenceStart = null; // Reset silence
              } else {
                  // Silence detected
                  if (vadContextRef.current.hasSpoken) {
                      if (!vadContextRef.current.silenceStart) {
                          vadContextRef.current.silenceStart = Date.now();
                      } else {
                          const silenceTime = Date.now() - vadContextRef.current.silenceStart;
                          if (silenceTime > SILENCE_DURATION) {
                              console.log("VAD: Auto-Stop Triggered (Silence > 1.5s)");
                              stopRecording();
                              return; // Stop loop
                          }
                      }
                  }
              }

              vadContextRef.current.animationFrameId = requestAnimationFrame(checkVolume);
          };

          checkVolume();

      } catch (e) {
          console.error("VAD Init Error:", e);
      }
  }, [stopRecording]);

  const startRecording = useCallback(async () => {
    try {
        let stream = mediaStream;
        if (!stream) {
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        }
        if (stream.getAudioTracks().length === 0) {
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
            if (audioBlob.size > 0) {
                 sendStreamMessage(null, audioBlob);
            }
            audioChunksRef.current = [];
        };

        audioChunksRef.current = [];
        recorder.start();
        mediaRecorderRef.current = recorder;
        setIsRecording(true);
        setStatus("listening");
        
        // Start VAD monitoring on the same stream
        startVAD(stream);

    } catch (e) {
      console.error("Failed to start recording:", e);
    }
  }, [mediaStream, sendStreamMessage, startVAD]);

  const toggleListening = async () => {
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
      setInput("");
      sendStreamMessage(textToSend, null);
  };

  const handleEndCall = () => {
    router.push('/home');
  };

  if (isLoading) return <div className="flex h-screen items-center justify-center bg-black text-white">Initializing Meeting...</div>;
  if (!user) return null;

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
