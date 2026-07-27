'use client';

import React, { useState } from 'react';
import { Activity, ShieldAlert, CheckCircle2, Server, Terminal, RefreshCw, Cpu, Layers, ArrowUpRight, Wrench } from 'lucide-react';

export const LiveMetrologySuite: React.FC = () => {
  const [activeServer, setActiveServer] = useState<number>(0);
  const [selectedDrift, setSelectedDrift] = useState<number>(1);
  const [filterLayer, setFilterLayer] = useState<string>('ALL');
  const [isSynthesized, setIsSynthesized] = useState<boolean>(false);

  const servers = [
    { id: 'srv-mcp-billing', name: 'billing-stripe-mcp', rev: 'v2026-07-24', health: 98.7, rps: 0.18, status: 'ONLINE', tools: 14, driftCount: 1 },
    { id: 'srv-mcp-vector', name: 'pgvector-kb-mcp', rev: 'v2026-06-12', health: 100.0, rps: 0.12, status: 'ONLINE', tools: 8, driftCount: 0 },
    { id: 'srv-mcp-crm', name: 'hubspot-crm-mcp', rev: 'v2026-05-30', health: 92.4, rps: 0.19, status: 'EXCURSION', tools: 22, driftCount: 2 },
    { id: 'srv-mcp-devops', name: 'github-repo-ops', rev: 'v2026-07-01', health: 100.0, rps: 0.08, status: 'ONLINE', tools: 19, driftCount: 0 },
  ];

  const drifts = [
    {
      id: 0,
      server: 'hubspot-crm-mcp',
      layer: 'L0',
      title: 'Required Field Insertion on Tool `create_contact`',
      confidence: 1.000,
      time: '12 mins ago',
      desc: 'Tool schema suddenly added required argument `hubspot_owner_id` without bumping protocol revision.',
      evidence: '{"field": "hubspot_owner_id", "old_required": false, "new_required": true, "severity": "CRITICAL_BREAK"}'
    },
    {
      id: 1,
      server: 'billing-stripe-mcp',
      layer: 'L2',
      title: 'Statistical Unit Shift on `calculate_freight_rate`',
      confidence: 0.998,
      time: '24 mins ago',
      desc: 'Observed float weight distribution shifted by factor of 2.20x (lbs vs kg). KS-test p=0.0003 <= α (0.05).',
      evidence: '{"test": "two_sample_ks", "statistic_D": 0.482, "p_value_raw": 0.0003, "benjamini_hochberg_fdr": "REJECT_NULL"}'
    },
    {
      id: 2,
      server: 'hubspot-crm-mcp',
      layer: 'L3',
      title: 'Semantic Embedding Centroid Divergence',
      confidence: 0.945,
      time: '1 hr ago',
      desc: 'OpenAI text-embedding-3-small vectors for tool docstring shifted 0.28 cosine distance from 30-day baseline.',
      evidence: '{"embedding_dim": 1536, "baseline_centroid_dist": 0.04, "observed_dist": 0.28, "threshold": 0.20}'
    },
  ];

  const filteredDrifts = filterLayer === 'ALL' ? drifts : drifts.filter(d => d.layer === filterLayer);
  const currentDrift = drifts[selectedDrift];

  return (
    <div className="space-y-8">
      
      {/* 1. MCP SERVER TELEMETRY GRID */}
      <div>
        <div className="flex items-center justify-between text-xs font-mono pb-3 border-b border-[#1A1B1E]/10 mb-4">
          <div className="flex items-center space-x-2 font-bold text-[#1A1B1E]">
            <Server size={14} className="text-[#3B5249]" />
            <span>ACTIVE MONITORED MCP CLUSTERS (NON-INVASIVE PROBE CAP ≤ 0.20 RPS)</span>
          </div>
          <span className="text-[#3B5249] font-semibold bg-[#3B5249]/10 px-2 py-0.5 rounded flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[#3B5249] animate-pulse"></span>
            <span>SYSTEM HEALTH: 97.8%</span>
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {servers.map((srv, idx) => {
            const isSelected = activeServer === idx;
            const hasExcursion = srv.status === 'EXCURSION' || srv.driftCount > 0;

            return (
              <div
                key={srv.id}
                onClick={() => setActiveServer(idx)}
                className={`p-5 rounded-xl border font-mono text-xs cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-[#1A1B1E] text-[#FDFBF7] shadow-lg border-[#1A1B1E] translate-y-[-2px]'
                    : 'bg-[#FAF8F5] hover:bg-[#EBE5DC]/60 text-[#2C2E33] border-[#1A1B1E]/15 shadow-sm'
                }`}
              >
                <div className="flex items-center justify-between font-bold mb-3">
                  <span className="truncate pr-2">{srv.name}</span>
                  {hasExcursion ? (
                    <span className="text-[10px] bg-[#C84B31] text-white px-1.5 py-0.5 rounded">DRIFT</span>
                  ) : (
                    <span className="text-[10px] bg-[#3B5249] text-white px-1.5 py-0.5 rounded">OK</span>
                  )}
                </div>
                <div className="space-y-1.5 text-[11px] opacity-80 border-t border-black/10 pt-3">
                  <div className="flex justify-between"><span>Revision:</span> <span className="font-semibold">{srv.rev}</span></div>
                  <div className="flex justify-between"><span>Probe Rate:</span> <span className="text-[#E08E45] font-semibold">{srv.rps} RPS</span></div>
                  <div className="flex justify-between"><span>Tools Evaluated:</span> <span>{srv.tools}</span></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. REAL-TIME DRIFT EXCURSION STREAM & EVIDENCE INSPECTOR */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left column: Feed stream */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between text-xs font-mono font-bold">
            <span>DETECTED EXCURSION STREAM ({filteredDrifts.length})</span>
            <div className="flex space-x-1 bg-[#EBE5DC] p-1 rounded font-normal text-[10px]">
              {['ALL', 'L0', 'L2', 'L3'].map((l) => (
                <button
                  key={l}
                  onClick={() => setFilterLayer(l)}
                  className={`px-2 py-0.5 rounded font-bold transition-all ${
                    filterLayer === l ? 'bg-[#1A1B1E] text-[#FDFBF7]' : 'text-[#2C2E33] hover:text-[#C84B31]'
                  }`}
                >
                  {l}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            {filteredDrifts.map((drift, i) => {
              const isSelected = selectedDrift === drifts.findIndex(d => d.id === drift.id);
              const badgeCol = drift.layer === 'L0' ? '#D97706' : drift.layer === 'L2' ? '#3B5249' : '#C84B31';

              return (
                <div
                  key={drift.id}
                  onClick={() => { setSelectedDrift(drift.id); setIsSynthesized(false); }}
                  className={`p-4 rounded-lg border cursor-pointer transition-all space-y-2 font-sans ${
                    isSelected
                      ? 'bg-[#F4F1EA] border-[#1A1B1E] shadow-md ring-1 ring-[#1A1B1E]'
                      : 'bg-[#FAF8F5] border-[#1A1B1E]/15 hover:border-[#1A1B1E]/30 shadow-sm'
                  }`}
                >
                  <div className="flex items-center justify-between font-mono text-xs">
                    <span className="px-2 py-0.5 text-[10px] font-bold text-white rounded" style={{ backgroundColor: badgeCol }}>
                      {drift.layer} EXCURSION
                    </span>
                    <span className="text-[11px] text-[#6A707A] font-medium">{drift.time} • {drift.server}</span>
                  </div>
                  <div className="font-bold text-sm text-[#1A1B1E]">{drift.title}</div>
                  <div className="text-xs text-[#2C2E33]/80 line-clamp-2 leading-relaxed">{drift.desc}</div>
                  <div className="pt-2 border-t border-black/5 flex items-center justify-between font-mono text-[11px] text-[#6A707A]">
                    <span>FDR Confidence Score:</span>
                    <span className="text-[#1A1B1E] font-bold">{(drift.confidence * 100).toFixed(1)}%</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right column: Tolerance Band & Evidence Inspector */}
        <div className="lg:col-span-7 p-6 rounded-2xl bg-[#1A1B1E] text-[#FDFBF7] font-mono border border-black space-y-6 shadow-2xl">
          <div className="flex items-center justify-between pb-4 border-b border-white/10 text-xs">
            <div className="flex items-center space-x-2">
              <Terminal size={16} className="text-[#E08E45]" />
              <span className="font-bold tracking-wider">EVIDENCE INSPECTOR &amp; TOLERANCE BAND</span>
            </div>
            <span className="text-[#C84B31] font-bold bg-[#C84B31]/10 px-2.5 py-1 rounded border border-[#C84B31]/30">
              ACTION REQUIRED: DRIFT ACTIVE
            </span>
          </div>

          <div className="space-y-2">
            <div className="text-sm font-black text-white">{currentDrift.title}</div>
            <div className="text-xs text-[#E08E45]">{currentDrift.desc}</div>
          </div>

          {/* Interactive SVG Tolerance Band Visualization */}
          <div className="p-5 rounded-xl bg-[#2C2E33] border border-white/10 space-y-3">
            <div className="flex justify-between items-center text-[11px] text-white/70 font-bold">
              <span>TIME-SERIES VOLATILITY TOLERANCE ENVELOPE (±3.0σ)</span>
              <span className="text-[#3B5249]">INLINE METROLOGY</span>
            </div>
            
            <div className="w-full h-40 relative bg-[#1A1B1E] rounded-lg overflow-hidden border border-white/5 p-4 flex flex-col justify-between">
              <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-16 bg-[#3B5249]/20 border-y border-[#3B5249]/50 flex items-center px-3 text-[10px] text-[#3B5249] font-bold">
                <span>IN-SPEC NOMINAL ENVELOPE (FDR ALPHA = 0.05)</span>
              </div>
              
              <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 600 160">
                {/* Baseline trend line inside envelope */}
                <path d="M 0 80 Q 150 75 300 82 T 480 80 L 520 20 L 600 20" fill="none" stroke="#E08E45" strokeWidth="3" />
                
                {/* Excursion Diamond Marker */}
                <g transform="translate(520, 20)">
                  <polygon points="0,-8 8,0 0,8 -8,0" fill="#C84B31" />
                  <circle cx="0" cy="0" r="14" fill="none" stroke="#C84B31" strokeWidth="2" strokeDasharray="3 3" />
                </g>
              </svg>

              <div className="flex justify-between text-[10px] text-white/50 relative z-10">
                <span>T - 24h</span>
                <span>T - 12h</span>
                <span>T - 1h</span>
                <span className="text-[#C84B31] font-bold">T - NOW (EXCURSION EVENT)</span>
              </div>
            </div>
          </div>

          {/* Raw JSON Evidence Dump */}
          <div className="space-y-2">
            <span className="text-[11px] font-bold text-white/70 block uppercase tracking-wide">Raw Statistical Evidence (pytest verified)</span>
            <pre className="p-4 rounded bg-black/60 border border-white/10 text-[11px] overflow-x-auto text-[#3B5249] font-mono leading-relaxed">
              {JSON.stringify(JSON.parse(currentDrift.evidence), null, 2)}
            </pre>
          </div>

          {/* Autonomous Shim Generator Action */}
          <div className="pt-4 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center space-x-2 text-xs text-white/80 font-mono">
              <Wrench size={16} className="text-[#D97706]" />
              <span>Remediation Status: {isSynthesized ? "SHIM_PATCH_MERGED_SUCCESSFULLY" : "READY_FOR_AUTONOMOUS_SHIM"}</span>
            </div>
            
            <button
              onClick={() => setIsSynthesized(!isSynthesized)}
              className={`px-6 py-2.5 rounded font-bold text-xs uppercase tracking-wider transition-all font-mono shadow-lg flex items-center space-x-2 ${
                isSynthesized
                  ? 'bg-[#3B5249] hover:bg-[#3B5249]/90 text-white'
                  : 'bg-[#C84B31] hover:bg-[#D97706] text-white'
              }`}
            >
              {isSynthesized ? (
                <>
                  <CheckCircle2 size={14} />
                  <span>Shim Patch Applied</span>
                </>
              ) : (
                <>
                  <span>Synthesize Shim Patch</span>
                  <ArrowUpRight size={14} />
                </>
              )}
            </button>
          </div>
        </div>
      </div>

    </div>
  );
};
