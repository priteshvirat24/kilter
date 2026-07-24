-- Kilter — Database Schema
-- FROZEN at hour 3. Changes require both engineers to agree and a note in CHANGELOG.md.
-- Apply: psql $DATABASE_URL < db/schema.sql

CREATE EXTENSION IF NOT EXISTS vector;

-- ─────────────────────────────────────────────────────────────
-- Servers under observation
-- ─────────────────────────────────────────────────────────────
CREATE TABLE servers (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                TEXT NOT NULL,
    slug                TEXT NOT NULL UNIQUE,
    endpoint_url        TEXT NOT NULL,
    transport           TEXT NOT NULL DEFAULT 'streamable_http',
    registry_source     TEXT,             -- 'official' | 'pulsemcp' | 'smithery' | 'manual'
    protocol_revision   TEXT,             -- e.g. '2025-11-25', '2026-07-28'
    auth_mode           TEXT NOT NULL DEFAULT 'none',  -- none | bearer | oauth
    probe_enabled       BOOLEAN NOT NULL DEFAULT true,
    opt_out             BOOLEAN NOT NULL DEFAULT false, -- maintainer requested exclusion
    rate_limit_rps      NUMERIC NOT NULL DEFAULT 0.2,
    first_seen_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_probed_at      TIMESTAMPTZ
);

-- ─────────────────────────────────────────────────────────────
-- Capability snapshot: what the server advertised at a moment
-- ─────────────────────────────────────────────────────────────
CREATE TABLE capability_snapshots (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id           UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
    captured_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    protocol_revision   TEXT,
    tools               JSONB NOT NULL,   -- full tools/list payload
    resources           JSONB,
    prompts             JSONB,
    content_hash        TEXT NOT NULL     -- sha256 of canonicalized tools payload
);
CREATE INDEX ON capability_snapshots (server_id, captured_at DESC);
CREATE INDEX ON capability_snapshots (server_id, content_hash);

-- ─────────────────────────────────────────────────────────────
-- A ProbeSet: the fixed inputs we replay. THIS IS THE CONTROL.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE probesets (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id           UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
    tool_name           TEXT NOT NULL,
    arguments           JSONB NOT NULL,   -- frozen forever; changing = new probeset
    generation_method   TEXT NOT NULL,    -- 'schema_synth' | 'recorded_trace' | 'manual'
    is_safe             BOOLEAN NOT NULL DEFAULT true,  -- read-only, no side effects
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (server_id, tool_name, arguments)
);

-- ─────────────────────────────────────────────────────────────
-- One execution of one probeset
-- ─────────────────────────────────────────────────────────────
CREATE TABLE observations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    probeset_id         UUID NOT NULL REFERENCES probesets(id) ON DELETE CASCADE,
    run_id              UUID NOT NULL,    -- groups all observations in one cycle
    observed_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    sample_index        INT NOT NULL,     -- 0..n-1 within this run
    latency_ms          INT,
    is_error            BOOLEAN NOT NULL DEFAULT false,
    error_code          INT,              -- watch for -32002 -> -32602 migration
    error_message       TEXT,
    raw_response        JSONB,
    shape_fingerprint   JSONB,            -- {paths: [...], types: {...}, cardinality: {...}}
    text_embedding      vector(1536)      -- NULL when tool returns no free text
);
CREATE INDEX ON observations (probeset_id, observed_at DESC);
CREATE INDEX ON observations (run_id);
CREATE INDEX ON observations USING hnsw (text_embedding vector_cosine_ops);

-- ─────────────────────────────────────────────────────────────
-- Baseline: the reference state + learned volatility
-- ─────────────────────────────────────────────────────────────
CREATE TABLE baselines (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    probeset_id         UUID NOT NULL REFERENCES probesets(id) ON DELETE CASCADE,
    established_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    sample_count        INT NOT NULL,
    capability_snapshot_id UUID REFERENCES capability_snapshots(id),
    field_stats         JSONB NOT NULL,   -- path -> {type, mean, std, categories, null_rate}
    volatility          JSONB NOT NULL,   -- path -> 0.0..1.0
    centroid            vector(1536),
    centroid_dispersion NUMERIC,
    is_active           BOOLEAN NOT NULL DEFAULT true
);
CREATE INDEX ON baselines (probeset_id) WHERE is_active;

-- ─────────────────────────────────────────────────────────────
-- Detected drift
-- ─────────────────────────────────────────────────────────────
CREATE TYPE drift_severity AS ENUM ('cosmetic', 'behavioral', 'breaking');
CREATE TYPE drift_layer    AS ENUM ('l0_capability','l1_structural','l2_statistical','l3_semantic');

CREATE TABLE drift_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id           UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
    probeset_id         UUID REFERENCES probesets(id) ON DELETE CASCADE,
    baseline_id         UUID REFERENCES baselines(id),
    run_id              UUID NOT NULL,
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    layer               drift_layer NOT NULL,
    severity            drift_severity NOT NULL,
    change_type         TEXT NOT NULL,    -- 'tool_removed','unit_shift','description_changed',...
    field_path          TEXT,             -- 'results[*].weight'
    title               TEXT NOT NULL,    -- human-readable, one line
    evidence            JSONB NOT NULL,   -- see 03-data-model.md for shape
    confidence          NUMERIC,          -- 0..1
    acknowledged        BOOLEAN NOT NULL DEFAULT false
);
CREATE INDEX ON drift_events (server_id, detected_at DESC);
CREATE INDEX ON drift_events (severity, detected_at DESC);

-- ─────────────────────────────────────────────────────────────
-- Generated remediation
-- ─────────────────────────────────────────────────────────────
CREATE TABLE remediations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drift_event_id      UUID NOT NULL REFERENCES drift_events(id) ON DELETE CASCADE,
    strategy            TEXT NOT NULL,    -- 'pin' | 'shim' | 'call_site'
    language            TEXT NOT NULL,    -- 'python' | 'typescript'
    patch_diff          TEXT NOT NULL,    -- unified diff, renders in the UI
    explanation         TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
