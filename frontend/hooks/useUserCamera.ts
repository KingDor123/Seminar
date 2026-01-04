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

    const stopLocalStream = () => {
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => track.stop());
        localStreamRef.current = null;
      }
      if (isActive) {
          setMediaStream(null);
      }
      if (userVideoRef.current) {
        userVideoRef.current.srcObject = null;
      }
    };

    if (isInCall) {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          console.warn("Media devices not supported in this browser.");
          setTimeout(() => { if (isActive) setError(he.errors.mediaDevicesUnsupported); }, 0);
          return;
      }

      setTimeout(() => { if (isActive) setError(null); }, 0); // Reset error

      // Request BOTH video and audio
      navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        .then(stream => {
          if (!isActive) {
              // Component unmounted or effect re-ran before this resolved.
              // Stop this stream immediately to prevent "zombie" tracks.
              stream.getTracks().forEach(track => track.stop());
              return;
          }
          
          if (userVideoRef.current) {
            userVideoRef.current.srcObject = stream;
          }
          localStreamRef.current = stream;
          setMediaStream(stream);
        })
        .catch(err => {
            if (!isActive) return;

            let errorMsg = he.errors.cameraMicFailed;
            
            if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
              errorMsg = he.errors.noCameraMicFound;
              console.warn("No camera/microphone device found.");
            } else if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
              errorMsg = he.errors.cameraAccessDenied;
              console.error("Camera/Mic Access Error:", err);
            } else {
              console.error("Camera/Mic Access Error:", err);
            }
            
            // Fallback 1: Try Audio Only (User might have no camera)
            navigator.mediaDevices.getUserMedia({ video: false, audio: true })
                .then(stream => {
                    console.log("Fallback to Audio-only stream");
                    localStreamRef.current = stream;
                    setMediaStream(stream);
                    setError(null); 
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
                            setError(errorMsg);
                        });
                });
        });
    } else {
      stopLocalStream();
    }

    return () => {
      isActive = false;
      stopLocalStream();
    };
  }, [isInCall]);

  return { userVideoRef, mediaStream, error };
};
