// frontend/components/FaceTimeView.tsx
import React, { useRef, useEffect } from 'react';
import Avatar3D from './Avatar3D';
import { SCENARIOS } from '../constants/appConstants';
import { ChatMessage } from '../types/chat';

interface FaceTimeViewProps {
  messages: ChatMessage[];
  isThinking: boolean;
  audioElement: HTMLAudioElement | null;
  audioUrl: string | null;
  visemes?: any[];
  isGeneratingAudio: boolean;
  isAiSpeaking: boolean;
  userVideoRef: React.RefObject<HTMLVideoElement | null>;
  isSpeechRecognitionListening: boolean;
  startListening: () => void;
  onEndCall: () => void;
  input: string;
  setInput: (input: string) => void;
  sendMessage: (textOverride?: string) => void;
  selectedScenario: string;
  audioRef: React.Ref<HTMLAudioElement>;
}

const FaceTimeView: React.FC<FaceTimeViewProps> = ({
  messages,
  isThinking,
  audioElement,
  audioUrl,
  visemes,
  isGeneratingAudio,
  isAiSpeaking,
  userVideoRef,
  isSpeechRecognitionListening,
  startListening,
  onEndCall,
  input,
  setInput,
  sendMessage,
  selectedScenario,
  audioRef,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [analyser, setAnalyser] = React.useState<AnalyserNode | null>(null);
  
  // Refs for robust AudioContext management
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);

  // Manage Audio Context
  useEffect(() => {
    if (!audioElement) return;

    // Initialize AudioContext if not already done
    if (!audioContextRef.current) {
      try {
          const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
          audioContextRef.current = new AudioContext();
          analyserRef.current = audioContextRef.current.createAnalyser();
          analyserRef.current.fftSize = 256;
          setAnalyser(analyserRef.current);
      } catch (e) {
          console.error("Failed to create AudioContext:", e);
          return;
      }
    }

    const ctx = audioContextRef.current;

    // Connect source to element if not already connected
    // We use a try-catch because checking if it's connected is hard
    if (!sourceRef.current && ctx && analyserRef.current) {
        try {
            const source = ctx.createMediaElementSource(audioElement);
            source.connect(analyserRef.current);
            analyserRef.current.connect(ctx.destination);
            sourceRef.current = source;
            console.log("Audio Context & Source initialized successfully.");
        } catch (e) {
            console.error("Error connecting MediaElementSource (likely already connected):", e);
        }
    }

    // Resume context if suspended
    if (ctx && ctx.state === 'suspended') {
        ctx.resume().catch(err => console.error("Failed to resume audio context:", err));
    }

    // Cleanup logic:
    // We intentionally DO NOT close the context or disconnect on unmount/re-mount 
    // of this effect if the audioElement persists, because we can't reconnect easily.
    // We relies on the browser/GC to clean up if the actual DOM element is destroyed.
    
    return () => {
       // If we really wanted to be clean, we'd close the context ONLY if the component is truly unmounting
       // but we can't know that for sure in Strict Mode's double-invocation.
    };
  }, [audioElement]);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  return (
    <div className="flex flex-col h-[650px] w-full max-w-6xl border border-gray-800 rounded-xl shadow-2xl bg-black overflow-hidden">
      {/* TOP HEADER: Scenario Title */}
      <div className="h-12 bg-gray-900/80 backdrop-blur border-b border-gray-800 flex items-center justify-center">
          <h2 className="text-gray-100 font-bold text-lg tracking-wide flex items-center gap-2">
             <span className="text-blue-500">●</span> 
             {SCENARIOS.find(s => s.id === selectedScenario)?.label || "Unknown Scenario"}
          </h2>
      </div>

      <div className="flex flex-1 overflow-hidden">
      
      {/* LEFT PANEL: Main AI View & Controls */}
      <div className="relative flex-1 bg-gray-900 flex flex-col">
        
        {/* 3D Scene Container */}
        <div className="flex-1 relative overflow-hidden">
           <Avatar3D audioElement={audioElement} visemes={visemes} audioAnalyser={analyser} />
           
           {/* Audio Player - technically visible but hidden from view to prevent browser 'display:none' optimizations */ }
           {audioUrl && (
             <div className="absolute opacity-0 pointer-events-none w-1 h-1 overflow-hidden">
                 <audio 
                   ref={audioRef} 
                   src={audioUrl}
                   onPlay={() => console.log("Audio started playing")}
                   onEnded={() => console.log("Audio finished playing")}
                   onError={(e) => console.error("Audio playback error:", e.currentTarget.error)}
                   onLoadedData={(e) => {
                      console.log("Audio loaded, attempting to play...");
                      const audio = e.currentTarget;
                      // Resume context if needed, then play
                      if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
                          audioContextRef.current.resume().then(() => {
                              console.log("Resumed AudioContext from suspended state");
                          }).catch(err => console.error("Failed to resume context:", err));
                      }
                      
                      audio.play()
                        .catch(err => {
                            console.error("Autoplay failed:", err);
                        });
                   }}
                 />
             </div>
           )}

           {/* Overlay Info (Scenario Label & Status) */}
           <div className="absolute top-4 left-4 z-10">
               {isGeneratingAudio ? (
                   <div className="text-green-400 animate-pulse font-bold bg-black/50 px-3 py-1 rounded-full backdrop-blur-md border border-green-500/30">
                     Generating Speech...
                   </div>
               ) : (
                   <div className="text-lg text-gray-200 font-medium bg-black/40 px-4 py-1 rounded-full backdrop-blur-md border border-white/10">
                     {SCENARIOS.find(s => s.id === selectedScenario)?.label}
                   </div>
               )}
           </div>

           {/* User PIP (Picture in Picture) - Top Right */}
           <div className="absolute top-4 right-4 w-48 h-36 bg-gray-900 rounded-lg border-2 border-white/20 overflow-hidden shadow-xl z-20">
             <video ref={userVideoRef} autoPlay muted playsInline className="w-full h-full object-cover transform scale-x-[-1]" />
           </div>
        </div>

        {/* Controls Bar (Bottom of Left Panel) */}
        <div className="h-20 bg-gray-900 border-t border-gray-800 flex items-center justify-center gap-8 z-20">
          <button
            onClick={onEndCall}
            className="flex items-center gap-2 px-6 py-3 bg-red-600 rounded-full text-white font-semibold hover:bg-red-700 shadow-lg transition-all hover:scale-105"
          >
            <span>📞</span> End Call
          </button>

          <button
            onClick={startListening}
            className={`p-4 rounded-full text-white shadow-lg transition-all hover:scale-110 ${
              isSpeechRecognitionListening 
                ? 'bg-white text-red-600 animate-pulse ring-4 ring-red-500/50 shadow-red-500/50' 
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            <span className="text-2xl">🎤</span>
          </button>
        </div>
      </div>

      {/* RIGHT PANEL: Chat Sidebar */}
      <div className="w-96 bg-gray-900 border-l border-gray-800 flex flex-col">
        
        {/* Header */}
        <div className="p-4 border-b border-gray-800 bg-gray-900/50 backdrop-blur text-gray-100 font-bold tracking-wide shadow-sm">
          Chat History
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-900/95 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
           {messages.length === 0 && (
             <div className="text-gray-500 text-center mt-10 italic text-sm">
               Start the conversation...
             </div>
           )}
           
           {messages.map((msg, idx) => (
             <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-3 rounded-2xl text-sm leading-relaxed shadow-md ${
                    msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-gray-800 text-gray-100 border border-gray-700 rounded-bl-none'
                }`}>
                    {msg.content}
                </div>
             </div>
           ))}
           
           {isThinking && (
             <div className="flex justify-start">
               <div className="bg-gray-800 border border-gray-700 p-3 rounded-2xl rounded-bl-none text-gray-400 text-xs italic animate-pulse">
                 AI is thinking...
               </div>
             </div>
           )}
           <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-800 bg-gray-900">
           <div className="flex gap-2 items-center bg-gray-800 rounded-full px-4 py-2 border border-gray-700 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition-all">
             <input 
               value={input}
               onChange={(e) => setInput(e.target.value)}
               onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
               placeholder="Type a message..."
               className="flex-1 bg-transparent text-white placeholder-gray-500 focus:outline-none text-sm"
             />
             <button 
               onClick={() => sendMessage()} 
               className="text-blue-500 hover:text-blue-400 transition p-1 disabled:opacity-50 disabled:cursor-not-allowed"
               disabled={!input.trim()}
             >
               <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
                 <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
               </svg>
             </button>
           </div>
        </div>
      </div>

      </div>
    </div>
  );
};

export default FaceTimeView;