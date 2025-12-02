"use client";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import LivingAvatar from "./LivingAvatar";

// Augment window interface for SpeechRecognition
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

const SCENARIOS = [
  { id: "interview", label: "Job Interview", prompt: "You are a hiring manager conducting a job interview." },
  { id: "grocery", label: "Grocery Store", prompt: "You are a helpful grocery store clerk helping a customer." },
  { id: "date", label: "First Date", prompt: "You are on a first date. Be friendly and ask questions." },
  { id: "conflict", label: "Conflict Resolution", prompt: "You are an upset neighbor complaining about noise." },
];

export default function ChatInterface() {
  const [isInCall, setIsInCall] = useState(false);
  const [messages, setMessages] = useState<{ role: "user" | "ai"; content: string }[]>([]);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [language, setLanguage] = useState<"en-US" | "he-IL">("he-IL");
  const [selectedScenario, setSelectedScenario] = useState(SCENARIOS[0].id);
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  const [streamFrame, setStreamFrame] = useState<string>("");
  
  const wsRef = useRef<WebSocket | null>(null);
  const wsAvatarRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const ttsBuffer = useRef("");
  const isSpeakingRef = useRef(false);
  
  // Audio Queue System
  const audioQueue = useRef<string[]>([]);
  const isPlayingAudio = useRef(false);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);

  const speak = async (text: string) => {
    if (!text.trim()) return;

    setIsGeneratingVideo(true);
    // Select Voice based on language
    const voice = language === "he-IL" ? "he-IL-HilaNeural" : "en-US-AriaNeural";

    try {
        // Request VIDEO instead of audio
        const res = await fetch("http://localhost:5001/api/video", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, voice })
        });

        if (!res.ok) throw new Error("Video Gen Error");

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        
        setVideoUrl(url);
        setIsGeneratingVideo(false);
        setIsAiSpeaking(true);

    } catch (err) {
        console.error("Video failed:", err);
        setIsGeneratingVideo(false);
    }
  };
  
  // ... (rest of code)

  const handleTTS = (chunk: string) => {
    ttsBuffer.current += chunk;
    // Speak on sentence endings or long pauses
    if (/[.?!](\s|$)/.test(ttsBuffer.current) || ttsBuffer.current.length > 150) {
      speak(ttsBuffer.current);
      ttsBuffer.current = "";
    }
  };

  useEffect(() => {
    // Connect to WebSocket Proxy
    const ws = new WebSocket("ws://localhost:5001/api/chat");
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("Connected to Chat Server");
    };

    ws.onmessage = (event) => {
      // strict mode safety: ensure this is the active socket
      if (wsRef.current !== ws) return;

      const text = event.data;
      setIsThinking(false);
      
      // Handle TTS
      handleTTS(text);
      
      setMessages((prev) => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.role === "ai") {
          return [
            ...prev.slice(0, -1),
            { ...lastMsg, content: lastMsg.content + text },
          ];
        } else {
          return [...prev, { role: "ai", content: text }];
        }
      });
    };

    ws.onclose = () => console.log("Chat Server Disconnected");
    ws.onerror = (err) => console.error("WebSocket Error:", err);

    return () => {
      // Cleanup: prevent duplicate handling if unmount happens before close completes
      ws.onmessage = null;
      ws.onclose = null;
      ws.onerror = null;
      ws.close();
      
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      // Note: We don't cancel speech here anymore to allow finishing the sentence,
      // or we could use audioQueue.current = [] to stop immediately.
    };
  }, [language]);

  useEffect(() => {
    if (isInCall && videoRef.current) {
      navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        .then(stream => {
          if (videoRef.current) videoRef.current.srcObject = stream;
        })
        .catch(err => console.error("Camera Error:", err));
    }
  }, [isInCall]);

  const startListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Your browser does not support speech recognition. Try Chrome.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognition.lang = language;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setIsListening(true);
    
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      // Auto-send
      sendMessage(transcript); 
    };

    recognition.onerror = (event: any) => {
      console.error("Speech Recognition Error:", event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const sendMessage = (textOverride?: string) => {
    const textToSend = textOverride || input;
    if (!textToSend.trim() || !wsRef.current) return;

    // Add User Message
    setMessages((prev) => [...prev, { role: "user", content: textToSend }]);
    setIsThinking(true);

    // Send to Backend
    wsRef.current.send(textToSend);
    setInput("");
  };

  const toggleLanguage = () => {
    setLanguage((prev) => (prev === "en-US" ? "he-IL" : "en-US"));
  };

  if (!isInCall) {
    // Lobby View
    return (
      <div className="flex flex-col items-center justify-center h-[500px] w-full max-w-2xl border rounded-lg shadow-lg bg-white dark:bg-gray-900 p-8 space-y-6">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Ready to Practice?</h2>
        
        <div className="w-full max-w-md space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Choose Scenario</label>
            <select 
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              className="w-full p-2 border rounded-md dark:bg-gray-800 dark:text-white"
            >
              {SCENARIOS.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
            </select>
          </div>

          <div>
             <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Language</label>
             <button
                onClick={toggleLanguage}
                className="w-full p-2 border rounded-md bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 transition flex justify-between items-center px-4"
            >
                <span>{language === "he-IL" ? "Hebrew (עברית)" : "English (US)"}</span>
                <span>{language === "he-IL" ? "🇮🇱" : "🇺🇸"}</span>
            </button>
          </div>
        </div>

        <button
          onClick={() => setIsInCall(true)}
          className="px-8 py-3 bg-green-600 text-white text-lg font-bold rounded-full shadow-lg hover:bg-green-700 transition transform hover:scale-105"
        >
          Start Video Call 📹
        </button>
      </div>
    );
  }

  // FaceTime View
  return (
    <div className="relative h-[600px] w-full max-w-4xl border rounded-xl shadow-2xl bg-black overflow-hidden flex flex-col">
      
      {/* Main AI View */}
      <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
        {videoUrl ? (
            <video 
                src={videoUrl} 
                autoPlay 
                className="w-full h-full object-cover"
                onEnded={() => {
                    setIsAiSpeaking(false);
                    // setVideoUrl(null); // Keep last frame?
                }}
            />
        ) : (
            <div className={`flex flex-col items-center transition-transform duration-200 ${isAiSpeaking ? "scale-105" : "scale-100"}`}>
                {/* Placeholder while loading or idle */}
                <div className="relative w-80 h-80 mb-6 rounded-full overflow-hidden border-4 border-gray-700 shadow-xl">
                    <Image 
                        src="/avatar.png" 
                        alt="AI Coach" 
                        fill 
                        className="object-cover"
                    />
                </div>
                <div className="text-center z-10">
                    <div className="text-3xl font-bold text-white drop-shadow-md">AI Coach</div>
                    {isGeneratingVideo ? (
                        <div className="text-green-400 animate-pulse mt-2 font-bold">Generating Video Response...</div>
                    ) : (
                        <div className="text-lg text-gray-300 mt-2 font-medium bg-black/30 px-3 py-1 rounded-full backdrop-blur-sm">
                        {SCENARIOS.find(s => s.id === selectedScenario)?.label}
                        </div>
                    )}
                </div>
            </div>
        )}
      </div>

      {/* Chat Overlay (Captions) */}
      <div className="absolute bottom-20 left-0 right-0 px-8 flex flex-col gap-2 pointer-events-none z-50">
        {messages.slice(-2).map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] p-3 rounded-2xl backdrop-blur-md ${
                    msg.role === 'user' 
                    ? 'bg-blue-600/80 text-white' 
                    : 'bg-gray-800/80 text-white'
                } shadow-lg text-lg`} dir="auto">
                    {msg.content}
                </div>
            </div>
        ))}
        {isThinking && <div className="text-white/70 text-sm animate-pulse">Thinking...</div>}
      </div>

      {/* User PIP (Picture in Picture) */}
      <div className="absolute top-4 right-4 w-48 h-36 bg-gray-900 rounded-lg border-2 border-white/20 overflow-hidden shadow-xl">
        <video ref={videoRef} autoPlay muted playsInline className="w-full h-full object-cover transform scale-x-[-1]" />
      </div>

      {/* Controls Bar */}
      <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-black/90 to-transparent flex items-center justify-center gap-6 pb-4">
        <button
          onClick={() => setIsInCall(false)}
          className="p-4 bg-red-600 rounded-full text-white hover:bg-red-700 shadow-lg transition"
        >
          📞 End
        </button>

        <button
          onClick={startListening}
          className={`p-4 rounded-full text-white shadow-lg transition ${
            isListening ? 'bg-white text-red-600 animate-pulse ring-4 ring-red-500/50' : 'bg-gray-700 hover:bg-gray-600'
          }`}
        >
          🎤
        </button>
      </div>
    </div>
  );
}