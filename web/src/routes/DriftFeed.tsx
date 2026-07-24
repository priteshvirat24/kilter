/**
 * routes/DriftFeed.tsx — Screen 1: / — Drift feed.
 *
 * Full-bleed list, one row per event.
 * Each row: severity chip, server name, title, field_path in mono,
 * relative time, 12px-tall inline sparkline tolerance band.
 *
 * Top strip: 4 numbers — servers / probe runs / behavioral 7d / breaking 7d.
 */

import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { api, type DriftEvent } from '../api/client'
import { SeverityBadge } from '../components/SeverityBadge'
import { ToleranceBand } from '../components/ToleranceBand'

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

function StatNumber({ value, label }: { value: number | string; label: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <span
        className="mono"
        style={{ fontSize: 'var(--text-2xl)', color: 'var(--ink-000)', fontVariantNumeric: 'tabular-nums' }}
      >
        {value}
      </span>
      <span className="label">{label}</span>
    </div>
  )
}

function DriftRow({ event }: { event: DriftEvent }) {
  const navigate = useNavigate()
  return (
    <div
      id={`drift-event-${event.id}`}
      role="row"
      onClick={() => navigate(`/drift/${event.id}`)}
      style={{
        display: 'grid',
        gridTemplateColumns: '90px 1fr auto auto',
        alignItems: 'center',
        gap: 'var(--space-4)',
        padding: 'var(--space-3) var(--space-6)',
        borderBottom: '1px solid var(--hairline)',
        cursor: 'pointer',
        transition: 'background var(--transition-fast)',
      }}
      onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.background = 'var(--ground-100)' }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLDivElement).style.background = 'transparent' }}
    >
      {/* Severity */}
      <SeverityBadge severity={event.severity} />

      {/* Content */}
      <div style={{ overflow: 'hidden' }}>
        <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'baseline', marginBottom: 2 }}>
          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--ink-000)', fontWeight: 500 }}>
            {event.server.name}
          </span>
          <span style={{ color: 'var(--ink-200)', fontSize: 'var(--text-xs)' }}>·</span>
          <span
            className="mono"
            style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-100)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 200 }}
          >
            {event.field_path ?? event.change_type}
          </span>
        </div>
        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--ink-100)', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {event.title}
        </p>
      </div>

      {/* Sparkline placeholder — 12px tall inline band */}
      <div style={{ width: 80, height: 12, flexShrink: 0 }}>
        {/* Rendered as a minimal SVG sparkline */}
        <svg width={80} height={12}>
          <rect x={0} y={3} width={80} height={6} fill="var(--tolerance)" fillOpacity={0.4} rx={1} />
          <line x1={0} y1={6} x2={80} y2={6} stroke="var(--reference)" strokeWidth={0.5} />
          <circle cx={72} cy={2} r={3} fill={event.severity === 'breaking' ? 'var(--breaking)' : 'var(--behavioral)'} />
        </svg>
      </div>

      {/* Relative time */}
      <span
        className="mono"
        style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-200)', whiteSpace: 'nowrap', flexShrink: 0 }}
      >
        {relativeTime(event.detected_at)}
      </span>
    </div>
  )
}

function SkeletonRow() {
  return (
    <div style={{ padding: 'var(--space-3) var(--space-6)', borderBottom: '1px solid var(--hairline)', display: 'flex', gap: 'var(--space-4)', alignItems: 'center' }}>
      <div className="skeleton" style={{ width: 72, height: 20 }} />
      <div style={{ flex: 1 }}>
        <div className="skeleton" style={{ width: '40%', height: 14, marginBottom: 6 }} />
        <div className="skeleton" style={{ width: '70%', height: 14 }} />
      </div>
      <div className="skeleton" style={{ width: 80, height: 12 }} />
      <div className="skeleton" style={{ width: 48, height: 14 }} />
    </div>
  )
}

export function DriftFeed() {
  const { data: driftData, isLoading: driftLoading } = useQuery({
    queryKey: ['drift'],
    queryFn: () => api.getDrift(),
    refetchInterval: 30000,
  })
  const { data: statsData } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.getStats(),
    refetchInterval: 30000,
  })

  return (
    <div style={{ minHeight: '100vh', background: 'var(--ground-000)' }}>
      {/* Top strip — 4 numbers */}
      <div
        style={{
          padding: 'var(--space-6) var(--space-6) var(--space-5)',
          borderBottom: '1px solid var(--hairline)',
          display: 'flex',
          gap: 'var(--space-10)',
          alignItems: 'flex-end',
        }}
      >
        <div style={{ marginRight: 'auto' }}>
          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'var(--text-xl)',
              fontWeight: 600,
              letterSpacing: '-0.01em',
              color: 'var(--ink-000)',
              marginBottom: 2,
            }}
          >
            Kilter
          </h1>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-200)', fontFamily: 'var(--font-mono)' }}>
            Active MCP drift detection
          </p>
        </div>
        <StatNumber value={statsData?.servers_monitored ?? '—'} label="Servers monitored" />
        <StatNumber value={statsData?.probe_runs_total ?? '—'} label="Probe runs" />
        <StatNumber value={statsData?.drift_events.behavioral ?? '—'} label="Behavioral 7d" />
        <StatNumber value={statsData?.drift_events.breaking ?? '—'} label="Breaking 7d" />
      </div>

      {/* Event feed */}
      <div role="table" aria-label="Drift event feed">
        {driftLoading
          ? Array.from({ length: 8 }, (_, i) => <SkeletonRow key={i} />)
          : driftData?.events.length === 0
          ? (
            <div style={{ padding: 'var(--space-12)', textAlign: 'center' }}>
              <p style={{ color: 'var(--ink-200)', fontSize: 'var(--text-sm)' }}>
                No drift detected in the last 7 days. Baseline established from recent probe runs.
              </p>
            </div>
          )
          : driftData?.events.map((event) => (
            <DriftRow key={event.id} event={event} />
          ))
        }
      </div>
    </div>
  )
}
