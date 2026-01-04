"use client";

import React, { useRef, useEffect, useState } from "react";
import { Canvas, useFrame, useLoader } from "@react-three/fiber";
import { useGLTF, Environment, OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { Viseme } from "../types/chat";

// --- 1. The 3D Model Component (Preferred) ---
function Model({ audioAnalyser, onError, visemes, audioElement }: { audioAnalyser: AnalyserNode | null, onError: () => void, visemes?: Viseme[], audioElement?: HTMLAudioElement | null }) {
  // Attempt to load the GLB. If it fails (404), catch error.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const gltf = useGLTF("/Businesswoman_Avatar_1202205922_texture.glb", true) as any; 
  
  useEffect(() => {
    // If loader returns null or error, trigger fallback
    if (!gltf || !gltf.scene) {
        onError();
    }
  }, [gltf, onError]);

  const headMeshRef = useRef<THREE.SkinnedMesh | null>(null);
  
  useEffect(() => {
    if (gltf.scene) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      gltf.scene.traverse((child: any) => {
        if (child.isMesh && child.morphTargetDictionary && !headMeshRef.current) {
           if (child.name.includes("Head") || child.name.includes("Face")) {
             headMeshRef.current = child;
           }
           if (!headMeshRef.current) headMeshRef.current = child;
        }
      });
    }
  }, [gltf.scene]);

  useFrame(() => {
    if (!headMeshRef.current || !headMeshRef.current.morphTargetInfluences || !headMeshRef.current.morphTargetDictionary) return;

    let targetOpenness = 0;

    // 1. Priority: Visemes (Timing-based Lip Sync)
    if (visemes && audioElement && !audioElement.paused) {
      const currentTime = audioElement.currentTime;
      // Find if current time is within any word boundary
      const activeWord = visemes.find(v => currentTime >= v.start && currentTime <= v.end);
      
      if (activeWord) {
        // Create a "talking" modulation
        // 0.3 base open + sine wave variation
        targetOpenness = 0.3 + Math.sin(currentTime * 25) * 0.2; 
      }
    } 
    // 2. Fallback: Audio Volume Analysis
    else if (audioAnalyser) {
        const dataArray = new Uint8Array(audioAnalyser.frequencyBinCount);
        audioAnalyser.getByteFrequencyData(dataArray);

        let sum = 0;
        const lowerBin = Math.floor(dataArray.length * 0.05);
        const upperBin = Math.floor(dataArray.length * 0.25);
        for (let i = lowerBin; i < upperBin; i++) sum += dataArray[i];
        const average = sum / (upperBin - lowerBin);
        targetOpenness = Math.min(1, (average / 255) * 2.5);
    }

    const jawIdx = headMeshRef.current.morphTargetDictionary["jawOpen"] ?? headMeshRef.current.morphTargetDictionary["viseme_aa"];
    if (jawIdx !== undefined) {
      const current = headMeshRef.current.morphTargetInfluences[jawIdx];
      // Smoothly interpolate to target
      headMeshRef.current.morphTargetInfluences[jawIdx] = THREE.MathUtils.lerp(current, targetOpenness, 0.2);
    }
  });

  if (!gltf.scene) return null;
  return <primitive object={gltf.scene} position={[0, -0.8, 0]} scale={1.0} />;
}

// --- 2. The 2.5D Fallback Component ---
function TwoDAvatar({ audioAnalyser }: { audioAnalyser: AnalyserNode | null }) {
  const texture = useLoader(THREE.TextureLoader, "/avatar.png");
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!meshRef.current) return;

    let loudness = 0;
    if (audioAnalyser) {
      const dataArray = new Uint8Array(audioAnalyser.frequencyBinCount);
      audioAnalyser.getByteFrequencyData(dataArray);
      const sum = dataArray.reduce((a, b) => a + b, 0);
      const avg = sum / dataArray.length;
      loudness = avg / 255;
    }

    const time = state.clock.getElapsedTime();
    const breathe = Math.sin(time * 2) * 0.02;
    const talkBounce = loudness * 0.1;

    const currentScale = 3 + breathe + (loudness * 0.2);
    meshRef.current.scale.set(currentScale, currentScale, 1);
    meshRef.current.position.y = -0.5 + talkBounce;
  });

  return (
    <mesh ref={meshRef} position={[0, -0.5, 0]}>
      <planeGeometry args={[1, 1]} />
      <meshBasicMaterial map={texture} transparent side={THREE.DoubleSide} />
    </mesh>
  );
}

// --- Wrapper to Handle Suspense & Errors ---
function SceneContent({ audioAnalyser, visemes, audioElement }: { audioAnalyser: AnalyserNode | null, visemes?: Viseme[], audioElement?: HTMLAudioElement | null }) {
    const [use3D, setUse3D] = useState(true);

    if (!use3D) {
        return <TwoDAvatar audioAnalyser={audioAnalyser} />;
    }

    return (
        <ErrorBoundary onFail={() => setUse3D(false)}>
            <Model 
              audioAnalyser={audioAnalyser} 
              onError={() => setUse3D(false)} 
              visemes={visemes}
              audioElement={audioElement}
            />
        </ErrorBoundary>
    );
}

// Simple Error Boundary for React Three Fiber
class ErrorBoundary extends React.Component<{ children: React.ReactNode, onFail: () => void }, { hasError: boolean }> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  componentDidCatch(error: any) {
    console.warn("Failed to load 3D Model, falling back to 2D:", error);
    this.props.onFail();
  }
  render() {
    if (this.state.hasError) return null;
    return this.props.children;
  }
}

export default function Avatar3D({ audioElement, visemes, audioAnalyser }: { audioElement: HTMLAudioElement | null, visemes?: Viseme[], audioAnalyser?: AnalyserNode | null }) {
  // Internal analyser state removed; use prop instead.

  return (
    <div className="w-full h-full bg-transparent">
      <Canvas camera={{ position: [0, 0, 5], fov: 60 }}>
        <ambientLight intensity={1} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        <Environment preset="city" />

        <React.Suspense fallback={<TwoDAvatar audioAnalyser={audioAnalyser || null} />}>
           <SceneContent audioAnalyser={audioAnalyser || null} visemes={visemes} audioElement={audioElement} />
        </React.Suspense>

        <OrbitControls enableZoom={false} enablePan={true} minPolarAngle={Math.PI / 2.2} maxPolarAngle={Math.PI / 1.8} />
      </Canvas>
    </div>
  );
}
