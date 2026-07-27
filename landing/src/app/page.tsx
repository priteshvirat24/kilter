'use client';

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, Play } from 'lucide-react';
import Link from 'next/link';

// Guarantee zero SSR blockages for WebGL Three.js canvas in App Router
const ThreeCanvas = dynamic(() => import('@/components/three/ThreeCanvas').then((mod) => mod.ThreeCanvas), { ssr: false });
const MetrologyCore = dynamic(() => import('@/components/three/MetrologyCore').then((mod) => mod.MetrologyCore), { ssr: false });

export default function HomePage() {
  const [isEntered, setIsEntered] = useState<boolean>(false);
  const [selectedLayer, setSelectedLayer] = useState<number | null>(null);
  
  // Judge / Present Mode State
  const [judgeModeActive, setJudgeModeActive] = useState<boolean>(false);
  const [sequenceStep, setSequenceStep] = useState<number>(0);

  // Cinematic Sequence Logic (30-40 seconds total)
  useEffect(() => {
    if (!judgeModeActive) {
      setSequenceStep(0);
      return;
    }

    const timings = [
      6000,  // Step 1: The Problem
      7000,  // Step 2: The Silent Failure
      6000,  // Step 3: The Solution
      7000,  // Step 4: Multi-layer Metrology
      6000,  // Step 5: Conclusion
    ];

    let currentStep = 0;
    
    const advanceSequence = () => {
      if (currentStep < timings.length) {
        setSequenceStep(currentStep + 1);
        setTimeout(advanceSequence, timings[currentStep]);
        currentStep++;
      } else {
        setTimeout(() => setJudgeModeActive(false), 2000);
      }
    };

    setTimeout(advanceSequence, 500);

    return () => {
      // Cleanup on unmount or cancel
    };
  }, [judgeModeActive]);

  return (
    <div className="min-h-screen w-full flex flex-col pb-24 relative">
      
      {/* SECTION 1: CLEAN, PROFESSIONAL HERO EXPERIENCE */}
      <section className="relative min-h-[85vh] w-full max-w-7xl mx-auto px-6 pt-20 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        
        {/* Left Typography Column */}
        <div className={`lg:col-span-5 space-y-10 z-10 transition-opacity duration-1000 ${judgeModeActive ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-[#EBE5DC] border border-[#1A1B1E]/10 font-mono text-xs font-bold text-[#1A1B1E] tracking-wider uppercase">
            <span className="w-2 h-2 rounded-full bg-[#3B5249] animate-pulse"></span>
            <span>YC F26 • ACTIVE MCP DRIFT DETECTION</span>
          </div>

          <h1 className="text-5xl lg:text-7xl font-black tracking-tight text-[#1A1B1E] leading-[1.05] selection:bg-[#C84B31] selection:text-white">
            Before breaking changes catch fire.
          </h1>

          <p className="text-lg text-[#2C2E33]/85 font-medium leading-relaxed max-w-lg">
            Autonomous multi-layer metrology for mission-critical Agentic systems. We actively probe Model Context Protocol servers to catch structural, statistical, and semantic drifts in real time.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-4">
            <button
              onClick={() => setJudgeModeActive(true)}
              className="px-8 py-4 bg-[#1A1B1E] hover:bg-[#C84B31] text-[#FDFBF7] font-extrabold text-sm uppercase tracking-wider rounded transition-all shadow-lg hover:shadow-xl flex items-center space-x-2 group"
            >
              <Play size={16} fill="currentColor" className="group-hover:scale-110 transition-transform text-[#E08E45]" />
              <span>Run Present Mode</span>
            </button>

            <button
              onClick={() => setIsEntered(!isEntered)}
              className={`px-6 py-4 rounded font-bold text-sm uppercase tracking-wider transition-all border font-mono flex items-center space-x-2 ${
                isEntered
                  ? 'bg-[#C84B31] text-[#FDFBF7] border-[#C84B31]'
                  : 'bg-[#FAF8F5] hover:bg-[#EBE5DC] text-[#1A1B1E] border-[#1A1B1E]/20'
              }`}
            >
              <Cpu size={16} className="text-[#E08E45]" />
              <span>{isEntered ? 'Exit Core View' : 'Inspect Architecture'}</span>
            </button>
          </div>
        </div>

        {/* Right 3D Object Core (Takes full space during cinematic mode) */}
        <div className={`transition-all duration-1000 ease-in-out relative ${judgeModeActive ? 'lg:col-span-12 h-[80vh]' : 'lg:col-span-7 h-[600px] lg:h-[750px]'} w-full`}>
          <div className="absolute inset-0 bg-gradient-to-tr from-[#FDFBF7] via-transparent to-[#F4F1EA]/50 rounded-full blur-3xl -z-10"></div>
          
          <ThreeCanvas enableZoom={false} fov={judgeModeActive ? 30 : (isEntered ? 36 : 42)}>
            <MetrologyCore isEntered={isEntered || judgeModeActive} onSelectLayer={setSelectedLayer} />
          </ThreeCanvas>
        </div>
      </section>

      {/* FULL-SCREEN CINEMATIC PRESENTATION OVERLAY */}
      <AnimatePresence>
        {judgeModeActive && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 1.5 }}
            className="fixed inset-0 z-50 pointer-events-none flex flex-col items-center justify-center bg-[#FDFBF7]/85 backdrop-blur-sm"
          >
            {/* Cinematic Stop Button (Clickable) */}
            <div className="absolute top-8 right-8 pointer-events-auto">
              <button 
                onClick={() => setJudgeModeActive(false)}
                className="px-4 py-2 font-mono text-xs font-bold tracking-widest uppercase text-[#1A1B1E] border border-[#1A1B1E]/20 rounded hover:bg-[#1A1B1E] hover:text-white transition-colors"
              >
                End Presentation
              </button>
            </div>

            <div className="max-w-4xl w-full px-8 text-center relative z-10">
              <AnimatePresence mode="wait">
                {sequenceStep === 1 && (
                  <motion.div
                    key="step1"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20, filter: 'blur(10px)' }}
                    transition={{ duration: 1.2 }}
                    className="space-y-6"
                  >
                    <span className="font-mono text-sm tracking-widest text-[#C84B31] font-bold uppercase">The Engineering Problem</span>
                    <h2 className="text-5xl lg:text-7xl font-black text-[#1A1B1E] leading-tight tracking-tight">
                      Agentic AI fails silently when third-party tools drift by a single unit.
                    </h2>
                  </motion.div>
                )}

                {sequenceStep === 2 && (
                  <motion.div
                    key="step2"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20, filter: 'blur(10px)' }}
                    transition={{ duration: 1.2 }}
                    className="space-y-8"
                  >
                    <h2 className="text-4xl lg:text-6xl font-black text-[#1A1B1E] leading-tight tracking-tight">
                      When a provider changes <span className="text-[#E08E45] font-mono bg-[#E08E45]/10 px-2 rounded">kg</span> to <span className="text-[#C84B31] font-mono bg-[#C84B31]/10 px-2 rounded">lbs</span> without bumping the protocol revision...
                    </h2>
                    <p className="text-2xl text-[#2C2E33]/80 font-medium">
                      Standard monitors return HTTP 200 OK. The AI orchestrator hallucinates disastrously.
                    </p>
                  </motion.div>
                )}

                {sequenceStep === 3 && (
                  <motion.div
                    key="step3"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 1.05, filter: 'blur(10px)' }}
                    transition={{ duration: 1.5 }}
                    className="space-y-6"
                  >
                    <span className="font-mono text-sm tracking-widest text-[#3B5249] font-bold uppercase">The Solution</span>
                    <h2 className="text-6xl lg:text-8xl font-black text-[#1A1B1E] tracking-tighter">
                      Kilter.
                    </h2>
                  </motion.div>
                )}

                {sequenceStep === 4 && (
                  <motion.div
                    key="step4"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20, filter: 'blur(10px)' }}
                    transition={{ duration: 1.2 }}
                    className="space-y-6"
                  >
                    <h2 className="text-4xl lg:text-6xl font-black text-[#1A1B1E] leading-tight tracking-tight">
                      Autonomous multi-layer metrology.
                    </h2>
                    <p className="text-xl lg:text-2xl text-[#2C2E33]/80 font-medium max-w-3xl mx-auto leading-relaxed">
                      Executing purely computational Structural, Statistical, and Semantic drift detection in real-time, completely non-invasive to production load.
                    </p>
                  </motion.div>
                )}

                {sequenceStep === 5 && (
                  <motion.div
                    key="step5"
                    initial={{ opacity: 0, filter: 'blur(10px)' }}
                    animate={{ opacity: 1, filter: 'blur(0px)' }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 2 }}
                    className="space-y-6"
                  >
                    <h2 className="text-5xl lg:text-7xl font-black text-[#1A1B1E] tracking-tight">
                      Before breaking changes catch fire.
                    </h2>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* SECTION 2: MINIMAL GATEWAY (Replaces the noisy sections) */}
      <section className={`w-full max-w-7xl mx-auto px-6 mt-12 transition-opacity duration-1000 ${judgeModeActive ? 'opacity-0' : 'opacity-100'}`}>
        <div className="p-12 rounded-2xl bg-[#F4F1EA] border border-[#1A1B1E]/10 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="space-y-3 max-w-xl">
            <span className="text-xs font-mono uppercase font-bold text-[#3B5249] tracking-wider">Engineering Deep Dive</span>
            <h3 className="text-3xl font-black text-[#1A1B1E] tracking-tight">Verify the metrology architecture.</h3>
            <p className="text-sm text-[#2C2E33]/80 leading-relaxed font-medium">
              Inspect our 4-layer isolation logic, test the read-only safety gate in real time, or monitor the integrated live telemetry suite.
            </p>
          </div>
          <div className="flex flex-wrap gap-4">
            <Link href="/engine" className="px-6 py-3.5 rounded bg-[#1A1B1E] hover:bg-[#C84B31] text-[#FDFBF7] font-mono font-bold text-xs uppercase tracking-wider transition-colors shadow">
              4-Layer Diff Engine
            </Link>
            <Link href="/demo" className="px-6 py-3.5 rounded bg-[#FAF8F5] border border-[#1A1B1E]/20 text-[#1A1B1E] hover:bg-[#EBE5DC] font-mono font-bold text-xs uppercase tracking-wider transition-colors">
              Live Metrology Suite
            </Link>
          </div>
        </div>
      </section>

    </div>
  );
}
