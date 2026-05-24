# CLAUDE.md — Safra Radar

## Read in this order before any task

1. `docs/SPEC_CONSOLIDADA.md` — source of truth for product rules and architecture
2. `docs/DECISIONS_LOG.md` — architectural decisions, work patterns, lessons learned
3. `docs/DATA_SOURCES.md` — external data source catalog, viability, risk, fallback
4. `docs/AGENTS_BOUNDARIES.md` — agent executor boundaries
5. `docs/ROADMAP.md` — product phases and acceptance criteria

**If anything is ambiguous for the task at hand, STOP and ask Eduardo. Never assume undescribed behavior.**

## Hard constraints

- **Never recommend a sale.** Never output "sell X% now", "lock this in". Deliver data, historical context, and clear visuals. The decision belongs to the producer. Any feature approaching automatic recommendation requires Eduardo's explicit approval in DECISIONS_LOG before implementation.
- **Never run git push.** Eduardo handles all pushes manually (`git push origin main`). Prepare commits only when asked, never push.
- **Never work on a file without its full current content.** Eduardo must paste the complete current file content in the chat before any edit. Never assume what exists.
- **One step at a time.** One decision, one file, one prompt. Wait for confirmation before advancing.
- **Boundary test before every execution prompt.** Ask: "Does this prompt touch only one layer?" If not, decompose into separate prompts — one per agent.

## Agent boundaries (summary)

| Agent | Acts on | Never touches |
|---|---|---|
| **Claude Code** | Python API, engines, tools, connections, scripts, tests, `requirements.txt`, `.md` files in the repo | Supabase, Lovable, Render, anything outside the Python repo |
| **Lovable** | React frontend, Edge Function calls, Supabase JS client reads | Python API (direct), any calculation logic |
| **Supabase Dashboard** | SQL migrations, Edge Functions, RLS policies, secrets | — |
| **Render Dashboard** | Env vars, deploy settings, production logs | — |
| **Eduardo** | `git push`, business decisions, manual infra config, phase validation | — |

Full detail in `docs/AGENTS_BOUNDARIES.md`.

## Integration flow

    User opens Lovable
       ↓
    Lovable reads latest snapshot from Supabase (JS client)
       ↓
    If snapshot within threshold → display + "updated Xmin ago" badge
    If user clicks "update" → Lovable calls Edge Function api-proxy
       ↓
    Edge Function adds X-API-Key and calls Python API on Render
       ↓
    Python API queries external source (yfinance, CEPEA, etc.)
       ↓
    Python API returns JSON to Edge Function
       ↓
    Edge Function writes to data_snapshots (UPSERT) and returns to Lovable
       ↓
    Lovable updates UI
