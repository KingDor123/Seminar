import { useState, useRef, useCallback, useEffect } from 'react';

interface UseAudioRecorderProps {
  onAudioData: (data: ArrayBuffer) => void;
  onError: (error: any) => void;
  externalStream?: MediaStream | null;
}

export const useAudioRecorder = ({ onAudioData, onError, externalStream }: UseAudioRecorderProps) => {
  const [isRecording, setIsRecording] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

  const startRecording = useCallback(async () => {
    try {
      let stream = externalStream;

      if (stream && stream.getAudioTracks().length === 0) {
          console.warn("External stream has no audio tracks. Falling back to requesting microphone.");
          stream = null;
      }

      if (!stream) {
          try {
             stream = await navigator.mediaDevices.getUserMedia({ audio: true });
             streamRef.current = stream;
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

      // Load the AudioWorklet Module
      try {
        await ctx.audioWorklet.addModule('/worklets/audio-processor.js');
      } catch (err) {
        console.error("Failed to load audio worklet:", err);
        throw new Error("AudioWorklet failed to load. Ensure /worklets/audio-processor.js exists in public/.");
      }

      const source = ctx.createMediaStreamSource(stream);
      sourceRef.current = source;

      // Create the Worklet Node
      const workletNode = new AudioWorkletNode(ctx, 'pcm-processor');
      workletNodeRef.current = workletNode;

      // Handle data from the worklet
      workletNode.port.onmessage = (event) => {
        const float32Data = event.data; // This is a Float32Array
        // We pass the underlying buffer (ArrayBuffer) to the callback
        onAudioData(float32Data.buffer);
      };

      source.connect(workletNode);
      workletNode.connect(ctx.destination); // Connect to destination to keep the graph alive (often needed)

      setIsRecording(true);

    } catch (err: any) {
      console.error("Error accessing microphone:", err);
      onError(err);
    }
  }, [onAudioData, onError, externalStream]);

  const stopRecording = useCallback(() => {
    if (workletNodeRef.current) {
        workletNodeRef.current.port.onmessage = null;
        workletNodeRef.current.disconnect();
    }
    
    if (sourceRef.current) {
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

  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, [stopRecording]);

  return { isRecording, startRecording, stopRecording };
};
