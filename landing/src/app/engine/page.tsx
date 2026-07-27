'use client';

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { VolatilitySlider } from '@/components/interactive/VolatilitySlider';
import { Layers, ArrowRight } from 'lucide-react';
import Link from 'next/link';

// Guarantee zero SSR blockages for WebGL Three.js canvas in App Router
const ThreeCanvas = dynamic(() => import('@/components/three/ThreeCanvas').then((mod) => mod.ThreeCanvas), { ssr: false });
const ExplodedLayers = dynamic(() => import('@/components/three/ExplodedLayers').then((mod) => mod.ExplodedLayers), { ssr: false });

export default function EnginePage() {
  const [explosionFactor, setExplosionFactor] = useState<number>(0.6);
  const [highlighted, setHighlighted] = useState<number | null>(null);

  const strataInfo = [
    { title: "L0 Capability Ring", code: "engine/diff/l0_capability.py", color: "#D97706", desc: "Monitors tool addition/removal, required field insertions, enum modifications, and protocol revision drift. Any required field addition is categorized as a breaking change with confidence 1.000." },
    { title: "L1 Structural Strata", code: "engine/diff/l1_structural.py", color: "#E08E45", desc: "Performs recursive shape fingerprinting. Lists are collapsed using array index notation (items[*]) to create stable structural hashes regardless of item counts." },
    { title: "L2 Statistical Grid", code: "engine/diff/l2_statistical.py", color: "#3B5249", desc: "Executes continuous Kolmogorov-Smirnov tests, categorical G-tests, Population Stability Index (PSI), and Rank-Biased Overlap (RBO). Applies Benjamini-Hochberg FDR correction." },
    { title: "L3 Semantic Core", code: "engine/diff/l3_semantic.py", color: "#C84B31", desc: "Computes cosine distance on 1536-dimensional embeddings (OpenAI text-embedding-3-small) stored in PostgreSQL pgvector to flag prompt centroid shifts and capability dispersion." },
  ];

  return (
    <div className="min-h-screen w-full max-w-7xl mx-auto px-6 py-12 space-y-24 pb-32">
      
      {/* HEADER */}
      <div className="space-y-4 max-w-3xl">
        <div className="inline-flex items-center space-x-2 font-mono text-xs font-bold text-[#D97706] uppercase tracking-widest">
          <Layers size={14} />
          <span>ARCHITECTURE • 4-LAYER DIFF ENGINE</span>
        </div>
        <h1 className="text-4xl lg:text-6xl font-black text-[#1A1B1E] tracking-tight">
          An interactive cross-section of pure metrology logic.
        </h1>
        <p className="text-base text-[#2C2E33]/85 font-medium leading-relaxed">
          Kilter’s engine is purely computational with zero I/O or network calls in the detection loop. Inspect each analytical layer below by dragging the structural decomposition slider.
        </p>
      </div>

      {/* THREE.JS EXPLODED VIEW SECTION */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center p-8 rounded-2xl glass-card border border-[#1A1B1E]/15 shadow-md">
        
        {/* Three.js Exploded Assembly */}
        <div className="lg:col-span-7 h-[550px] w-full relative bg-[#F4F1EA]/80 rounded-xl overflow-hidden border border-[#1A1B1E]/15 shadow-inner">
          <ThreeCanvas cameraPosition={[5, 2, 5]} fov={42}>
            <ExplodedLayers explosionFactor={explosionFactor} highlightedLayer={highlighted} />
          </ThreeCanvas>

          {/* Controls Overlay */}
          <div className="absolute bottom-6 left-6 right-6 bg-[#FAF8F5]/95 p-4 rounded-lg border border-[#1A1B1E]/15 space-y-2 backdrop-blur shadow-md z-20">
            <div className="flex justify-between text-xs font-mono font-bold">
              <span>STRATA DECOMPOSITION (EXPLODE)</span>
              <span className="text-[#C84B31]">{(explosionFactor * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={explosionFactor}
              onChange={(e) => setExplosionFactor(parseFloat(e.target.value))}
              className="w-full accent-[#1A1B1E] cursor-pointer"
            />
          </div>
        </div>

        {/* Strata Selection & Specification Cards */}
        <div className="lg:col-span-5 space-y-4">
          <div className="text-xs font-mono uppercase text-[#6A707A] font-bold px-1">
            SELECT A STRATUM TO ISOLATE METRICS:
          </div>
          {strataInfo.map((item, idx) => {
            const isSelected = highlighted === idx;
            return (
              <div
                key={item.title}
                onClick={() => setHighlighted(isSelected ? null : idx)}
                className={`p-5 rounded-lg border cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-[#1A1B1E] text-[#FDFBF7] shadow-lg border-[#1A1B1E] scale-[1.02]'
                    : 'bg-[#FAF8F5] text-[#2C2E33] hover:bg-[#EBE5DC] border-[#1A1B1E]/15 shadow-sm'
                }`}
              >
                <div className="flex items-center justify-between font-mono text-xs font-bold mb-2">
                  <span style={{ color: isSelected ? '#E08E45' : item.color }}>{item.title}</span>
                  <span className="text-[10px] opacity-70">{item.code}</span>
                </div>
                <p className="text-xs leading-relaxed opacity-90 font-sans font-normal">
                  {item.desc}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* VOLATILITY SUPPRESSION SECTION */}
      <div className="space-y-6">
        <div className="max-w-2xl space-y-2">
          <h2 className="text-3xl font-black text-[#1A1B1E] tracking-tight">
            Avoiding Pager Fatigue via Volatility Suppression
          </h2>
          <p className="text-sm text-[#2C2E33]/80">
            Why alert when a random `timestamp` or `uuid` fluctuates? Kilter computes per-field baseline volatility ($v$) and dynamically widens tolerance envelopes on dynamic parameters while locking down critical numeric fee models.
          </p>
        </div>

        <VolatilitySlider />
      </div>

      {/* FOOTER ACTION */}
      <div className="flex justify-between items-center pt-8 border-t border-[#1A1B1E]/10 font-mono text-xs">
        <Link href="/" className="text-[#2C2E33] hover:text-[#C84B31] transition-colors">
          ← Return to Overview
        </Link>
        <Link href="/safety" className="px-5 py-2.5 bg-[#1A1B1E] text-[#FDFBF7] font-bold rounded uppercase hover:bg-[#C84B31] transition-colors flex items-center space-x-1">
          <span>Proceed to Safety Gate & Remediation</span>
          <ArrowRight size={14} />
        </Link>
      </div>

    </div>
  );
}
