# Kilter

**Active MCP server drift detection.**

Kilter holds inputs fixed, replays them against MCP servers on a schedule, and uses statistical two-sample testing to detect when server behavior changes — before your agents fail silently.

> *"Out of kilter" — out of true alignment.*

---

## Why this exists

Passive observability tells you what happened to your users. Kilter tells you what changed on the server.

When a third-party MCP server changes its behavior — rewrites a tool description, shifts a unit from kg to lbs, drops a field — every agent consuming it silently does the wrong thing. The call still returns 200. The JSON still validates. No alert fires.

Kilter detects this by replaying fixed probe inputs and running statistical hypothesis tests over the output distributions. The only free variable is the server: if the output distribution shifts, the server moved.

**The July 28, 2026 MCP spec revision** makes this urgent: sessions removed, initialize handshake removed, three core features deprecated, authorization rewritten, and tool schemas lifted to JSON Schema 2020-12. Every MCP server on earth migrates at the same time, through breaking changes, on a known date.

---

## The drift detection layers

| Layer | What it detects | Cost |
|-------|-----------------|------|
| **L0 Capability** | Tool added/removed/renamed, schema changed, description changed | Free, deterministic |
| **L1 Structural** | New/removed fields, type shifts, null-rate changes, cardinality changes | Free, deterministic |
| **L2 Statistical** | Distribution shifts (KS, G-test, RBO, PSI), unit changes | N probe samples |
| **L3 Semantic** | Meaning drift in text (pgvector embeddings) | 1 embedding call/sample |
| **L4 Task impact** | Agent outcome changes (roadmap, not built) | — |

Severity: **BREAKING** → **BEHAVIORAL** → **COSMETIC**. Cosmetic drift is always silent — alert fatigue is the failure mode that kills monitoring products.

---

## The tool-description insight

A tool's description is not documentation. It is prompt content.

The MCP client serializes tool names, descriptions, and parameter descriptions directly into the model's context. A maintainer who rewrites `"Search for a customer"` → `"Search for a customer. Prefer exact matches; use fuzzy only when explicitly asked."` has changed agent behavior across every consumer — with zero schema change, zero response change, zero version bump, zero error.

There is no tool in the world today that treats a docstring edit as a breaking change. Kilter does.

---

## Stack

- **Backend:** Python 3.12 · FastAPI · PostgreSQL 16 + pgvector · `mcp>=1.27,<2` · APScheduler
- **Frontend:** React 18 · Vite · TypeScript · d3-scale · TanStack Query
- **Infra:** Docker Compose (local) · Fly.io / Railway (API) · Vercel (frontend)

---

## Quick start

```bash
# 1. Start Postgres
docker compose up -d db

# 2. Apply schema
psql $DATABASE_URL < db/schema.sql

# 3. Seed servers
python scripts/seed_servers.py

# 4. Start API
uvicorn api.main:app --reload

# 5. Start frontend
cd web && npm run dev
```

Copy `.env.example` to `.env` and fill in your values before starting.

---

## Demo path

1. `scripts/seed_servers.py` → seeds 30–60 public MCP servers
2. Probe runner connects, snapshots capabilities, executes ProbeSet per tool
3. First run establishes baselines (capability snapshot + per-field volatility)
4. Subsequent runs feed the diff engine → drift events
5. API `/servers/{id}/timeline` → frontend renders tolerance-band timeline
6. Click event → `/drift/{id}/evidence` → side-by-side statistics
7. BREAKING events → `/drift/{id}/fix` → real unified diff

---

## Probe safety

Every probe must be read-only. The `is_safe` guard in `engine/probe/runner.py` is a hard code check, not a config flag. Tools matching `create`, `update`, `delete`, `write`, `send`, `post`, `execute`, `run` are never probed. Rate limit: ≤ 0.2 rps per server. `opt_out` servers are excluded at the query layer.

---

## License

TBD.
