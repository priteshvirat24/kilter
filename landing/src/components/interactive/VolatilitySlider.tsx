'use client';

import React, { useState } from 'react';
import { Sliders, ShieldAlert, CheckCircle2, Activity } from 'lucide-react';

export const VolatilitySlider: React.FC = () => {
  const [volatility, setVolatility] = useState<number>(0.15); // 0.00 to 1.00
  const [rawShift, setRawShift] = useState<number>(2.40); // Standard deviations

  // Kilter volatility engine logic: adjusted threshold = base_threshold (3.0) * (1 + volatility * 2)
  const baseThreshold = 3.00;
  const effectiveThreshold = baseThreshold * (1 + volatility * 2);
  const isAlarmTriggered = rawShift >= effectiveThreshold;

  return (
    <div className="p-8 rounded-xl glass-card border border-[#1A1B1E]/10 space-y-8 max-w-3xl mx-auto shadow-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1A1B1E]/10 pb-6">
        <div>
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-1 bg-[#3B5249]/10 text-[#3B5249] rounded">
            L2 Statistical Volatility Profiler
          </span>
          <h3 className="text-xl font-extrabold text-[#1A1B1E] mt-2 tracking-tight">
            Dynamic Excursion Suppression
          </h3>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono text-[#6A707A]">
          <Sliders size={14} className="text-[#E08E45]" />
          <span>FDR Alpha: 0.05 (Benjamini-Hochberg)</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Sliders */}
        <div className="space-y-6">
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono font-medium">
              <span className="text-[#2C2E33]">Baseline Field Volatility (v)</span>
              <span className="text-[#C84B31] font-bold">{volatility.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={volatility}
              onChange={(e) => setVolatility(parseFloat(e.target.value))}
              className="w-full accent-[#C84B31] cursor-pointer"
            />
            <p className="text-[11px] text-[#6A707A]">
              {volatility < 0.2 ? "Stable numeric metric (e.g. processing_fee_pct)." : volatility < 0.6 ? "Moderately fluctuating load latency metric." : "Highly random field (e.g. timestamp or request_id)."}
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono font-medium">
              <span className="text-[#2C2E33]">Observed Shift Intensity (σ)</span>
              <span className="text-[#1A1B1E] font-bold">{rawShift.toFixed(2)}σ</span>
            </div>
            <input
              type="range"
              min="0"
              max="7"
              step="0.1"
              value={rawShift}
              onChange={(e) => setRawShift(parseFloat(e.target.value))}
              className="w-full accent-[#1A1B1E] cursor-pointer"
            />
          </div>
        </div>

        {/* Visual Diagnostic Output */}
        <div className={`p-6 rounded-lg border flex flex-col justify-between transition-colors ${
          isAlarmTriggered ? 'bg-[#C84B31]/5 border-[#C84B31]/30' : 'bg-[#3B5249]/5 border-[#3B5249]/30'
        }`}>
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase text-[#6A707A]">Evaluation Output</span>
              {isAlarmTriggered ? (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-bold uppercase bg-[#C84B31] text-[#FDFBF7]">
                  <ShieldAlert size={12} />
                  <span>Drift Excursion</span>
                </span>
              ) : (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-bold uppercase bg-[#3B5249] text-[#FDFBF7]">
                  <CheckCircle2 size={12} />
                  <span>Suppressed (In-Spec)</span>
                </span>
              )}
            </div>

            <div className="mt-6 space-y-2 font-mono">
              <div className="flex justify-between text-xs">
                <span>Nominal Tolerance Band:</span>
                <span className="font-semibold">±{effectiveThreshold.toFixed(2)}σ</span>
              </div>
              <div className="flex justify-between text-xs">
                <span>Observed Deviation:</span>
                <span className={isAlarmTriggered ? "text-[#C84B31] font-bold" : "text-[#3B5249] font-bold"}>
                  {rawShift.toFixed(2)}σ
                </span>
              </div>
            </div>
          </div>

          <p className="mt-6 text-[11px] text-[#2C2E33]/80 leading-relaxed border-t border-black/5 pt-4 font-normal">
            {isAlarmTriggered
              ? "The observed shift exceeds the dynamically computed volatility threshold. An action-required drift excursion alert is emitted to downstream agents."
              : "Despite variation, Kilter suppresses the alert because normal baseline volatility accounts for this deviation, avoiding pager fatigue and false-positive model breaks."}
          </p>
        </div>
      </div>
    </div>
  );
};
