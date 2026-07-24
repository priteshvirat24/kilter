/**
 * web/src/api/client.ts — Typed fetch layer.
 *
 * All API calls go through here. Returns typed responses.
 * TanStack Query is used at the route level for caching + loading states.
 *
 * Polling: 30s interval (per spec — real-time/WebSockets explicitly cut).
 */

const BASE = '/api'

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const err = body?.error ?? { code: 'fetch_error', message: res.statusText }
    throw new Error(err.message ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

// ── Types (inlined until openapi-typescript generates them) ─────────────────

export interface DriftCounts { cosmetic: number; behavioral: number; breaking: number }

export interface ServerSummary {
  id: string
  name: string
  slug: string
  protocol_revision: string | null
  tool_count: number
  last_probed_at: string | null
  health: 'stable' | 'drifting' | 'breaking' | 'unreachable'
  drift_counts: DriftCounts
  detection_power: 'high' | 'medium' | 'low'
}

export interface ServersResponse { servers: ServerSummary[]; total: number }

export interface ToolSummary {
  name: string
  probeset_count: number
  volatility_mean: number
  detection_power: 'high' | 'medium' | 'low'
  last_drift: { severity: string; detected_at: string } | null
}

export interface ServerDetail {
  id: string
  name: string
  endpoint_url: string
  protocol_revision: string | null
  baseline_established_at: string | null
  tools: ToolSummary[]
}

export interface TimelinePoint {
  run_id: string
  at: string
  value: number
  in_tolerance: boolean
  drift_event_id: string | null
}

export interface FieldSeries {
  field_path: string
  dtype: string
  volatility: number
  nominal: number
  tolerance_lower: number
  tolerance_upper: number
  points: TimelinePoint[]
}

export interface CapabilityMarker {
  at: string
  kind: string
  severity: 'cosmetic' | 'behavioral' | 'breaking'
  drift_event_id: string
}

export interface TimelineResponse {
  server_id: string
  tool_name: string
  field_series: FieldSeries[]
  capability_markers: CapabilityMarker[]
}

export interface DriftEvent {
  id: string
  server: { id: string; name: string; slug: string }
  detected_at: string
  layer: string
  severity: 'cosmetic' | 'behavioral' | 'breaking'
  change_type: string
  field_path: string | null
  title: string
  confidence: number | null
  has_remediation: boolean
  acknowledged: boolean
}

export interface DriftFeedResponse { events: DriftEvent[]; next_cursor: string | null }

export interface EvidenceResponse {
  drift_event_id: string
  server: { id: string; name: string; slug: string }
  detected_at: string
  layer: string
  severity: string
  change_type: string
  field_path: string | null
  title: string
  confidence: number | null
  evidence: Record<string, unknown>
}

export interface RemediationResponse {
  drift_event_id: string
  strategy: string
  language: string
  explanation: string
  patch_diff: string
  confidence: number | null
}

export interface StatsResponse {
  servers_monitored: number
  probe_runs_total: number
  drift_events: DriftCounts
  servers_with_breaking_drift_7d: number
  last_run_at: string | null
}

// ── API functions ────────────────────────────────────────────────────────────

export const api = {
  getServers: () => apiFetch<ServersResponse>('/servers'),
  getServer: (id: string) => apiFetch<ServerDetail>(`/servers/${id}`),
  getTimeline: (id: string, tool?: string, window?: string) =>
    apiFetch<TimelineResponse>(
      `/servers/${id}/timeline${tool ? `?tool=${encodeURIComponent(tool)}` : ''}${window ? `&window=${window}` : ''}`
    ),
  getDrift: (params?: { severity?: string; server_id?: string; since?: string; cursor?: string }) => {
    const qs = new URLSearchParams()
    if (params?.severity) qs.set('severity', params.severity)
    if (params?.server_id) qs.set('server_id', params.server_id)
    if (params?.since) qs.set('since', params.since)
    if (params?.cursor) qs.set('cursor', params.cursor)
    const query = qs.toString()
    return apiFetch<DriftFeedResponse>(`/drift${query ? `?${query}` : ''}`)
  },
  getEvidence: (id: string) => apiFetch<EvidenceResponse>(`/drift/${id}/evidence`),
  getRemediation: (id: string) => apiFetch<RemediationResponse>(`/drift/${id}/remediation`),
  triggerProbe: (id: string) => apiFetch(`/servers/${id}/probe`, { method: 'POST' }),
  getStats: () => apiFetch<StatsResponse>('/stats'),
}
