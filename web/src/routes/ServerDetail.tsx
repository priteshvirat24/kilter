/**
 * routes/ServerDetail.tsx — Screen 2: /servers/:id
 *
 * Tool list on the left (mono, with per-tool volatility as a 4-bar micro-histogram).
 * Selected tool's field series on the right as stacked <ToleranceBand />.
 * Protocol revision badge in the header.
 */

import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api, type ToolSummary } from '../api/client'
import { DriftTimeline } from '../components/DriftTimeline'
import { SeverityBadge } from '../components/SeverityBadge'

function VolatilityHistogram({ value }: { value: number }) {
  // 4-bar micro-histogram representing volatility 0→1
  const bars = [0.25, 0.5, 0.75, 1.0]
  return (
    <svg width={20} height={12} aria-label={`Volatility ${value.toFixed(2)}`}>
      {bars.map((threshold, i) => (
        <rect
          key={i}
          x={i * 5}
          y={12 - (value >= threshold ? 10 : 3)}
          width={4}
          height={value >= threshold ? 10 : 3}
          fill={value >= threshold ? 'var(--in-spec)' : 'var(--ground-200)'}
        />
      ))}
    </svg>
  )
}

function DetectionPowerBadge({ power }: { power: 'high' | 'medium' | 'low' }) {
  const colors = { high: 'var(--reference)', medium: 'var(--behavioral)', low: 'var(--ink-200)' }
  return (
    <span
      className="label"
      style={{ color: colors[power], fontSize: '10px' }}
    >
      {power}
    </span>
  )
}

export function ServerDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [selectedTool, setSelectedTool] = useState<string | null>(null)

  const { data: server, isLoading: serverLoading, error: serverError } = useQuery({
    queryKey: ['server', id],
    queryFn: () => api.getServer(id!),
    enabled: !!id,
    refetchInterval: 30000,
  })

  const activeTool = selectedTool ?? server?.tools[0]?.name ?? null

  const { data: timeline, isLoading: timelineLoading } = useQuery({
    queryKey: ['timeline', id, activeTool],
    queryFn: () => api.getTimeline(id!, activeTool ?? undefined),
    enabled: !!id && !!activeTool,
    refetchInterval: 30000,
  })

  if (serverError) {
    return (
      <div style={{ padding: 'var(--space-8)', color: 'var(--breaking)' }}>
        <p className="mono" style={{ fontSize: 'var(--text-sm)' }}>
          This server didn't respond. It may be down or rate-limiting us. Retry in 60s.
        </p>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--ground-000)' }}>
      {/* Header */}
      <div
        style={{
          padding: 'var(--space-5) var(--space-6)',
          borderBottom: '1px solid var(--hairline)',
          display: 'flex',
          alignItems: 'baseline',
          gap: 'var(--space-4)',
        }}
      >
        <button
          id="btn-back-to-feed"
          onClick={() => navigate('/')}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--ink-200)',
            fontFamily: 'var(--font-mono)',
            fontSize: 'var(--text-xs)',
            cursor: 'pointer',
            padding: 0,
          }}
        >
          ← Feed
        </button>

        {serverLoading ? (
          <div className="skeleton" style={{ width: 200, height: 24 }} />
        ) : (
          <>
            <h1
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 'var(--text-lg)',
                fontWeight: 600,
                color: 'var(--ink-000)',
              }}
            >
              {server?.name}
            </h1>
            {server?.protocol_revision && (
              <span
                className="mono"
                style={{
                  fontSize: 'var(--text-xs)',
                  color: 'var(--reference)',
                  background: 'rgba(79, 184, 201, 0.1)',
                  padding: '2px var(--space-2)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid rgba(79, 184, 201, 0.2)',
                }}
              >
                {server.protocol_revision}
              </span>
            )}
            {server?.baseline_established_at && (
              <span className="label">
                Baseline: {new Date(server.baseline_established_at).toLocaleDateString()}
              </span>
            )}
          </>
        )}
      </div>

      {/* Two-column layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', minHeight: 'calc(100vh - 64px)' }}>
        {/* Tool list — left */}
        <div style={{ borderRight: '1px solid var(--hairline)', padding: 'var(--space-4) 0' }}>
          <p className="label" style={{ padding: '0 var(--space-4)', marginBottom: 'var(--space-3)' }}>
            Tools
          </p>

          {serverLoading
            ? Array.from({ length: 4 }, (_, i) => (
                <div key={i} style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--hairline)' }}>
                  <div className="skeleton" style={{ width: '70%', height: 13 }} />
                </div>
              ))
            : server?.tools.map((tool) => (
                <ToolRow
                  key={tool.name}
                  tool={tool}
                  isSelected={activeTool === tool.name}
                  onClick={() => setSelectedTool(tool.name)}
                />
              ))
          }
        </div>

        {/* Timeline — right */}
        <div style={{ padding: 'var(--space-5) var(--space-6)' }}>
          {activeTool && (
            <p className="label" style={{ marginBottom: 'var(--space-4)' }}>
              {activeTool}
            </p>
          )}

          {timelineLoading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {[120, 96, 96].map((h, i) => (
                <div key={i} className="skeleton" style={{ height: h }} />
              ))}
            </div>
          ) : (
            <DriftTimeline
              fieldSeries={timeline?.field_series ?? []}
              capabilityMarkers={timeline?.capability_markers ?? []}
              onExcursionClick={(id) => navigate(`/drift/${id}`)}
            />
          )}
        </div>
      </div>
    </div>
  )
}

function ToolRow({
  tool,
  isSelected,
  onClick,
}: {
  tool: ToolSummary
  isSelected: boolean
  onClick: () => void
}) {
  return (
    <button
      id={`tool-${tool.name}`}
      onClick={onClick}
      style={{
        display: 'flex',
        width: '100%',
        alignItems: 'center',
        gap: 'var(--space-3)',
        padding: 'var(--space-3) var(--space-4)',
        borderBottom: '1px solid var(--hairline)',
        background: isSelected ? 'var(--ground-100)' : 'transparent',
        border: 'none',
        borderLeft: isSelected ? `2px solid var(--reference)` : '2px solid transparent',
        borderBottom: '1px solid var(--hairline)',
        cursor: 'pointer',
        textAlign: 'left',
        transition: 'background var(--transition-fast)',
      }}
    >
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <p
          className="mono"
          style={{
            fontSize: 'var(--text-xs)',
            color: isSelected ? 'var(--ink-000)' : 'var(--ink-100)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {tool.name}
        </p>
        {tool.last_drift && (
          <div style={{ marginTop: 2 }}>
            <SeverityBadge severity={tool.last_drift.severity as 'breaking' | 'behavioral' | 'cosmetic'} />
          </div>
        )}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2 }}>
        <VolatilityHistogram value={tool.volatility_mean} />
        <DetectionPowerBadge power={tool.detection_power} />
      </div>
    </button>
  )
}
