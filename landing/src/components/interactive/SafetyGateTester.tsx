'use client';

import React, { useState } from 'react';
import { ShieldCheck, ShieldAlert, Terminal, Play, Check } from 'lucide-react';

export const SafetyGateTester: React.FC = () => {
  const [toolName, setToolName] = useState<string>('create_billing_invoice');
  const [description, setDescription] = useState<string>('Creates a new chargeable invoice in Stripe and notifies client');
  const [tested, setTested] = useState<boolean>(true);

  // Kilter unsafe pattern matching exactly from engine/probe/probeset.py
  const unsafeWords = [
    'create', 'update', 'delete', 'write', 'send', 'post', 'execute',
    'run', 'submit', 'insert', 'modify', 'patch', 'put', 'remove',
    'destroy', 'wipe', 'reset', 'trigger'
  ];

  const evaluateSafety = (name: string, desc: string) => {
    const combined = `${name} ${desc}`.toLowerCase();
    const regex = new RegExp(`(?<![a-z])(${unsafeWords.join('|')})(?![a-z])`, 'i');
    const match = combined.match(regex);
    return {
      isSafe: !match,
      matchedWord: match ? match[0] : null
    };
  };

  const result = evaluateSafety(toolName, description);

  const sampleTools = [
    { name: "get_server_status", desc: "Reads current health telemetry from cluster" },
    { name: "delete_user_account", desc: "Permanently wipes user records from DB" },
    { name: "search_kb_articles", desc: "Queries PostgreSQL pgvector knowledge base" },
    { name: "trigger_webhook", desc: "Triggers external billing webhook event" },
  ];

  return (
    <div className="p-8 rounded-xl glass-card border border-[#1A1B1E]/10 max-w-4xl mx-auto space-y-8 shadow-sm">
      <div className="border-b border-[#1A1B1E]/10 pb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-1 bg-[#D97706]/10 text-[#D97706] rounded">
            Code-Level Safety Architecture (engine/probe/probeset.py)
          </span>
          <h3 className="text-xl font-extrabold text-[#1A1B1E] mt-2 tracking-tight">
            Read-Only Hard Gate (is_tool_safe)
          </h3>
          <p className="text-xs text-[#6A707A] mt-1">
            Probing active production MCP servers requires absolute zero-write guarantees. Try any tool name:
          </p>
        </div>
        <div className="font-mono text-xs text-[#3B5249] flex items-center space-x-1 bg-[#3B5249]/10 px-3 py-1 rounded-full">
          <Check size={12} />
          <span>Max Rate Cap: ≤ 0.20 RPS</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-7 space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-mono font-semibold text-[#2C2E33]">Tool Identifier (Name)</label>
            <input
              type="text"
              value={toolName}
              onChange={(e) => { setToolName(e.target.value); setTested(true); }}
              className="w-full px-4 py-2.5 rounded bg-[#FAF8F5] border border-[#1A1B1E]/20 text-sm font-mono focus:outline-none focus:border-[#C84B31] transition-colors"
              placeholder="e.g. execute_sql_migration"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-mono font-semibold text-[#2C2E33]">Tool Description & Docstring</label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => { setDescription(e.target.value); setTested(true); }}
              className="w-full px-4 py-2 rounded bg-[#FAF8F5] border border-[#1A1B1E]/20 text-sm font-mono focus:outline-none focus:border-[#C84B31] transition-colors resize-none"
              placeholder="e.g. Executes raw query on live database..."
            />
          </div>

          <div className="pt-2">
            <span className="text-[11px] text-[#6A707A] font-mono uppercase block mb-2">Try Real MCP Sample Tools:</span>
            <div className="flex flex-wrap gap-2">
              {sampleTools.map((t) => (
                <button
                  key={t.name}
                  onClick={() => { setToolName(t.name); setDescription(t.desc); setTested(true); }}
                  className="px-2.5 py-1 text-xs font-mono rounded bg-[#EBE5DC]/70 hover:bg-[#1A1B1E] hover:text-[#FDFBF7] transition-all text-[#2C2E33]"
                >
                  {t.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-5 flex flex-col justify-between p-6 rounded-lg border bg-[#1A1B1E] text-[#FDFBF7] font-mono">
          <div>
            <div className="flex items-center justify-between text-xs border-b border-white/10 pb-3">
              <span className="text-[#6A707A]">SAFETY GATE OUTPUT</span>
              <Terminal size={14} className="text-[#E08E45]" />
            </div>

            <div className="mt-6 flex flex-col items-center justify-center py-4 text-center">
              {result.isSafe ? (
                <>
                  <div className="w-12 h-12 rounded-full bg-[#3B5249]/20 flex items-center justify-center text-[#3B5249] mb-3 border border-[#3B5249]/40">
                    <ShieldCheck size={26} />
                  </div>
                  <span className="text-sm font-bold text-[#3B5249] tracking-wider uppercase">PROBE AUTHORIZED</span>
                  <span className="text-[11px] text-white/60 mt-1">Read-Only safe signature verified.</span>
                </>
              ) : (
                <>
                  <div className="w-12 h-12 rounded-full bg-[#C84B31]/20 flex items-center justify-center text-[#C84B31] mb-3 border border-[#C84B31]/40">
                    <ShieldAlert size={26} />
                  </div>
                  <span className="text-sm font-bold text-[#C84B31] tracking-wider uppercase">PROBE BLOCKED</span>
                  <span className="text-[11px] text-[#E08E45] mt-1 font-semibold">
                    Unsafe write token detected: "{result.matchedWord}"
                  </span>
                </>
              )}
            </div>
          </div>

          <div className="border-t border-white/10 pt-4 text-[10px] text-white/60 space-y-1">
            <div className="flex justify-between"><span>SYNTH_STRATEGY:</span> <span>JSON_SCHEMA_MUTATION</span></div>
            <div className="flex justify-between"><span>AMBIGUITY_FALLBACK:</span> <span>REJECT_UNSAFE</span></div>
          </div>
        </div>
      </div>
    </div>
  );
};
