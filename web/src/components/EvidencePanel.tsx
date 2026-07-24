/**
 * EvidencePanel.tsx — Three-column evidence display.
 *
 * BASELINE | CURRENT | TEST columns separated by hairlines.
 * Below: plain_english sentence in Plex Sans at 16px.
 * "The numbers prove it; the sentence sells it."
 */

import type { FC } from 'react'

interface EvidenceSummary {
  sample_count: number
  window?: [string, string]
  summary?: Record<string, unknown>
  examples?: unknown[]
}

interface EvidenceData {
  test: string
  statistic: number | null
  p_value: number | null
  p_value_adjusted: number | null
  field_volatility: number | null
  baseline: EvidenceSummary
  current: EvidenceSummary
  plain_english: string
}

interface EvidencePanelProps {
  evidence: EvidenceData
}

export const EvidencePanel: FC<EvidencePanelProps> = ({ evidence }) => {
  const { baseline, current, test, statistic, p_value, p_value_adjusted, field_volatility, plain_english } = evidence

  return (
    <div style={{ width: '100%' }}>
      {/* Three columns */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1px 1fr 1px 1fr',
          gap: 0,
          borderTop: '1px solid var(--hairline)',
          borderBottom: '1px solid var(--hairline)',
          marginBottom: 'var(--space-6)',
        }}
      >
        {/* BASELINE */}
        <EvidenceColumn title="BASELINE" data={baseline} />

        {/* Hairline divider */}
        <div style={{ background: 'var(--hairline)', width: 1 }} />

        {/* CURRENT */}
        <EvidenceColumn title="CURRENT" data={current} />

        {/* Hairline divider */}
        <div style={{ background: 'var(--hairline)', width: 1 }} />

        {/* TEST */}
        <div style={{ padding: 'var(--space-4)' }}>
          <p className="label" style={{ marginBottom: 'var(--space-3)' }}>TEST</p>
          <Row label="Method" value={test?.replace(/_/g, ' ').toUpperCase() ?? '—'} mono />
          <Row label="Statistic" value={statistic?.toFixed(4) ?? '—'} mono />
          <Row label="p-value" value={p_value?.toFixed(6) ?? '—'} mono />
          <Row label="FDR adj. p" value={p_value_adjusted?.toFixed(6) ?? '—'} mono />
          <Row
            label="Volatility"
            value={field_volatility != null ? field_volatility.toFixed(2) : '—'}
            mono
            highlight={field_volatility != null && field_volatility < 0.1}
          />
        </div>
      </div>

      {/* plain_english — the sentence that sells it */}
      <p
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: 'var(--text-md)',
          lineHeight: 1.7,
          color: 'var(--ink-000)',
          maxWidth: 680,
        }}
      >
        {plain_english}
      </p>
    </div>
  )
}

function EvidenceColumn({ title, data }: { title: string; data: EvidenceSummary }) {
  const summary = data.summary as Record<string, unknown> | undefined
  const examples = data.examples as unknown[] | undefined

  return (
    <div style={{ padding: 'var(--space-4)' }}>
      <p className="label" style={{ marginBottom: 'var(--space-3)' }}>{title}</p>
      <Row label="Samples" value={String(data.sample_count)} mono />
      {data.window && (
        <Row
          label="Window"
          value={`${formatDate(data.window[0])} — ${formatDate(data.window[1])}`}
          mono
        />
      )}
      {summary?.mean != null && (
        <Row label="Mean" value={Number(summary.mean).toFixed(3)} mono />
      )}
      {summary?.std != null && (
        <Row label="Std" value={Number(summary.std).toFixed(3)} mono />
      )}
      {summary?.unit_hint && (
        <Row label="Unit hint" value={String(summary.unit_hint)} mono />
      )}
      {examples && examples.length > 0 && (
        <div style={{ marginTop: 'var(--space-2)' }}>
          <p className="label" style={{ marginBottom: 2 }}>Examples</p>
          {examples.slice(0, 3).map((ex, i) => (
            <p key={i} className="mono" style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-100)' }}>
              {String(ex)}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}

function Row({
  label,
  value,
  mono = false,
  highlight = false,
}: {
  label: string
  value: string
  mono?: boolean
  highlight?: boolean
}) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-1)', gap: 'var(--space-2)' }}>
      <span style={{ color: 'var(--ink-200)', fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)', letterSpacing: '0.04em' }}>
        {label}
      </span>
      <span
        style={{
          fontFamily: mono ? 'var(--font-mono)' : 'var(--font-body)',
          fontSize: 'var(--text-xs)',
          color: highlight ? 'var(--reference)' : 'var(--ink-000)',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {value}
      </span>
    </div>
  )
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch {
    return iso
  }
}
