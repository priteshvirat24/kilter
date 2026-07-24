/**
 * routes/EvidenceView.tsx — Screen 3: /drift/:id
 *
 * "The prove it screen and the emotional center of the demo."
 *
 * Top: full-width <ToleranceBand /> at maximum zoom, scrubbed to the excursion.
 * Below: three-column BASELINE | CURRENT | TEST.
 * Below: plain_english sentence in Plex Sans at 16px.
 * Below: link to remediation if has_remediation.
 */

import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { SeverityBadge } from '../components/SeverityBadge'
import { EvidencePanel } from '../components/EvidencePanel'
import { ToleranceBand } from '../components/ToleranceBand'

export function EvidenceView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: evidence, isLoading, error } = useQuery({
    queryKey: ['evidence', id],
    queryFn: () => api.getEvidence(id!),
    enabled: !!id,
  })

  const { data: remediation } = useQuery({
    queryKey: ['remediation', id],
    queryFn: () => api.getRemediation(id!),
    enabled: !!id,
    retry: false,  // Don't retry — not all events have remediations
  })

  if (isLoading) {
    return (
      <div style={{ padding: 'var(--space-8)' }}>
        <div className="skeleton" style={{ width: '40%', height: 24, marginBottom: 'var(--space-6)' }} />
        <div className="skeleton" style={{ width: '100%', height: 120, marginBottom: 'var(--space-6)' }} />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1px 1fr 1px 1fr', gap: 0 }}>
          {[1, 2, 3].map(i => (
            <div key={i} style={{ padding: 'var(--space-4)' }}>
              <div className="skeleton" style={{ width: '60%', height: 12, marginBottom: 'var(--space-3)' }} />
              {[1,2,3,4].map(j => <div key={j} className="skeleton" style={{ height: 12, marginBottom: 6 }} />)}
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error || !evidence) {
    return (
      <div style={{ padding: 'var(--space-8)' }}>
        <p style={{ color: 'var(--breaking)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)' }}>
          Drift event not found. It may have been deleted.
        </p>
      </div>
    )
  }

  const ev = evidence.evidence as Record<string, unknown>
  const hasTimeline = ev.baseline && (ev.baseline as Record<string, unknown>).examples

  // Build a minimal timeline from the evidence examples for the ToleranceBand
  const baselineExamples = ((ev.baseline as Record<string, unknown>)?.examples as number[] | undefined) ?? []
  const currentExamples = ((ev.current as Record<string, unknown>)?.examples as number[] | undefined) ?? []
  const baselineMean = ((ev.baseline as Record<string, unknown>)?.summary as Record<string,number> | undefined)?.mean
  const currentMean = ((ev.current as Record<string, unknown>)?.summary as Record<string,number> | undefined)?.mean

  const allValues = [...baselineExamples, ...currentExamples]
  const minVal = Math.min(...allValues, baselineMean ?? Infinity, currentMean ?? Infinity)
  const maxVal = Math.max(...allValues, baselineMean ?? -Infinity, currentMean ?? -Infinity)
  const nominal = baselineMean ?? minVal
  const tolerance = Math.abs(nominal) * 0.15 || 1
  const volatility = (ev.field_volatility as number | null) ?? 0.1

  // Synthesize timeline points from evidence examples
  const baseNow = Date.now() - 7 * 24 * 60 * 60 * 1000
  const timelinePoints = [
    ...baselineExamples.map((v, i) => ({
      run_id: `base-${i}`,
      at: new Date(baseNow + i * 24 * 60 * 60 * 1000).toISOString(),
      value: v,
      in_tolerance: true,
      drift_event_id: null,
    })),
    ...currentExamples.map((v, i) => ({
      run_id: `curr-${i}`,
      at: new Date(Date.now() - (currentExamples.length - i - 1) * 3600000).toISOString(),
      value: v,
      in_tolerance: false,
      drift_event_id: id ?? null,
    })),
  ]

  return (
    <div style={{ minHeight: '100vh', background: 'var(--ground-000)' }}>
      {/* Header */}
      <div
        style={{
          padding: 'var(--space-5) var(--space-6)',
          borderBottom: '1px solid var(--hairline)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-4)',
        }}
      >
        <button
          id="btn-back-from-evidence"
          onClick={() => navigate(-1)}
          style={{ background: 'none', border: 'none', color: 'var(--ink-200)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', cursor: 'pointer', padding: 0 }}
        >
          ←
        </button>
        <SeverityBadge severity={evidence.severity as 'breaking' | 'behavioral' | 'cosmetic'} size="md" />
        <h1
          style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-lg)', fontWeight: 600, color: 'var(--ink-000)', flex: 1 }}
        >
          {evidence.title}
        </h1>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-200)' }}>
          {evidence.server.name}
        </span>
      </div>

      <div style={{ padding: 'var(--space-6)' }}>
        {/* Field path */}
        {evidence.field_path && (
          <p
            className="mono"
            style={{ fontSize: 'var(--text-sm)', color: 'var(--ink-100)', marginBottom: 'var(--space-5)' }}
          >
            {evidence.field_path}
          </p>
        )}

        {/* Full-width tolerance band at maximum zoom */}
        {timelinePoints.length > 0 && (
          <div style={{ marginBottom: 'var(--space-6)', padding: 'var(--space-4)', background: 'var(--ground-100)', borderRadius: 'var(--radius-md)' }}>
            <ToleranceBand
              fieldPath={evidence.field_path ?? evidence.change_type}
              volatility={volatility}
              nominal={nominal}
              toleranceLower={nominal - tolerance}
              toleranceUpper={nominal + tolerance}
              points={timelinePoints}
              height={140}
            />
          </div>
        )}

        {/* Three-column evidence panel */}
        <EvidencePanel
          evidence={{
            test: (ev.test as string) ?? evidence.change_type,
            statistic: (ev.statistic as number | null) ?? null,
            p_value: (ev.p_value as number | null) ?? null,
            p_value_adjusted: (ev.p_value_adjusted as number | null) ?? null,
            field_volatility: (ev.field_volatility as number | null) ?? null,
            baseline: ev.baseline as { sample_count: number; window?: [string, string]; summary?: Record<string, unknown>; examples?: unknown[] },
            current: ev.current as { sample_count: number; window?: [string, string]; summary?: Record<string, unknown>; examples?: unknown[] },
            plain_english: (ev.plain_english as string) ?? '',
          }}
        />

        {/* Remediation link */}
        {remediation && (
          <div style={{ marginTop: 'var(--space-6)', paddingTop: 'var(--space-5)', borderTop: '1px solid var(--hairline)' }}>
            <Link
              id="btn-view-remediation"
              to={`/drift/${id}/fix`}
              style={{
                display: 'inline-block',
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--text-sm)',
                color: 'var(--reference)',
                textDecoration: 'none',
                padding: 'var(--space-2) var(--space-4)',
                border: '1px solid rgba(79, 184, 201, 0.3)',
                borderRadius: 'var(--radius-md)',
              }}
            >
              View patch →
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
