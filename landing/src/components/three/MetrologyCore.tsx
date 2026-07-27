'use client';

import React, { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Float, Html, Line } from '@react-three/drei';
import * as THREE from 'three';

interface MetrologyCoreProps {
  isEntered?: boolean;
  onSelectLayer?: (index: number | null) => void;
}

export const MetrologyCore: React.FC<MetrologyCoreProps> = ({
  isEntered = false,
  onSelectLayer,
}) => {
  const groupRef = useRef<THREE.Group>(null);
  const coreRef = useRef<THREE.Mesh>(null);
  const [hoveredLayer, setHoveredLayer] = useState<number | null>(null);
  const [activeLayer, setActiveLayer] = useState<number | null>(null);

  // 4 Metrology Strata definitions matching genuine Kilter specification
  const layers = [
    { name: "L0 CAPABILITY", sub: "Protocol Revision & Tools", yOffset: 1.35, color: "#D97706", detail: "Confidence 1.000 • Structural Gate" },
    { name: "L1 STRUCTURAL", sub: "JSON Shape Thumbprints", yOffset: 0.45, color: "#E08E45", detail: "items[*] Array Collapsing" },
    { name: "L2 STATISTICAL", sub: "KS-Test & Benjamini-Hochberg", yOffset: -0.45, color: "#3B5249", detail: "3.00σ Excursion Threshold" },
    { name: "L3 SEMANTIC", sub: "1536-dim pgvector Centroids", yOffset: -1.35, color: "#C84B31", detail: "OpenAI Embedding Cosine Dist" },
  ];

  useFrame((state, delta) => {
    if (!groupRef.current) return;

    // Smooth model positioning & scaling based on interactive state
    // Shifting default X position to -0.45 guarantees zero clipping on right-side HTML tags
    const targetScale = isEntered ? 1.25 : 1.05;
    const targetY = isEntered && activeLayer !== null ? -layers[activeLayer].yOffset * 1.4 : 0;
    const targetX = isEntered ? -0.7 : -0.45;

    groupRef.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.08);
    groupRef.current.position.lerp(new THREE.Vector3(targetX, targetY, 0), 0.08);

    // Gentle idle rotation & cursor parallax reactivity
    if (!isEntered || activeLayer === null) {
      groupRef.current.rotation.y += delta * 0.15;
      const targetRotX = state.pointer.y * 0.25;
      const targetRotZ = -state.pointer.x * 0.25;
      groupRef.current.rotation.x = THREE.MathUtils.lerp(groupRef.current.rotation.x, targetRotX, 0.08);
      groupRef.current.rotation.z = THREE.MathUtils.lerp(groupRef.current.rotation.z, targetRotZ, 0.08);
    }

    // Inner mechanical core rapid rotation
    if (coreRef.current) {
      coreRef.current.rotation.y -= delta * 0.8;
      coreRef.current.rotation.x += delta * 0.3;
    }
  });

  const handleLayerClick = (idx: number, e: any) => {
    e.stopPropagation();
    const next = activeLayer === idx ? null : idx;
    setActiveLayer(next);
    if (onSelectLayer) onSelectLayer(next);
  };

  return (
    <Float speed={2.0} rotationIntensity={0.2} floatIntensity={0.5}>
      <group ref={groupRef} position={[-0.45, 0, 0]}>
        
        {/* Central Vertical Metrology Conduit / Data Axis */}
        <mesh position={[0, 0, 0]}>
          <cylinderGeometry args={[0.06, 0.06, 4.0, 32]} />
          <meshStandardMaterial color="#1A1B1E" metalness={0.9} roughness={0.1} />
        </mesh>

        {/* Rotating Central Intelligent Vector Core (pgvector centroid) */}
        <mesh ref={coreRef} position={[0, 0, 0]}>
          <icosahedronGeometry args={[0.45, 1]} />
          <meshStandardMaterial
            color="#C84B31"
            wireframe
            wireframeLinewidth={3}
            emissive="#C84B31"
            emissiveIntensity={0.7}
          />
        </mesh>

        {/* Layered Cross-Cut Assemblies */}
        {layers.map((layer, idx) => {
          const isHovered = hoveredLayer === idx;
          const isSelected = activeLayer === idx;

          const currentY = isEntered ? layer.yOffset * 1.6 : layer.yOffset;
          const ringRadius = 1.5 - idx * 0.1;

          return (
            <group
              key={layer.name}
              position={[0, currentY, 0]}
              onPointerOver={(e) => { e.stopPropagation(); setHoveredLayer(idx); }}
              onPointerOut={() => setHoveredLayer(null)}
              onClick={(e) => handleLayerClick(idx, e)}
            >
              {/* Outer Precision Engineering Ring Disc */}
              <mesh rotation={[Math.PI / 2, 0, 0]}>
                <torusGeometry args={[ringRadius, 0.07, 24, 64]} />
                <meshStandardMaterial
                  color={isHovered || isSelected ? layer.color : "#2C2E33"}
                  metalness={0.6}
                  roughness={0.3}
                  emissive={isHovered || isSelected ? layer.color : "#1A1B1E"}
                  emissiveIntensity={0.4}
                />
              </mesh>

              {/* Internal Cross-Cut Strata Glass Plate */}
              <mesh rotation={[Math.PI / 2, 0, 0]}>
                <ringGeometry args={[0.18, ringRadius - 0.07, 48]} />
                <meshStandardMaterial
                  color={isHovered || isSelected ? layer.color : "#EBE5DC"}
                  transparent
                  opacity={isHovered || isSelected ? 0.65 : 0.35}
                  metalness={0.4}
                  roughness={0.5}
                  side={THREE.DoubleSide}
                />
              </mesh>

              {/* Orbital Metrology Marker Diamonds */}
              <mesh position={[ringRadius, 0, 0]} rotation={[0, 0, Math.PI / 4]}>
                <boxGeometry args={[0.16, 0.16, 0.16]} />
                <meshStandardMaterial color={layer.color} emissive={layer.color} emissiveIntensity={0.8} />
              </mesh>
              <mesh position={[-ringRadius, 0, 0]} rotation={[0, 0, Math.PI / 4]}>
                <boxGeometry args={[0.16, 0.16, 0.16]} />
                <meshStandardMaterial color={layer.color} emissive={layer.color} emissiveIntensity={0.8} />
              </mesh>

              {/* Tighter HTML 3D Callout (Closer offset prevents edge clipping) */}
              <Html position={[ringRadius + 0.18, 0, 0]} center className="pointer-events-none whitespace-nowrap z-10">
                <div className={`px-3 py-1 rounded border shadow-md backdrop-blur font-mono transition-all ${
                  isHovered || isSelected
                    ? 'bg-[#1A1B1E]/95 border-[#E08E45] scale-105 shadow-xl text-white'
                    : 'bg-[#FAF8F5]/90 border-[#1A1B1E]/20 text-[#1A1B1E] opacity-95'
                }`}>
                  <div className="flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: layer.color }}></span>
                    <span className="text-[11px] font-black tracking-wide uppercase">
                      {layer.name}
                    </span>
                  </div>
                  <div className={`text-[9px] ${isHovered || isSelected ? 'text-[#FAF8F5]/80' : 'text-[#6A707A]'} block font-sans mt-0.5 font-medium`}>
                    {layer.sub}
                  </div>
                  {(isSelected || isHovered) && (
                    <div className="text-[9px] font-mono mt-1 font-bold pt-1 border-t border-white/10" style={{ color: layer.color }}>
                      {layer.detail}
                    </div>
                  )}
                </div>
              </Html>

              {/* Connecting Lead Guide Line */}
              <Line
                points={[
                  [0, 0, 0],
                  [ringRadius + 0.15, 0, 0],
                ]}
                color={layer.color}
                lineWidth={1.5}
              />
            </group>
          );
        })}
      </group>
    </Float>
  );
};
