// frontend/hooks/useUserCamera.ts
import { useState, useEffect, useRef } from 'react';

export const useUserCamera = (isInCall: boolean) => {
  const userVideoRef = useRef<HTMLVideoElement>(null);
  const localStreamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    const stopLocalStream = () => {
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => track.stop());
        localStreamRef.current = null;
      }

      if (userVideoRef.current) {
        userVideoRef.current.srcObject = null;
      }
    };

    if (isInCall) {
      if (userVideoRef.current) { // Ensure video ref is available before attempting to get media
        navigator.mediaDevices.getUserMedia({ video: true, audio: false })
          .then(stream => {
            if (userVideoRef.current) {
              userVideoRef.current.srcObject = stream;
            }
            localStreamRef.current = stream;
          })
          .catch(err => console.error("Camera Error:", err));
      } else {
        console.warn("User video ref not available for camera access.");
      }
    } else {
      stopLocalStream();
    }

    return stopLocalStream; // Cleanup function
  }, [isInCall]);

  return { userVideoRef };
};
