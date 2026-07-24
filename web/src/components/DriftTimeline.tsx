/**
 * DriftTimeline.tsx — Full server timeline view.
 * Stacked ToleranceBand components, one per field series.
 */

import type { FC } from 'react'
import { ToleranceBand, type CapabilityMarker, type TimelinePoint } from './ToleranceBand'

export interface FieldSeriesData {
  field_path: string
  dtype: string
  volatility: number
  nominal: number
  tolerance_lower: number
  tolerance_upper: number
  points: TimelinePoint[]
}

interface DriftTimelineProps {
  fieldSeries: FieldSeriesData[]
  capabilityMarkers: CapabilityMarker[]
  onExcursionClick?: (drift_event_id: string) => void
}

export const DriftTimeline: FC<DriftTimelineProps> = ({
  fieldSeries,
  capabilityMarkers,
  onExcursionClick,
}) => {
  if (fieldSeries.length === 0) {
    return (
      <div
        style={{
          padding: 'var(--space-8)',
          textAlign: 'center',
          borderTop: '1px solid var(--hairline)',
        }}
      >
        <p style={{ color: 'var(--ink-200)', fontSize: 'var(--text-sm)' }}>
          No drift data available for this tool yet.
        </p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {fieldSeries.map((series) => (
        <div
          key={series.field_path}
          style={{
            padding: 'var(--space-4)',
            borderTop: '1px solid var(--hairline)',
          }}
        >
          <ToleranceBand
            fieldPath={series.field_path}
            volatility={series.volatility}
            nominal={series.nominal}
            toleranceLower={series.tolerance_lower}
            toleranceUpper={series.tolerance_upper}
            points={series.points}
            capabilityMarkers={capabilityMarkers.filter(
              (m) => new Date(m.at) >= new Date(series.points[0]?.at ?? 0)
            )}
            onExcursionClick={onExcursionClick}
          />
        </div>
      ))}
    </div>
  )
}
