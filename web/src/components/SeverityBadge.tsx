/**
 * SeverityBadge.tsx — Severity chip component.
 * Renders a small mono-uppercase label with appropriate color.
 */

import type { FC } from 'react'

type Severity = 'cosmetic' | 'behavioral' | 'breaking'

interface SeverityBadgeProps {
  severity: Severity
  size?: 'sm' | 'md'
}

export const SeverityBadge: FC<SeverityBadgeProps> = ({ severity, size = 'sm' }) => {
  return (
    <span
      className={`chip chip--${severity}`}
      style={{ fontSize: size === 'md' ? 'var(--text-sm)' : 'var(--text-xs)' }}
    >
      {severity}
    </span>
  )
}
