'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { AnimatedCounter } from '@/components/ui/AnimatedCounter';
import { ArrowRight, Cpu, CheckCircle2, ShieldAlert, Zap } from 'lucide-react';

// Dynamic client-side imports to guarantee zero SSR WebGL canvas blockages
const ThreeCanvas = dynamic(() => import('@/components/three/ThreeCanvas').then((mod) => mod.ThreeCanvas), { ssr: false });
const MetrologyCore = dynamic(() => import('@/components/three/MetrologyCore').then((mod) => mod.MetrologyCore), { ssr: false });

export default function HomePage() {
  const [isEntered, setIsEntered] = useState<boolean>(false);
  const [selectedLayer, setSelectedLayer] = useState<number | null>(null);

  return (
    <div className="min-h-screen w-full flex flex-col space-y-32 pb-32">
      
      {/* SECTION 1: MASSIVE INTERACTIVE HERO EXPERIENCE */}
      <section className="relative min-h-[90vh] w-full max-w-7xl mx-auto px-6 pt-12 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        
        {/* Left Typography Column */}
        <div className="lg:col-span-6 space-y-8 z-10">
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-[#EBE5DC] border border-[#1A1B1E]/10 font-mono text-xs font-bold text-[#1A1B1E] tracking-wider uppercase">
            <span className="w-2 h-2 rounded-full bg-[#C84B31] animate-pulse"></span>
            <span>YC F26 • ACTIVE MCP DRIFT DETECTION</span>
          </div>

          <h1 className="text-5xl lg:text-7xl font-black tracking-tight text-[#1A1B1E] leading-[1.05] selection:bg-[#C84B31] selection:text-white">
            Before breaking changes catch fire.
          </h1>

          <p className="text-lg lg:text-xl text-[#2C2E33]/85 font-medium leading-relaxed max-w-xl">
            Autonomous multi-layer metrology for mission-critical Agentic systems. We actively probe Model Context Protocol servers to catch structural, statistical, and semantic drifts in real time.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Link
              href="/demo"
              className="px-8 py-4 bg-[#1A1B1E] hover:bg-[#C84B31] text-[#FDFBF7] font-extrabold text-sm uppercase tracking-wider rounded transition-all shadow-lg hover:shadow-xl flex items-center space-x-2 group"
            >
              <span>Launch Local Suite (:3005)</span>
              <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform text-[#E08E45]" />
            </Link>

            <button
              onClick={() => setIsEntered(!isEntered)}
              className={`px-6 py-4 rounded font-bold text-sm uppercase tracking-wider transition-all border font-mono flex items-center space-x-2 ${
                isEntered
                  ? 'bg-[#C84B31] text-[#FDFBF7] border-[#C84B31]'
                  : 'bg-[#FAF8F5] hover:bg-[#EBE5DC] text-[#1A1B1E] border-[#1A1B1E]/20'
              }`}
            >
              <Cpu size={16} className="text-[#E08E45]" />
              <span>{isEntered ? 'Exit Core View' : 'Enter The Machine'}</span>
            </button>
          </div>

          {/* Live Interactive Storytelling Status Notice */}
          <div className="pt-4 border-t border-[#1A1B1E]/10 flex items-center justify-between text-xs font-mono text-[#6A707A]">
            <span>INTERACTION: CLICK OR HOVER OVER 3D STRATA</span>
            <span className="text-[#3B5249] font-bold">ALPHA 0.05 FDR</span>
          </div>
        </div>

        {/* Right 3D Object Core (50-60% width) */}
        <div className="lg:col-span-6 h-[550px] lg:h-[700px] w-full relative">
          <div className="absolute inset-0 bg-gradient-to-tr from-[#FDFBF7] via-transparent to-[#F4F1EA]/50 rounded-full blur-2xl -z-10"></div>
          <ThreeCanvas enableZoom={false} fov={isEntered ? 36 : 42}>
            <MetrologyCore isEntered={isEntered} onSelectLayer={setSelectedLayer} />
          </ThreeCanvas>

          {isEntered && (
            <div className="absolute bottom-6 left-6 right-6 p-4 rounded-lg bg-[#1A1B1E]/95 text-[#FDFBF7] border border-white/10 text-xs font-mono backdrop-blur animate-in fade-in z-20">
              <div className="flex justify-between items-center text-[#E08E45] font-bold pb-2 border-b border-white/10 mb-2">
                <span>MACHINE DIAGNOSTIC MODE ON</span>
                <span>ZOOM COORD: ACTIVE</span>
              </div>
              <p className="text-white/80 leading-relaxed font-sans">
                You have entered Kilter&apos;s detection engine core. Each floating architectural disc executes pure, zero-I/O calculations across JSON schema fingerprints and 1536-dimensional OpenAI vector centroids.
              </p>
            </div>
          )}
        </div>
      </section>

      {/* SECTION 2: ATTENTION ENGINEERING ANIMATED METRIC DASHBOARD */}
      <section className="w-full max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-8 rounded-xl glass-card border border-[#1A1B1E]/10 space-y-4 shadow-sm">
            <span className="text-xs font-mono font-bold uppercase text-[#6A707A] tracking-wider">Statistical Rigor</span>
            <div className="text-5xl font-black text-[#1A1B1E]">
              <AnimatedCounter to={98.7} decimals={1} suffix="%" />
            </div>
            <p className="text-sm text-[#2C2E33]/80 font-medium">
              Excursion suppression rate on dynamic high-volatility fields (timestamps, UUIDs) using Benjamini-Hochberg FDR control.
            </p>
          </div>

          <div className="p-8 rounded-xl glass-card border border-[#1A1B1E]/10 space-y-4 shadow-sm">
            <span className="text-xs font-mono font-bold uppercase text-[#6A707A] tracking-wider">Detection Velocity</span>
            <div className="text-5xl font-black text-[#C84B31]">
              <AnimatedCounter to={12} decimals={0} suffix="x" />
            </div>
            <p className="text-sm text-[#2C2E33]/80 font-medium">
              Faster anomaly identification compared to passive log sampling. Active probing surfaces breaks before agent traffic arrives.
            </p>
          </div>

          <div className="p-8 rounded-xl glass-card border border-[#1A1B1E]/10 space-y-4 shadow-sm">
            <span className="text-xs font-mono font-bold uppercase text-[#6A707A] tracking-wider">Non-Invasive Hard Cap</span>
            <div className="text-5xl font-black text-[#3B5249]">
              <AnimatedCounter to={0.2} decimals={2} prefix="≤ " suffix=" RPS" />
            </div>
            <p className="text-sm text-[#2C2E33]/80 font-medium">
              Hard code-level throttle guarantees zero production load degradation during active schema synthesis cycles.
            </p>
          </div>
        </div>
      </section>

      {/* SECTION 3: PROBLEM VS SOLUTION ("THE SILENT BREAK") */}
      <section className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        <div className="lg:col-span-5 space-y-6">
          <span className="text-xs font-mono uppercase tracking-widest text-[#C84B31] font-bold">The Engineering Problem</span>
          <h2 className="text-4xl font-black tracking-tight text-[#1A1B1E]">
            LLMs fail silently when tools drift by a single unit.
          </h2>
          <p className="text-sm text-[#2C2E33]/80 leading-relaxed">
            When a third-party MCP provider changes a field from `kg` to `lbs`, or alters an enum value without bumping the protocol revision, standard monitors see HTTP 200 OK. Yet downstream AI agents hallucinate disastrously.
          </p>
          <div className="pt-2">
            <Link
              href="/engine"
              className="inline-flex items-center space-x-2 font-mono text-xs font-bold uppercase tracking-wider text-[#1A1B1E] hover:text-[#C84B31] transition-colors"
            >
              <span>Explore 4-Layer Metrology Engine</span>
              <ArrowRight size={14} />
            </Link>
          </div>
        </div>

        <div className="lg:col-span-7 p-8 rounded-xl bg-[#1A1B1E] text-[#FDFBF7] font-mono text-xs space-y-6 border border-black/20 shadow-xl">
          <div className="flex items-center justify-between pb-4 border-b border-white/10 text-[11px] text-[#6A707A]">
            <span>TELEMETRY: TIMELINE_STREAM_EXCURSION</span>
            <span className="text-[#C84B31] font-bold animate-pulse">CRITICAL_DRIFT_DETECTED</span>
          </div>
          <div className="space-y-4">
            <div className="p-3 rounded bg-white/5 border border-white/10 flex items-start justify-between">
              <div className="space-y-1">
                <span className="text-[#3B5249] font-bold block">T-0: BASELINE ESTABLISHED (3 CYCLES)</span>
                <span className="text-white/80">Tool `calculate_freight_rate`: weight_kg (float, range [0.5, 45.0])</span>
              </div>
              <CheckCircle2 size={18} className="text-[#3B5249]" />
            </div>
            
            <div className="p-3 rounded bg-[#C84B31]/10 border border-[#C84B31]/40 flex items-start justify-between">
              <div className="space-y-1">
                <span className="text-[#C84B31] font-bold block">T+20m: SILENT UNIT SHIFT (L2 STATISTICAL EXCURSION)</span>
                <span className="text-white/80">Observed weight_value mean shifted 2.20x (lbs vs kg). KS-test p=0.0003 &lt; α (0.05).</span>
              </div>
              <ShieldAlert size={18} className="text-[#C84B31]" />
            </div>

            <div className="p-3 rounded bg-[#E08E45]/10 border border-[#E08E45]/40 flex items-start justify-between">
              <div className="space-y-1">
                <span className="text-[#E08E45] font-bold block">REMEDIATION: AUTO-SHIM PATCH GENERATED</span>
                <span className="text-white/80">Shim patch `PatchResult` applied before AI orchestrator executes shipment contract.</span>
              </div>
              <Zap size={18} className="text-[#E08E45]" />
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4: NAVIGATION GATEWAY TO SPECIALIZED EXPERIENCES */}
      <section className="max-w-7xl mx-auto px-6">
        <div className="p-12 rounded-2xl bg-[#F4F1EA] border border-[#1A1B1E]/10 metrology-grid flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="space-y-2 max-w-xl">
            <span className="text-xs font-mono uppercase font-bold text-[#3B5249]">Deep Interactive Exploration</span>
            <h3 className="text-3xl font-black text-[#1A1B1E] tracking-tight">Ready to verify the algorithms?</h3>
            <p className="text-sm text-[#2C2E33]/80">
              Inspect our mathematical proofs, test the read-only safety gate in real time, or interact directly with our running local metrology dashboard integrated within this suite.
            </p>
          </div>
          <div className="flex flex-wrap gap-4">
            <Link href="/engine" className="px-6 py-3.5 rounded bg-[#1A1B1E] hover:bg-[#C84B31] text-[#FDFBF7] font-mono font-bold text-xs uppercase tracking-wider transition-colors">
              4-Layer Architecture
            </Link>
            <Link href="/safety" className="px-6 py-3.5 rounded bg-[#FAF8F5] border border-[#1A1B1E]/20 text-[#1A1B1E] hover:bg-[#EBE5DC] font-mono font-bold text-xs uppercase tracking-wider transition-colors">
              Test Safety Gate
            </Link>
            <Link href="/demo" className="px-6 py-3.5 rounded bg-[#3B5249] text-white font-mono font-bold text-xs uppercase tracking-wider transition-colors shadow">
              Live Gateway
            </Link>
          </div>
        </div>
      </section>

    </div>
  );
}
