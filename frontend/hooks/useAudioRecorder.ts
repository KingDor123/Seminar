import { useState, useRef, useCallback, useEffect } from 'react';

interface UseAudioRecorderProps {
  onAudioData: (data: ArrayBuffer) => void;
  onError: (error: unknown) => void;
  externalStream?: MediaStream | null;
}

export const useAudioRecorder = ({ onAudioData, onError, externalStream }: UseAudioRecorderProps) => {
  const [isRecording, setIsRecording] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

  const cleanup = useCallback(() => {
    // 1. Disconnect and clean up Worklet
    if (workletNodeRef.current) {
        workletNodeRef.current.port.onmessage = null;
        workletNodeRef.current.disconnect();
        workletNodeRef.current = null;
    }
    
    // 2. Disconnect Source
    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }

    // 3. Close AudioContext
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(console.error);
      audioContextRef.current = null;
    }
    
    // 4. Stop Stream Tracks (only if we created them)
    if (streamRef.current && !externalStream) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    streamRef.current = null;

    setIsRecording(false);
  }, [externalStream]);

  const startRecording = useCallback(async () => {
    try {
      // Ensure clean state before starting
      cleanup();

      let stream = externalStream;

      if (stream && stream.getAudioTracks().length === 0) {
          console.warn("External stream has no audio tracks. Falling back to requesting microphone.");
          stream = null;
      }

      if (!stream) {
          try {
             stream = await navigator.mediaDevices.getUserMedia({ audio: {
                 echoCancellation: true,
                 noiseSuppression: true,
                 autoGainControl: true
             } });
          } catch (e: unknown) {
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              if ((e as any).name === 'NotFoundError' || (e as any).name === 'DevicesNotFoundError') {
                  console.error("No microphone found.");
              }
              throw e;
          }
      }

      if (!stream) {
          throw new Error("No media stream available for recording.");
      }

      streamRef.current = stream;

      // Handle stream inactivity (e.g. user revoked permission or unplugged mic)
      stream.getAudioTracks()[0].onended = () => {
          console.log("Microphone track ended externally.");
          cleanup();
      };

      // Create AudioContext
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const ctx = new AudioContextClass({ sampleRate: 16000 });
      audioContextRef.current = ctx;

      // CRITICAL: Ensure context is running (fixes browser autoplay policy issues)
      if (ctx.state === 'suspended') {
          await ctx.resume();
      }

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
        onAudioData(float32Data.buffer);
      };

      source.connect(workletNode);
      workletNode.connect(ctx.destination); // Connect to destination to keep the graph alive

      setIsRecording(true);

    } catch (err: unknown) {
      console.error("Error accessing microphone:", err);
      onError(err);
      cleanup();
    }
  }, [onAudioData, onError, externalStream, cleanup]);

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return { isRecording, startRecording, stopRecording: cleanup };
};
