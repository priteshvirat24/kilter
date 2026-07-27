'use client';

import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import { Activity } from 'lucide-react';

interface ThreeCanvasProps {
  children: React.ReactNode;
  cameraPosition?: [number, number, number];
  fov?: number;
  enableZoom?: boolean;
  enablePan?: boolean;
  className?: string;
  onPointerMissed?: () => void;
}

// Fallback loader to prevent invisible suspense stalls
const MetrologyLoader = () => {
  return (
    <Html center>
      <div className="flex flex-col items-center space-y-3 p-4 rounded-lg bg-[#1A1B1E] text-[#FDFBF7] font-mono text-xs shadow-xl border border-white/10 w-60">
        <Activity size={24} className="text-[#E08E45] animate-bounce" />
        <div className="text-center font-bold tracking-wider uppercase">INITIALIZING METROLOGY CORE...</div>
        <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
          <div className="bg-[#C84B31] h-full w-1/2 animate-pulse rounded-full"></div>
        </div>
      </div>
    </Html>
  );
};

export const ThreeCanvas: React.FC<ThreeCanvasProps> = ({
  children,
  cameraPosition = [4, 2.5, 5.5],
  fov = 42,
  enableZoom = false,
  enablePan = false,
  className = "w-full h-full min-h-[500px]",
  onPointerMissed,
}) => {
  return (
    <div className={`relative ${className}`}>
      <Canvas
        camera={{ position: cameraPosition, fov }}
        dpr={[1, 2]}
        shadows={false}
        onPointerMissed={onPointerMissed}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
        style={{ width: '100%', height: '100%' }}
      >
        <Suspense fallback={<MetrologyLoader />}>
          {/* Robust studio multidirectional illumination */}
          <ambientLight intensity={1.1} color="#FAF8F5" />
          <directionalLight position={[10, 12, 10]} intensity={2.0} color="#FFFFFF" />
          <directionalLight position={[-10, -8, -5]} intensity={1.2} color="#6A7B4C" />
          <directionalLight position={[0, 10, -10]} intensity={1.0} color="#E08E45" />
          <pointLight position={[0, 0, 4]} intensity={2.5} color="#D97706" distance={15} />
          
          {children}

          <OrbitControls
            enableZoom={enableZoom}
            enablePan={enablePan}
            rotateSpeed={0.5}
            dampingFactor={0.08}
            makeDefault
            target={[0, 0, 0]}
            minPolarAngle={Math.PI * 0.15}
            maxPolarAngle={Math.PI * 0.85}
          />
        </Suspense>
      </Canvas>
      
      {/* HUD Edge Coordinates */}
      <div className="absolute top-4 right-4 pointer-events-none text-[10px] font-mono text-[#6A707A]/80 uppercase tracking-wider flex flex-col items-end z-10">
        <span>CAM: FOV {fov}° | ORIENT: ORBITAL_FREE</span>
        <span>ENGINE: KILTER_L0_L3_ACTIVE</span>
      </div>
    </div>
  );
};
