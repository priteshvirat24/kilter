'use client';

import React, { useState } from 'react';
import { ArrowRight, Wrench, CheckCircle2, RefreshCw } from 'lucide-react';

export const PatchDiffPreview: React.FC = () => {
  const [strategy, setStrategy] = useState<'shim' | 'pin'>('shim');

  const unitShiftDiff = `--- a/mcp_server_client/shipping.py
+++ b/mcp_server_client/shipping.py
@@ -42,7 +42,9 @@
     # KILTER AUTOMATED SHIM REMEDIATION (L2 Statistical Excursion)
-    raw_weight = payload.get("weight_value")
+    raw_weight_lbs = payload.get("weight_value")
+    # Normalizing unit shift detected (lbs -> kg, factor: 0.453592)
+    raw_weight = raw_weight_lbs * 0.453592 if raw_weight_lbs else 0.0
     
     return {"shipping_fee_usd": calculate_tariff(raw_weight)}`;

  const pinStubDiff = `--- a/mcp_server_client/config.py
+++ b/mcp_server_client/config.py
@@ -14,6 +14,9 @@
- MCP_PROTOCOL_REVISION = "2026-07-24"
+ # KILTER ARCHITECTURAL PIN (L0 Capability Excursion: tool 'get_rates' removed)
+ MCP_PROTOCOL_REVISION = "2026-06-15"
+ ENABLE_FALLBACK_STUB = True`;

  return (
    <div className="p-8 rounded-xl glass-card border border-[#1A1B1E]/10 max-w-4xl mx-auto space-y-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1A1B1E]/10 pb-6">
        <div>
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-1 bg-[#3B5249]/10 text-[#3B5249] rounded">
            Automated Remediation Engine (engine/remediate/patch.py)
          </span>
          <h3 className="text-xl font-extrabold text-[#1A1B1E] mt-2 tracking-tight">
            Autonomous Shim & Pin Generators
          </h3>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setStrategy('shim')}
            className={`px-3 py-1.5 rounded text-xs font-mono font-semibold uppercase tracking-wider transition-all ${
              strategy === 'shim'
                ? 'bg-[#1A1B1E] text-[#FDFBF7] shadow-sm'
                : 'bg-[#EBE5DC]/60 text-[#2C2E33] hover:bg-[#EBE5DC]'
            }`}
          >
            Shim Strategy (Unit Shift)
          </button>
          <button
            onClick={() => setStrategy('pin')}
            className={`px-3 py-1.5 rounded text-xs font-mono font-semibold uppercase tracking-wider transition-all ${
              strategy === 'pin'
                ? 'bg-[#1A1B1E] text-[#FDFBF7] shadow-sm'
                : 'bg-[#EBE5DC]/60 text-[#2C2E33] hover:bg-[#EBE5DC]'
            }`}
          >
            Pin Strategy (Tool Removal)
          </button>
        </div>
      </div>

      <div className="bg-[#1A1B1E] p-6 rounded-lg overflow-x-auto border border-black text-xs font-mono leading-relaxed text-[#FAF8F5]/90 shadow-inner">
        <div className="flex items-center justify-between text-[11px] text-[#6A707A] pb-3 mb-3 border-b border-white/10">
          <span>TARGET FILE: {strategy === 'shim' ? 'shipping.py (L2 Excursion)' : 'config.py (L0 Breaking Change)'}</span>
          <span className="text-[#3B5249] font-bold">UNIFIED_DIFF_VALID</span>
        </div>
        <pre className="space-y-0.5">
          {(strategy === 'shim' ? unitShiftDiff : pinStubDiff).split('\n').map((line, i) => {
            let colorClass = 'text-white/80';
            if (line.startsWith('+')) colorClass = 'text-[#3B5249] font-bold bg-[#3B5249]/10 block px-1 -mx-1';
            else if (line.startsWith('-')) colorClass = 'text-[#C84B31] font-bold bg-[#C84B31]/10 block px-1 -mx-1';
            else if (line.startsWith('@') || line.startsWith('---') || line.startsWith('+++')) colorClass = 'text-[#E08E45] font-semibold';
            return <div key={i} className={colorClass}>{line}</div>;
          })}
        </pre>
      </div>

      <div className="flex items-center justify-between text-xs font-mono text-[#6A707A] pt-2">
        <div className="flex items-center space-x-2">
          <Wrench size={14} className="text-[#D97706]" />
          <span>Patch verification status: READY_FOR_MERGE</span>
        </div>
        <span>Generated without human developer intervention</span>
      </div>
    </div>
  );
};
