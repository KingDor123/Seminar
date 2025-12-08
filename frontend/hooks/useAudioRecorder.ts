import { useState, useRef, useCallback, useEffect } from 'react';

interface UseAudioRecorderProps {
  onAudioData: (data: ArrayBuffer) => void;
  onError: (error: any) => void;
  externalStream?: MediaStream | null;
}

export const useAudioRecorder = ({ onAudioData, onError, externalStream }: UseAudioRecorderProps) => {
  const [isRecording, setIsRecording] = useState(false);
  const streamRef = useRef<MediaStream | null>(null); // Only used if we created the stream ourselves
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

  const startRecording = useCallback(async () => {
    try {
      let stream = externalStream;

      // Validate external stream has audio
      if (stream && stream.getAudioTracks().length === 0) {
          console.warn("External stream has no audio tracks. Falling back to requesting microphone.");
          stream = null;
      }

      // Fallback: If no valid external stream, try to get one
      if (!stream) {
          try {
             stream = await navigator.mediaDevices.getUserMedia({ audio: true });
             streamRef.current = stream; // Track it so we can stop it later
          } catch (e: any) {
              if (e.name === 'NotFoundError' || e.name === 'DevicesNotFoundError') {
                  console.warn("No microphone found.");
              }
              throw e;
          }
      }

      if (!stream) {
          throw new Error("No media stream available for recording.");
      }

      // Create AudioContext
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
        const buffer = new Float32Array(inputData);
        onAudioData(buffer.buffer);
      };

      source.connect(processor);
      processor.connect(ctx.destination);

      setIsRecording(true);

    } catch (err: any) {
      if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
         // handled above or passed through
      } else {
         console.error("Error accessing microphone:", err);
      }
      onError(err);
    }
  }, [onAudioData, onError, externalStream]);

  const stopRecording = useCallback(() => {
    if (processorRef.current && sourceRef.current) {
      processorRef.current.disconnect();
      sourceRef.current.disconnect();
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    // Only stop tracks if WE created the stream (fallback mode)
    // If it was external, the parent manages it.
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
