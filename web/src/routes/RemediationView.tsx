/**
 * routes/RemediationView.tsx — Screen 4: /drift/:id/fix
 *
 * Unified diff with syntax highlighting, real line numbers, red/green gutters.
 * Single primary action: Copy patch.
 * NOT "Open PR" — GitHub App not built, and a button that doesn't work
 * is worse than one that isn't there.
 */

import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

function DiffLine({ line, lineNum }: { line: string; lineNum: number }) {
  let bg = 'transparent'
  let color = 'var(--ink-100)'
  let gutterColor = 'var(--ink-200)'
  let prefix = ' '

  if (line.startsWith('+') && !line.startsWith('+++')) {
    bg = 'rgba(79, 184, 201, 0.08)'
    color = 'var(--ink-000)'
    gutterColor = 'var(--reference)'
    prefix = '+'
  } else if (line.startsWith('-') && !line.startsWith('---')) {
    bg = 'rgba(229, 72, 77, 0.08)'
    color = 'var(--breaking)'
    gutterColor = 'var(--breaking)'
    prefix = '-'
  } else if (line.startsWith('@@')) {
    bg = 'rgba(79, 184, 201, 0.05)'
    color = 'var(--reference)'
  } else if (line.startsWith('---') || line.startsWith('+++')) {
    color = 'var(--ink-200)'
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '40px 16px 1fr',
        background: bg,
        minHeight: 20,
        alignItems: 'stretch',
      }}
    >
      {/* Line number */}
      <span
        className="mono"
        style={{
          fontSize: 12,
          color: 'var(--ink-200)',
          paddingLeft: 'var(--space-2)',
          paddingRight: 'var(--space-2)',
          userSelect: 'none',
          borderRight: '1px solid var(--hairline)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-end',
        }}
      >
        {lineNum}
      </span>
      {/* Gutter: +/- indicator */}
      <span
        className="mono"
        style={{
          fontSize: 12,
          color: gutterColor,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          userSelect: 'none',
          fontWeight: 600,
        }}
      >
        {prefix !== ' ' ? prefix : ''}
      </span>
      {/* Content */}
      <span
        className="mono"
        style={{
          fontSize: 12,
          color,
          paddingLeft: 'var(--space-2)',
          paddingRight: 'var(--space-2)',
          whiteSpace: 'pre',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        {line}
      </span>
    </div>
  )
}

export function RemediationView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [copied, setCopied] = useState(false)

  const { data: remediation, isLoading, error } = useQuery({
    queryKey: ['remediation', id],
    queryFn: () => api.getRemediation(id!),
    enabled: !!id,
  })

  const handleCopy = async () => {
    if (!remediation?.patch_diff) return
    try {
      await navigator.clipboard.writeText(remediation.patch_diff)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback: select the text
    }
  }

  if (isLoading) {
    return (
      <div style={{ padding: 'var(--space-8)' }}>
        <div className="skeleton" style={{ width: '40%', height: 24, marginBottom: 'var(--space-6)' }} />
        <div className="skeleton" style={{ width: '100%', height: 400 }} />
      </div>
    )
  }

  if (error || !remediation) {
    return (
      <div style={{ padding: 'var(--space-8)' }}>
        <p style={{ color: 'var(--breaking)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)' }}>
          No remediation available for this event.
        </p>
      </div>
    )
  }

  const lines = remediation.patch_diff.split('\n')

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
          id="btn-back-from-remediation"
          onClick={() => navigate(-1)}
          style={{ background: 'none', border: 'none', color: 'var(--ink-200)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', cursor: 'pointer', padding: 0 }}
        >
          ← Evidence
        </button>

        <span className="label" style={{ marginRight: 'auto' }}>
          {remediation.strategy.toUpperCase()} · {remediation.language}
        </span>

        {/* Single primary action: Copy patch */}
        <button
          id="btn-copy-patch"
          onClick={handleCopy}
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 'var(--text-xs)',
            fontWeight: 500,
            color: copied ? 'var(--in-spec)' : 'var(--reference)',
            background: copied ? 'rgba(122, 136, 152, 0.1)' : 'rgba(79, 184, 201, 0.1)',
            border: `1px solid ${copied ? 'var(--in-spec)' : 'rgba(79, 184, 201, 0.3)'}`,
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-2) var(--space-4)',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)',
          }}
        >
          {copied ? 'Patch copied' : 'Copy patch'}
        </button>
      </div>

      {/* Explanation */}
      <div
        style={{
          padding: 'var(--space-4) var(--space-6)',
          borderBottom: '1px solid var(--hairline)',
          background: 'var(--ground-100)',
        }}
      >
        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--ink-100)', lineHeight: 1.6 }}>
          {remediation.explanation}
        </p>
        {remediation.confidence != null && (
          <p className="label" style={{ marginTop: 'var(--space-2)' }}>
            Confidence: {(remediation.confidence * 100).toFixed(0)}%
          </p>
        )}
      </div>

      {/* Diff */}
      <div
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 12,
          background: 'var(--ground-100)',
          borderTop: '1px solid var(--hairline)',
          overflow: 'auto',
        }}
        aria-label="Unified diff patch"
      >
        {lines.map((line, i) => (
          <DiffLine key={i} line={line} lineNum={i + 1} />
        ))}
      </div>
    </div>
  )
}
