"use client";

import { useEffect, useRef } from "react";

interface LivingAvatarProps {
  src: string;
  isSpeaking: boolean;
  streamFrame?: string; // New prop for server-side frames
  className?: string;
}

export default function LivingAvatar({ src, isSpeaking, streamFrame, className }: LivingAvatarProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const animationFrameRef = useRef<number>(0);
  const timeRef = useRef<number>(0);

  // Load static avatar
  useEffect(() => {
    const img = new Image();
    img.src = src;
    img.onload = () => {
      imageRef.current = img;
    };
  }, [src]);

  // Handle Stream Frames (Priority)
  useEffect(() => {
    if (!streamFrame || !canvasRef.current) return;
    
    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
        // Draw the streamed frame directly
        const canvas = canvasRef.current!;
        // Match canvas size to display size
        const rect = canvas.getBoundingClientRect();
        if (canvas.width !== rect.width) canvas.width = rect.width;
        if (canvas.height !== rect.height) canvas.height = rect.height;
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw filling the canvas (simple cover)
        const scale = Math.max(canvas.width / img.width, canvas.height / img.height);
        const w = img.width * scale;
        const h = img.height * scale;
        const x = (canvas.width - w) / 2;
        const y = (canvas.height - h) / 2;
        
        ctx.drawImage(img, x, y, w, h);
    };
    img.src = `data:image/jpeg;base64,${streamFrame}`;

  }, [streamFrame]);

  // Handle Animation Loop (Fallback if no streamFrame)
  useEffect(() => {
    if (streamFrame) return; // detailed stream takes precedence

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const animate = () => {
      if (streamFrame) return; // Stop animation if streaming starts

      timeRef.current += 0.05;
      const img = imageRef.current;

      // Resize canvas
      const rect = canvas.getBoundingClientRect();
      if (canvas.width !== rect.width) canvas.width = rect.width;
      if (canvas.height !== rect.height) canvas.height = rect.height;

      if (!img || !img.complete) {
        animationFrameRef.current = requestAnimationFrame(animate);
        return;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();

      // --- "Alive" Parameters ---
      const breatheSpeed = 0.03;
      const breatheAmount = 0.02;
      const breatheScale = 1 + Math.sin(timeRef.current * breatheSpeed) * breatheAmount;

      let jawOffset = 0;
      let speakingScale = 1;
      
      if (isSpeaking) {
        const talkIntensity = 0.03; 
        speakingScale = 1 + Math.abs(Math.sin(timeRef.current * 10)) * talkIntensity;
        jawOffset = Math.sin(timeRef.current * 15) * 2; 
      }

      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const scale = Math.max(canvas.width / img.width, canvas.height / img.height);
      const drawWidth = img.width * scale * breatheScale;
      const drawHeight = img.height * scale * breatheScale * (isSpeaking ? speakingScale : 1);
      const x = centerX - drawWidth / 2;
      const y = centerY - drawHeight / 2 + jawOffset;

      ctx.drawImage(img, x, y, drawWidth, drawHeight);
      ctx.restore();
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameRef.current);
    };
  }, [isSpeaking, streamFrame]);

  return (
    <canvas 
      ref={canvasRef} 
      className={`w-full h-full object-cover ${className}`} 
    />
  );
}
