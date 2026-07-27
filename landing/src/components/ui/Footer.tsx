'use client';

import React from 'react';
import Link from 'next/link';
import { GitBranch, ExternalLink, Cpu, Activity, ArrowUpRight } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-[#F4F1EA] border-t border-[#1A1B1E]/10 pt-16 pb-12 px-6 metrology-grid">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-[#1A1B1E]/10">
        <div className="space-y-4 md:col-span-1">
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 rounded bg-[#1A1B1E] flex items-center justify-center font-bold text-[#FDFBF7] text-xs">
              K
            </div>
            <span className="font-extrabold tracking-wider text-sm text-[#1A1B1E]">KILTER</span>
          </div>
          <p className="text-xs text-[#2C2E33]/80 leading-relaxed font-normal">
            Autonomous multi-layer metrology and active drift detection for mission-critical Model Context Protocol (MCP) server infrastructures.
          </p>
          <div className="pt-2">
            <a
              href="https://github.com/priteshvirat24/kilter"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center space-x-2 text-xs font-mono font-medium text-[#1A1B1E] hover:text-[#C84B31] transition-colors"
            >
              <GitBranch size={16} />
              <span>priteshvirat24/kilter</span>
              <ArrowUpRight size={14} className="opacity-60" />
            </a>
          </div>
        </div>

        <div>
          <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-[#1A1B1E] mb-4">Architecture</h4>
          <ul className="space-y-2.5 text-xs text-[#2C2E33]/90 font-medium">
            <li><Link href="/engine" className="hover:text-[#C84B31] transition-colors flex items-center space-x-1"><span>L0 Capability Ring</span></Link></li>
            <li><Link href="/engine" className="hover:text-[#C84B31] transition-colors flex items-center space-x-1"><span>L1 Structural Strata</span></Link></li>
            <li><Link href="/engine" className="hover:text-[#C84B31] transition-colors flex items-center space-x-1"><span>L2 Statistical Grid (KS & PSI)</span></Link></li>
            <li><Link href="/engine" className="hover:text-[#C84B31] transition-colors flex items-center space-x-1"><span>L3 Semantic Centroids (pgvector)</span></Link></li>
            <li><Link href="/safety" className="hover:text-[#C84B31] transition-colors flex items-center space-x-1"><span>Volatility Suppressor</span></Link></li>
          </ul>
        </div>

        <div>
          <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-[#1A1B1E] mb-4">Live Suite & Probing</h4>
          <ul className="space-y-2.5 text-xs text-[#2C2E33]/90 font-medium">
            <li><Link href="/safety" className="hover:text-[#C84B31] transition-colors">Read-Only Safety Gate (is_tool_safe)</Link></li>
            <li><Link href="/safety" className="hover:text-[#C84B31] transition-colors">Shim Remediation Patch Generator</Link></li>
            <li><Link href="/demo" className="hover:text-[#C84B31] transition-colors">Live Dashboard Gateway</Link></li>
            <li><Link href="/demo" className="hover:text-[#C84B31] transition-colors flex items-center space-x-1"><span>Integrated Suite (:3005)</span></Link></li>
            <li><a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="hover:text-[#C84B31] transition-colors flex items-center space-x-1"><span>FastAPI OpenAPI Schema</span> <ExternalLink size={12} className="opacity-60" /></a></li>
          </ul>
        </div>

        <div>
          <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-[#1A1B1E] mb-4">Specifications & Quality</h4>
          <ul className="space-y-2.5 text-xs text-[#2C2E33]/90 font-medium font-mono">
            <li className="flex items-center justify-between py-1 border-b border-black/5"><span className="text-[#6A707A]">FPS TARGET:</span> <span className="font-bold text-[#3B5249]">60.0 FPS</span></li>
            <li className="flex items-center justify-between py-1 border-b border-black/5"><span className="text-[#6A707A]">TEST SUITE:</span> <span className="font-bold text-[#3B5249]">88 PASSED (0.00% err)</span></li>
            <li className="flex items-center justify-between py-1 border-b border-black/5"><span className="text-[#6A707A]">RATE LIMIT:</span> <span className="font-bold text-[#D97706]">≤ 0.20 RPS</span></li>
            <li className="flex items-center justify-between py-1"><span className="text-[#6A707A]">EMBEDDINGS:</span> <span className="font-bold text-[#1A1B1E]">1536-dim (OpenAI)</span></li>
          </ul>
        </div>
      </div>

      <div className="max-w-7xl mx-auto pt-8 flex flex-col md:flex-row items-center justify-between text-xs font-mono text-[#6A707A]">
        <div className="flex items-center space-x-2">
          <span>Kilter System Specification</span>
          <span>•</span>
          <span className="text-[#3B5249] font-medium">YC F26 Architecture Standard</span>
        </div>
        <div className="mt-4 md:mt-0 flex items-center space-x-6">
          <span>Zero Mock Content Standard</span>
          <span>•</span>
          <span>Designed with Metrology Precision</span>
        </div>
      </div>
    </footer>
  );
};
