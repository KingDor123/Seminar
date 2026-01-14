// frontend/hooks/useUserCamera.ts
import { useState, useEffect, useRef } from 'react';
import { he } from '../constants/he';

export const useUserCamera = (isInCall: boolean) => {
  const userVideoRef = useRef<HTMLVideoElement>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const [mediaStream, setMediaStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    const stopStream = (stream: MediaStream | null) => {
      stream?.getTracks().forEach(t => t.stop());
    };

    const stopLocalStream = () => {
      stopStream(localStreamRef.current);
      localStreamRef.current = null;

      if (userVideoRef.current) {
        userVideoRef.current.srcObject = null;
      }
      if (isActive) {
        setMediaStream(null);
      }
    };

    const acceptStream = (stream: MediaStream, attachVideo: boolean) => {
      if (!isActive) {
        stopStream(stream);
        return;
      }
      if (attachVideo && userVideoRef.current) {
        userVideoRef.current.srcObject = stream;
      } else if (userVideoRef.current) {
        userVideoRef.current.srcObject = null;
      }
      localStreamRef.current = stream;
      setMediaStream(stream);
      setError(null);
    };

    const request = async () => {
      if (!navigator.mediaDevices?.getUserMedia) {
        if (isActive) setError(he.errors.mediaDevicesUnsupported);
        return;
      }

      if (isActive) setError(null);

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        acceptStream(stream, true);
        return;
      } catch (err: any) {
        if (!isActive) return;

        let errorMsg = he.errors.cameraMicFailed;
        if (err?.name === 'NotFoundError' || err?.name === 'DevicesNotFoundError') {
          errorMsg = he.errors.cameraMicFailed;
        } else if (err?.name === 'NotAllowedError' || err?.name === 'PermissionDeniedError') {
          errorMsg = he.errors.mediaDevicesUnsupported;
        }

        // Fallback 1: audio-only
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ video: false, audio: true });
          acceptStream(stream, false);
          return;
        } catch {
          // Fallback 2: video-only
          try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            acceptStream(stream, true);
            return;
          } catch {
            if (isActive) setError(errorMsg);
          }
        }
      }
    };

    if (isInCall) request();
    else stopLocalStream();

    return () => {
      isActive = false;
      stopLocalStream();
    };
  }, [isInCall]);

  return { userVideoRef, mediaStream, error };
};
