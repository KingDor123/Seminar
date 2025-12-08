// frontend/hooks/useUserCamera.ts
import { useState, useEffect, useRef } from 'react';

export const useUserCamera = (isInCall: boolean) => {
  const userVideoRef = useRef<HTMLVideoElement>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const [mediaStream, setMediaStream] = useState<MediaStream | null>(null);

  useEffect(() => {
    const stopLocalStream = () => {
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => track.stop());
        localStreamRef.current = null;
        setMediaStream(null);
      }

      if (userVideoRef.current) {
        userVideoRef.current.srcObject = null;
      }
    };

    if (isInCall) {
      // Request BOTH video and audio to avoid race conditions
      navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        .then(stream => {
          if (userVideoRef.current) {
            userVideoRef.current.srcObject = stream;
          }
          localStreamRef.current = stream;
          setMediaStream(stream);
        })
        .catch(err => {
            if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
              console.warn("No camera/microphone device found.");
            } else {
              console.error("Camera/Mic Access Error:", err);
            }
            
            // Fallback: Try Video Only if Audio failed (or vice versa, but mostly we want video)
            // This handles cases where user has Cam but no Mic
            navigator.mediaDevices.getUserMedia({ video: true, audio: false })
                .then(stream => {
                    if (userVideoRef.current) userVideoRef.current.srcObject = stream;
                    localStreamRef.current = stream;
                    setMediaStream(stream);
                })
                .catch(() => {}); // Ignore double failure
        });
    } else {
      stopLocalStream();
    }

    return stopLocalStream; // Cleanup function
  }, [isInCall]);

  return { userVideoRef, mediaStream };
};
