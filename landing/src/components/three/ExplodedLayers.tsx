'use client';

import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html, Line } from '@react-three/drei';
import * as THREE from 'three';

interface ExplodedLayersProps {
  explosionFactor: number; // 0 to 1 slider value
  highlightedLayer: number | null;
}

export const ExplodedLayers: React.FC<ExplodedLayersProps> = ({
  explosionFactor,
  highlightedLayer,
}) => {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = THREE.MathUtils.lerp(groupRef.current.rotation.y, state.clock.elapsedTime * 0.15, 0.05);
    }
  });

  const specs = [
    { title: "L0 Capability", desc: "Tool Addition & Required Fields", yBase: 1.2, maxDiff: 2.5, col: "#D97706", detail: "Alerts on protocol revision mismatch or enum shrinkage." },
    { title: "L1 Structural", desc: "Response Shape Fingerprinting", yBase: 0.4, maxDiff: 0.8, col: "#E08E45", detail: "Collapses arbitrary array indices (items[*]) into uniform hashes." },
    { title: "L2 Statistical", desc: "Two-Sample KS & PSI Tests", yBase: -0.4, maxDiff: -0.8, col: "#3B5249", detail: "Benjamini-Hochberg FDR correction ensures α=0.05 across tools." },
    { title: "L3 Semantic", desc: "1536-dim pgvector Centroid Shift", yBase: -1.2, maxDiff: -2.5, col: "#C84B31", detail: "Cosine distance evaluation on OpenAI embedding vectors." },
  ];

  return (
    <group ref={groupRef} position={[-0.8, 0, 0]} scale={[1.05, 1.05, 1.05]}>
      {specs.map((spec, idx) => {
        const yPos = spec.yBase + spec.maxDiff * explosionFactor;
        const isHighlight = highlightedLayer === null || highlightedLayer === idx;

        return (
          <group key={spec.title} position={[0, yPos, 0]}>
            {/* Strata Plate */}
            <mesh rotation={[Math.PI / 2, 0, 0]}>
              <cylinderGeometry args={[1.8, 1.8, 0.07, 48]} />
              <meshStandardMaterial
                color={isHighlight ? spec.col : "#8C7A6B"}
                wireframe={!isHighlight}
                transparent
                opacity={isHighlight ? 0.85 : 0.25}
                metalness={0.6}
                roughness={0.3}
                emissive={isHighlight ? spec.col : "#000000"}
                emissiveIntensity={0.3}
              />
            </mesh>

            {/* Orbiting Diagnostic Particle Nodes */}
            <mesh position={[1.9, 0.1, 0]}>
              <sphereGeometry args={[0.1, 16, 16]} />
              <meshStandardMaterial color={spec.col} emissive={spec.col} emissiveIntensity={0.8} />
            </mesh>

            {/* Reliable HTML 3D Specification Label */}
            <Html position={[2.1, 0, 0]} center className="pointer-events-none whitespace-nowrap">
              <div className={`p-2.5 rounded-lg border shadow-md backdrop-blur transition-all font-mono text-xs ${
                isHighlight ? 'bg-[#1A1B1E]/95 border-[#E08E45] text-white shadow-xl' : 'bg-[#FAF8F5]/90 border-black/10 text-[#2C2E33] opacity-60'
              }`}>
                <div className="font-bold uppercase tracking-wider flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: spec.col }}></span>
                  <span className="text-[11px]" style={{ color: isHighlight ? '#E08E45' : spec.col }}>{spec.title}</span>
                </div>
                <div className={`text-[10px] font-sans mt-0.5 ${isHighlight ? 'text-white/80' : 'text-[#6A707A]'}`}>
                  {spec.desc}
                </div>
                {isHighlight && (
                  <div className="text-[9px] font-mono mt-1 pt-1 border-t border-white/10" style={{ color: spec.col }}>
                    {spec.detail}
                  </div>
                )}
              </div>
            </Html>

            {/* Vertical Connector guide lines when exploded */}
            {idx < 3 && (
              <Line
                points={[
                  [0, 0, 0],
                  [0, (specs[idx + 1].yBase + specs[idx + 1].maxDiff * explosionFactor) - yPos, 0],
                ]}
                color="#6A707A"
                lineWidth={1.5}
                dashed
              />
            )}
          </group>
        );
      })}
    </group>
  );
};
