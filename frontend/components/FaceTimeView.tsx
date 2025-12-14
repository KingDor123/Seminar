// frontend/components/FaceTimeView.tsx
import React, { useRef, useEffect, useState } from 'react';
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
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);

  const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);
  const [showChat, setShowChat] = useState(false);
  const [micMuted, setMicMuted] = useState(false);
  const [cameraOff, setCameraOff] = useState(false);
  
  // Derived state for subtitles
  const lastSubtitle = messages.length > 0 ? messages[messages.length - 1].content : "";
  
  // Refs for robust AudioContext management

  // Manage Audio Context
  useEffect(() => {
    if (!audioElement) return;

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

    if (!sourceRef.current && ctx && analyserRef.current) {
        try {
            const source = ctx.createMediaElementSource(audioElement);
            source.connect(analyserRef.current);
            analyserRef.current.connect(ctx.destination);
            sourceRef.current = source;
        } catch (e) {
            console.error("Error connecting MediaElementSource:", e);
        }
    }

    if (ctx && ctx.state === 'suspended') {
        ctx.resume().catch(err => console.error("Failed to resume audio context:", err));
    }
  }, [audioElement]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking, showChat]);

  // Handle local mute/camera toggle logic
  const toggleMic = () => {
    setMicMuted(!micMuted);
    // Note: Actual stream track disabling needs to happen in useUserCamera hook or here if we had access to the stream
    // For now this is visual only + functionality link
    if (isSpeechRecognitionListening && !micMuted) {
       // logic to stop listening handled by parent mostly, but we can simulate "mute"
    } else if (micMuted) {
       startListening(); // Re-enable
    }
  };

  const toggleCamera = () => {
     setCameraOff(!cameraOff);
     if (userVideoRef.current && userVideoRef.current.srcObject) {
        const stream = userVideoRef.current.srcObject as MediaStream;
        stream.getVideoTracks().forEach(track => track.enabled = cameraOff); // Toggle inverse because state is updating
     }
  };

  return (
    <div className="relative flex h-[80vh] w-full max-w-7xl bg-black rounded-3xl overflow-hidden shadow-2xl border border-gray-800">
      
      {/* --- Main Stage (AI Avatar) --- */}
      <div className={`relative transition-all duration-300 ${showChat ? 'w-2/3' : 'w-full'} h-full bg-gradient-to-b from-gray-900 to-black`}>
        
        {/* Header Overlay */}
        <div className="absolute top-0 left-0 right-0 p-6 flex justify-between items-start z-10 bg-gradient-to-b from-black/60 to-transparent">
             <div className="flex items-center gap-3">
                 <div className="bg-gray-800/80 backdrop-blur-md p-2 rounded-lg border border-gray-700">
                     <span className="text-xl">🏦</span>
                 </div>
                 <div>
                     <h2 className="text-white font-bold text-lg leading-tight">
                         {SCENARIOS.find(s => s.id === selectedScenario)?.label || "Meeting"}
                     </h2>
                     <div className="flex items-center gap-2">
                         <span className={`w-2 h-2 rounded-full ${isGeneratingAudio || isAiSpeaking ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`}></span>
                         <span className="text-gray-400 text-xs uppercase tracking-wider font-medium">
                             {isGeneratingAudio ? "Generating..." : isAiSpeaking ? "Speaking" : "Connected"}
                         </span>
                     </div>
                 </div>
             </div>
             
             <div className="bg-red-500/10 text-red-400 px-3 py-1 rounded-full text-xs font-mono border border-red-500/20 flex items-center gap-2">
                 <span>REC</span>
                 <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
             </div>
        </div>

        {/* 3D Scene */}
        <div className="w-full h-full">
            <Avatar3D audioElement={audioElement} visemes={visemes} audioAnalyser={analyser} />
        </div>

        {/* Dynamic Subtitles Overlay */}
        <div className="absolute bottom-24 left-0 right-0 px-12 text-center pointer-events-none">
            {lastSubtitle && (
                 <div className="inline-block bg-black/60 backdrop-blur-md text-white text-lg px-6 py-3 rounded-2xl shadow-lg border border-white/5 transition-all duration-500">
                     {lastSubtitle}
                 </div>
            )}
        </div>

        {/* Audio Element (Hidden) */}
        {audioUrl && (
             <div className="absolute opacity-0 pointer-events-none w-1 h-1">
                 <audio ref={audioRef} src={audioUrl} autoPlay />
             </div>
        )}
      </div>


      {/* --- Chat Sidebar (Collapsible) --- */}
      <div className={`absolute right-0 top-0 bottom-0 bg-gray-900/95 backdrop-blur-xl border-l border-gray-700 transition-all duration-300 transform ${showChat ? 'translate-x-0 w-1/3' : 'translate-x-full w-0'} z-20 flex flex-col`}>
          <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-gray-900">
              <h3 className="text-white font-bold">Meeting Chat</h3>
              <button onClick={() => setShowChat(false)} className="text-gray-400 hover:text-white">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
              </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[85%] p-3 rounded-2xl text-sm ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-200'}`}>
                          {msg.content}
                      </div>
                  </div>
              ))}
              <div ref={messagesEndRef} />
          </div>

          <div className="p-4 border-t border-gray-700 bg-gray-900">
              <div className="relative">
                  <input 
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                      placeholder="Type a message..."
                      className="w-full bg-gray-800 text-white rounded-full pl-4 pr-10 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-700"
                  />
                  <button onClick={() => sendMessage()} className="absolute right-2 top-1.5 text-blue-400 hover:text-blue-300">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                          <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                      </svg>
                  </button>
              </div>
          </div>
      </div>


      {/* --- User PIP (Floating) --- */}
      <div className={`absolute top-24 right-6 w-48 h-36 bg-gray-800 rounded-xl overflow-hidden shadow-2xl border-2 border-gray-700 z-10 transition-all duration-300 ${showChat ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
           {cameraOff ? (
               <div className="w-full h-full flex items-center justify-center bg-gray-800 text-gray-500">
                   <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                       <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                   </svg>
               </div>
           ) : (
               <video ref={userVideoRef} autoPlay muted playsInline className="w-full h-full object-cover transform scale-x-[-1]" />
           )}
           <div className="absolute bottom-2 left-2 bg-black/60 px-2 py-0.5 rounded text-[10px] text-white font-medium backdrop-blur-sm">
               You
           </div>
      </div>


      {/* --- Bottom Controls Bar --- */}
      <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 flex items-center gap-4 bg-gray-900/90 backdrop-blur-xl border border-gray-700 px-6 py-3 rounded-full shadow-2xl z-30">
          
          {/* Mute Button */}
          <button 
             onClick={toggleMic}
             className={`p-3 rounded-full transition-all ${micMuted ? 'bg-red-500 text-white hover:bg-red-600' : 'bg-gray-700 text-white hover:bg-gray-600'}`}
             title={micMuted ? "Unmute" : "Mute"}
          >
              {micMuted ? (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3l18 18" />
                  </svg>
              ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
              )}
          </button>

          {/* Camera Button */}
          <button 
             onClick={toggleCamera}
             className={`p-3 rounded-full transition-all ${cameraOff ? 'bg-red-500 text-white hover:bg-red-600' : 'bg-gray-700 text-white hover:bg-gray-600'}`}
             title={cameraOff ? "Turn Video On" : "Turn Video Off"}
          >
              {cameraOff ? (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3l18 18" />
                  </svg>
              ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
              )}
          </button>

          {/* Chat Toggle */}
          <button 
             onClick={() => setShowChat(!showChat)}
             className={`p-3 rounded-full transition-all ${showChat ? 'bg-blue-600 text-white' : 'bg-gray-700 text-white hover:bg-gray-600'}`}
             title="Toggle Chat"
          >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
          </button>

          {/* End Call */}
          <button 
             onClick={onEndCall}
             className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-full font-bold flex items-center gap-2 shadow-lg transition-transform hover:scale-105"
             title="End Meeting"
          >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h6.666M19.333 12.889A2.25 2.25 0 0121.583 15v3.667a2.25 2.25 0 01-2.25 2.25H2.417A2.25 2.25 0 01.167 18.667V15a2.25 2.25 0 012.25-2.111" />
              </svg>
              <span className="text-sm">Leave</span>
          </button>
      </div>

    </div>
  );
};

export default FaceTimeView;
