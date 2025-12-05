import { useState, useRef, useCallback, useEffect } from 'react';

interface UseAudioRecorderProps {
  onAudioData: (data: ArrayBuffer) => void;
  onError: (error: any) => void;
}

export const useAudioRecorder = ({ onAudioData, onError }: UseAudioRecorderProps) => {
  const [isRecording, setIsRecording] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Create AudioContext with desired sample rate for Whisper (16kHz is ideal, but browser might enforce native)
      // We will try to request 16kHz, but fallback to native and resample if needed?
      // For simplicity, let's try asking for 16kHz.
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const ctx = new AudioContextClass({ sampleRate: 16000 });
      audioContextRef.current = ctx;

      const source = ctx.createMediaStreamSource(stream);
      sourceRef.current = source;

      // Buffer size 4096 is ~250ms at 16kHz
      const processor = ctx.createScriptProcessor(4096, 1, 1); 
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        // Clone data to send
        const buffer = new Float32Array(inputData);
        onAudioData(buffer.buffer);
      };

      source.connect(processor);
      processor.connect(ctx.destination); // Essential for Chrome to fire events

      setIsRecording(true);

    } catch (err) {
      console.error("Error accessing microphone:", err);
      onError(err);
    }
  }, [onAudioData, onError]);

  const stopRecording = useCallback(() => {
    if (processorRef.current && sourceRef.current) {
      processorRef.current.disconnect();
      sourceRef.current.disconnect();
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    setIsRecording(false);
  }, []);

  // Cleanup
  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, [stopRecording]);

  return { isRecording, startRecording, stopRecording };
};
