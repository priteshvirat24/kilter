'use client';

import React from 'react';
import { Terminal, Cpu, Check, Server } from 'lucide-react';
import Link from 'next/link';
import { LiveMetrologySuite } from '@/components/interactive/LiveMetrologySuite';

export default function DemoGatewayPage() {
  return (
    <div className="min-h-screen w-full max-w-7xl mx-auto px-6 py-12 space-y-16 pb-32">
      
      {/* HEADER */}
      <div className="space-y-4 max-w-3xl">
        <div className="inline-flex items-center space-x-2 font-mono text-xs font-bold text-[#1A1B1E] uppercase tracking-widest bg-[#EBE5DC] px-3 py-1 rounded">
          <Terminal size={14} />
          <span>INTEGRATED METROLOGY SUITE • PORT 3005</span>
        </div>
        <h1 className="text-4xl lg:text-6xl font-black text-[#1A1B1E] tracking-tight">
          Active real-time telemetry &amp; drift inspection.
        </h1>
        <p className="text-base text-[#2C2E33]/85 font-medium leading-relaxed">
          Explore monitored Model Context Protocol clusters, verify live excursion streams across all four detection strata, and trigger autonomous shim remediation directly inside this integrated suite.
        </p>
      </div>

      {/* METROLOGY SUITE INTERACTIVE DASHBOARD */}
      <div className="p-8 rounded-2xl glass-card border border-[#1A1B1E]/15 shadow-xl">
        <LiveMetrologySuite />
      </div>

      {/* ARCHITECTURAL GUARANTEES FOOTER BAR */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-mono text-xs pt-4">
        <div className="p-6 rounded-lg bg-[#FAF8F5] border border-[#1A1B1E]/10 space-y-2 shadow-sm">
          <div className="flex justify-between items-center text-[#3B5249] font-bold">
            <span>ENGINE STATUS</span>
            <span className="w-2.5 h-2.5 rounded-full bg-[#3B5249] animate-pulse"></span>
          </div>
          <div className="text-base font-black text-[#1A1B1E]">Fully Integrated (:3005)</div>
          <div className="text-[11px] text-[#6A707A]">All telemetry and interactive probes execute directly within this unified suite.</div>
        </div>

        <div className="p-6 rounded-lg bg-[#FAF8F5] border border-[#1A1B1E]/10 space-y-2 shadow-sm">
          <div className="flex justify-between items-center text-[#D97706] font-bold">
            <span>FDR STATISTICAL RIGOR</span>
            <span className="w-2.5 h-2.5 rounded-full bg-[#D97706] animate-pulse"></span>
          </div>
          <div className="text-base font-black text-[#1A1B1E]">Benjamini-Hochberg Control</div>
          <div className="text-[11px] text-[#6A707A]">Alpha = 0.05 targets across dynamic MCP parameters.</div>
        </div>

        <div className="p-6 rounded-lg bg-[#1A1B1E] text-[#FDFBF7] space-y-2 shadow-md flex flex-col justify-between">
          <div>
            <span className="text-white/60 font-bold block pb-1 border-b border-white/10">SAFETY GATE</span>
            <div className="text-base font-black text-[#3B5249] mt-2">Max Rate: ≤ 0.20 RPS</div>
            <p className="text-[11px] text-[#FAF8F5]/80 mt-1 font-sans">
              Hard code-level throttle forbids database writes during synthesis.
            </p>
          </div>
        </div>
      </div>

      {/* FOOTER ACTION */}
      <div className="flex justify-between items-center pt-8 border-t border-[#1A1B1E]/10 font-mono text-xs">
        <Link href="/safety" className="text-[#2C2E33] hover:text-[#C84B31] transition-colors">
          ← Back to Safety Gate
        </Link>
        <Link href="/specs" className="px-5 py-2.5 bg-[#1A1B1E] text-[#FDFBF7] font-bold rounded uppercase hover:bg-[#C84B31] transition-colors">
          View Technical Specifications &amp; Math Proofs →
        </Link>
      </div>

    </div>
  );
}
