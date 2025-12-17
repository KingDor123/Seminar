// frontend/hooks/useApi.ts
import { useState, useCallback, useRef, useEffect } from 'react';

// Centralize API base URL resolution
const useApiBase = () => {
  const resolveApiBase = useCallback(() => {
    let apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5001";
    apiBase = apiBase.replace(/\/$/, "");

    if (/^\d+$/.test(apiBase)) {
      apiBase = `http://localhost:${apiBase}`;
    } else if (!apiBase.startsWith("http")) {
      apiBase = `http://${apiBase}`;
    }
    return apiBase;
  }, []);

  return resolveApiBase;
};

// Hook for TTS functionality
export const useTTS = () => {
  const resolveApiBase = useApiBase();
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [visemes, setVisemes] = useState<unknown[]>([]); // Store visemes
  
  // Ref to track the current URL for cleanup
  const audioUrlRef = useRef<string | null>(null);

  // Cleanup effect: runs when audioUrl changes or component unmounts
  useEffect(() => {
    // If there was a previous URL and it's different from the new one, revoke it
    if (audioUrlRef.current && audioUrlRef.current !== audioUrl) {
      console.log("Revoking old TTS URL:", audioUrlRef.current);
      URL.revokeObjectURL(audioUrlRef.current);
    }
    // Update ref to current
    audioUrlRef.current = audioUrl;
  }, [audioUrl]);

  // Cleanup strictly on unmount
  useEffect(() => {
      return () => {
          if (audioUrlRef.current) {
               console.log("Component unmounting, revoking URL:", audioUrlRef.current);
               URL.revokeObjectURL(audioUrlRef.current);
          }
      };
  }, []);

  const updateAudioUrl = useCallback((url: string | null) => {
    setAudioUrl(url);
  }, []);

  const speak = useCallback(async (text: string, language: "en-US" | "he-IL") => {
    if (!text.trim()) return;

    setIsGeneratingAudio(true);
    const voice = language === "he-IL" ? "he-IL-HilaNeural" : "en-US-AriaNeural";

    try {
      const base = resolveApiBase();
      const res = await fetch(`${base}/api/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        console.error("TTS Error Details:", errData);
        throw new Error("TTS Gen Error");
      }

      const data = await res.json();
      
      // Decode base64 audio
      const binaryString = window.atob(data.audio);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: 'audio/mpeg' });
      console.log(`TTS Audio Blob created, size: ${blob.size} bytes`);
      const url = URL.createObjectURL(blob);

      setVisemes(data.visemes || []);
      // Directly set the new URL. The effect will handle cleanup of the old one.
      setAudioUrl(url);
      
      setIsGeneratingAudio(false);
      return true; // Indicate success
    } catch (err) {
      console.error("TTS failed:", err);
      setIsGeneratingAudio(false);
      return false; // Indicate failure
    }
  }, [resolveApiBase]);

  return { speak, isGeneratingAudio, audioUrl, updateAudioUrl, visemes };
};

// Hook for WebSocket base URL
export const useWebSocketUrl = () => {
  const resolveApiBase = useApiBase();

  const getWsUrl = useCallback((path: string) => {
    const base = resolveApiBase();
    return `${base.replace(/^http/, "ws")}${path}`;
  }, [resolveApiBase]);

  return getWsUrl;
};

// Generic API Hook
export const useApi = () => {
  const resolveApiBase = useApiBase();
  return { getApiUrl: resolveApiBase };
};
