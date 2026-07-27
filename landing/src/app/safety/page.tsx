'use client';

import React from 'react';
import { SafetyGateTester } from '@/components/interactive/SafetyGateTester';
import { PatchDiffPreview } from '@/components/interactive/PatchDiffPreview';
import { ShieldCheck, Wrench, Terminal, ArrowRight, Lock } from 'lucide-react';
import Link from 'next/link';

export default function SafetyPage() {
  return (
    <div className="min-h-screen w-full max-w-7xl mx-auto px-6 py-12 space-y-24 pb-32">
      
      {/* HEADER */}
      <div className="space-y-4 max-w-3xl">
        <div className="inline-flex items-center space-x-2 font-mono text-xs font-bold text-[#3B5249] uppercase tracking-widest">
          <ShieldCheck size={14} />
          <span>SAFETY ARCHITECTURE & AUTOMATED SHIM REMEDIATION</span>
        </div>
        <h1 className="text-4xl lg:text-6xl font-black text-[#1A1B1E] tracking-tight">
          Non-invasive probing with guaranteed read-only execution.
        </h1>
        <p className="text-base text-[#2C2E33]/85 font-medium leading-relaxed">
          A single accidental write to a production MCP database during an active scan would compromise enterprise reliability forever. Kilter enforces a hard code-level read-only gate before schema synthesis ever initiates.
        </p>
      </div>

      {/* SAFETY GATE INTERACTIVE TEST BENCH */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-extrabold text-[#1A1B1E] tracking-tight">Interactive Probe Safety Gate</h2>
          <span className="font-mono text-xs text-[#C84B31] font-bold">SAFETY ENGINE: ONLINE</span>
        </div>
        <SafetyGateTester />
      </section>

      {/* REMEDIATION PATCH GENERATION PREVIEW */}
      <section className="space-y-6">
        <div className="max-w-2xl space-y-2">
          <div className="inline-flex items-center space-x-1 font-mono text-xs font-bold text-[#D97706] uppercase">
            <Wrench size={12} />
            <span>Autonomous Repair</span>
          </div>
          <h2 className="text-3xl font-black text-[#1A1B1E] tracking-tight">
            Automated Shim & Pin Patch Generation
          </h2>
          <p className="text-sm text-[#2C2E33]/80">
            When Kilter detects an L2 statistical unit shift (such as an MCP provider switching weights from `kg` to `lbs`), our remediation engine immediately synthesizes a unified diff shim to normalize inputs without downtime.
          </p>
        </div>
        <PatchDiffPreview />
      </section>

      {/* FOOTER ACTION */}
      <div className="flex justify-between items-center pt-8 border-t border-[#1A1B1E]/10 font-mono text-xs">
        <Link href="/engine" className="text-[#2C2E33] hover:text-[#C84B31] transition-colors">
          ← Back to 4-Layer Diff Engine
        </Link>
        <Link href="/demo" className="px-5 py-2.5 bg-[#1A1B1E] text-[#FDFBF7] font-bold rounded uppercase hover:bg-[#C84B31] transition-colors flex items-center space-x-1">
          <span>Connect to Live Suite (:3005)</span>
          <ArrowRight size={14} />
        </Link>
      </div>

    </div>
  );
}
