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
            
            // Fallback 1: Try Audio Only (User might have no camera)
            navigator.mediaDevices.getUserMedia({ video: false, audio: true })
                .then(stream => {
                    console.log("Fallback to Audio-only stream");
                    localStreamRef.current = stream;
                    setMediaStream(stream);
                })
                .catch(() => {
                     // Fallback 2: Try Video Only (User might have no mic)
                     navigator.mediaDevices.getUserMedia({ video: true, audio: false })
                        .then(stream => {
                            if (userVideoRef.current) userVideoRef.current.srcObject = stream;
                            localStreamRef.current = stream;
                            setMediaStream(stream);
                        })
                        .catch(() => {
                            console.warn("No media devices available.");
                        });
                });
        });
    } else {
      stopLocalStream();
    }

    return stopLocalStream; // Cleanup function
  }, [isInCall]);

  return { userVideoRef, mediaStream };
};
