/**
 * ToleranceBand.tsx — THE signature component.
 *
 * Renders a time-series with a nominal baseline line, a tolerance envelope,
 * in-spec measurements (grey dots), and excursions (diamonds in amber/red).
 * Capability markers (schema/description changes) appear as vertical ticks.
 *
 * Implementation: raw SVG + d3-scale only. NOT Recharts.
 * One animation: draw left-to-right over ~600ms on mount.
 * Respects prefers-reduced-motion.
 *
 * ~150 lines of SVG logic.
 */

import { useEffect, useRef, useState } from 'react'
import { scaleLinear, scaleTime } from 'd3-scale'

export interface TimelinePoint {
  run_id: string
  at: string           // ISO 8601
  value: number
  in_tolerance: boolean
  drift_event_id: string | null
}

export interface CapabilityMarker {
  at: string           // ISO 8601
  kind: string
  severity: 'cosmetic' | 'behavioral' | 'breaking'
  drift_event_id: string
}

export interface ToleranceBandProps {
  fieldPath: string
  volatility: number
  nominal: number
  toleranceLower: number
  toleranceUpper: number
  points: TimelinePoint[]
  capabilityMarkers?: CapabilityMarker[]
  height?: number
  onExcursionClick?: (drift_event_id: string) => void
}

const SEVERITY_COLOR: Record<string, string> = {
  breaking:   'var(--breaking)',
  behavioral: 'var(--behavioral)',
  cosmetic:   'var(--cosmetic)',
}

function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function ToleranceBand({
  fieldPath,
  volatility,
  nominal,
  toleranceLower,
  toleranceUpper,
  points,
  capabilityMarkers = [],
  height = 96,
  onExcursionClick,
}: ToleranceBandProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(600)
  const [drawProgress, setDrawProgress] = useState(prefersReducedMotion() ? 1 : 0)

  const PADDING = { top: 12, right: 16, bottom: 24, left: 8 }
  const innerW = width - PADDING.left - PADDING.right
  const innerH = height - PADDING.top - PADDING.bottom

  // Measure container width
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setWidth(entry.contentRect.width)
      }
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  // Draw animation — left to right over 600ms
  useEffect(() => {
    if (prefersReducedMotion() || points.length === 0) {
      setDrawProgress(1)
      return
    }
    setDrawProgress(0)
    const start = performance.now()
    const DURATION = 600

    const animate = (now: number) => {
      const progress = Math.min((now - start) / DURATION, 1)
      setDrawProgress(progress)
      if (progress < 1) requestAnimationFrame(animate)
    }
    const raf = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(raf)
  }, [points.length])

  if (points.length === 0) {
    return (
      <div ref={containerRef} style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span className="label" style={{ color: 'var(--ink-200)' }}>No data</span>
      </div>
    )
  }

  // Scales
  const times = points.map((p) => new Date(p.at).getTime())
  const allMarkerTimes = capabilityMarkers.map((m) => new Date(m.at).getTime())
  const allTimes = [...times, ...allMarkerTimes]
  const minT = Math.min(...allTimes)
  const maxT = Math.max(...allTimes)

  const yMin = Math.min(toleranceLower, ...points.map((p) => p.value)) * 0.92
  const yMax = Math.max(toleranceUpper, ...points.map((p) => p.value)) * 1.08

  const xScale = scaleLinear().domain([minT, maxT]).range([0, innerW])
  const yScale = scaleLinear().domain([yMin, yMax]).range([innerH, 0])

  // Clip draw progress to the x axis
  const visibleMaxX = drawProgress * innerW
  const visiblePoints = points.filter(
    (p) => xScale(new Date(p.at).getTime()) <= visibleMaxX
  )

  // Tolerance envelope path
  const envPath = [
    `M ${xScale(minT).toFixed(1)},${yScale(toleranceUpper).toFixed(1)}`,
    `L ${xScale(maxT).toFixed(1)},${yScale(toleranceUpper).toFixed(1)}`,
    `L ${xScale(maxT).toFixed(1)},${yScale(toleranceLower).toFixed(1)}`,
    `L ${xScale(minT).toFixed(1)},${yScale(toleranceLower).toFixed(1)}`,
    'Z',
  ].join(' ')

  // Nominal line (full width, always visible)
  const nominalY = yScale(nominal).toFixed(1)

  // Measurement points line path
  const linePath = visiblePoints.length > 1
    ? visiblePoints.map((p, i) => {
        const x = xScale(new Date(p.at).getTime()).toFixed(1)
        const y = yScale(p.value).toFixed(1)
        return `${i === 0 ? 'M' : 'L'} ${x},${y}`
      }).join(' ')
    : ''

  // Label dates
  const firstDate = new Date(minT).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  const lastDate = new Date(maxT).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })

  return (
    <div ref={containerRef} style={{ width: '100%' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 'var(--space-1)' }}>
        <span
          className="mono"
          style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-100)', letterSpacing: '0.02em' }}
        >
          {fieldPath}
        </span>
        <span className="label" style={{ fontSize: '10px' }}>
          VOLATILITY {volatility.toFixed(2)}&nbsp;
          {'▁'.repeat(Math.max(1, Math.round(volatility * 4)))}
        </span>
      </div>

      <svg
        ref={svgRef}
        width={width}
        height={height}
        role="img"
        aria-label={`Tolerance band chart for ${fieldPath}`}
      >
        <g transform={`translate(${PADDING.left},${PADDING.top})`}>
          {/* Tolerance envelope — 40% opacity fill */}
          <path
            d={envPath}
            fill="var(--tolerance)"
            fillOpacity={0.4}
            stroke="none"
          />

          {/* Nominal line — 1px reference cyan */}
          <line
            x1={0} y1={nominalY}
            x2={innerW} y2={nominalY}
            stroke="var(--reference)"
            strokeWidth={1}
          />

          {/* Capability markers — vertical ticks */}
          {capabilityMarkers.map((m) => {
            const mx = xScale(new Date(m.at).getTime())
            if (mx > visibleMaxX) return null
            const color = SEVERITY_COLOR[m.severity] ?? 'var(--ink-200)'
            return (
              <line
                key={m.drift_event_id}
                x1={mx} y1={0}
                x2={mx} y2={innerH}
                stroke={color}
                strokeWidth={1}
                strokeDasharray="3 2"
                opacity={0.6}
              />
            )
          })}

          {/* Measurement line */}
          {linePath && (
            <path
              d={linePath}
              fill="none"
              stroke="var(--in-spec)"
              strokeWidth={1}
              opacity={0.5}
            />
          )}

          {/* Measurement dots and excursion diamonds */}
          {visiblePoints.map((p, i) => {
            const px = xScale(new Date(p.at).getTime())
            const py = yScale(p.value)
            const isExcursion = !p.in_tolerance

            if (isExcursion) {
              // Diamond shape for excursions
              const size = 5
              const diamondPath = `M ${px},${py - size} L ${px + size},${py} L ${px},${py + size} L ${px - size},${py} Z`
              // Color from severity — we approximate from the drift event presence
              const excursionColor = p.drift_event_id ? 'var(--breaking)' : 'var(--behavioral)'
              return (
                <g key={p.run_id}>
                  <path
                    d={diamondPath}
                    fill={excursionColor}
                    style={{ cursor: p.drift_event_id ? 'pointer' : 'default' }}
                    onClick={() => p.drift_event_id && onExcursionClick?.(p.drift_event_id)}
                  />
                </g>
              )
            }

            return (
              <circle
                key={p.run_id}
                cx={px}
                cy={py}
                r={3}
                fill="var(--in-spec)"
                opacity={0.8}
              />
            )
          })}

          {/* Axis labels */}
          <text
            x={0} y={innerH + 16}
            fill="var(--ink-200)"
            fontFamily="var(--font-mono)"
            fontSize={10}
          >
            {firstDate}
          </text>
          <text
            x={innerW} y={innerH + 16}
            fill="var(--ink-200)"
            fontFamily="var(--font-mono)"
            fontSize={10}
            textAnchor="end"
          >
            {lastDate}
          </text>
        </g>
      </svg>
    </div>
  )
}
