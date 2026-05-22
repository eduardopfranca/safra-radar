# Safra Radar

Market intelligence portal for soy and corn — built for the Brazilian mid-size producer (500–3,000 ha). Product by Madcap.

**Product promise:** curated market data at commodity-trading-desk level, translated into plain producer language. Prices in BRL/sack, exchange rate, port premium, ENSO, USDA events, and post-event rapid analysis. Never recommends a sale. Delivers data + historical context + clear visuals; the decision belongs to the producer.

## Stack

| Layer | Technology |
|---|---|
| Backend/API | Python 3.11+ + FastAPI, deployed on Render |
| Database | Supabase (PostgreSQL) |
| Auth proxy | Supabase Edge Function (`api-proxy`) |
| Frontend | React/TypeScript via Lovable |
| Frontend mirror | Vercel |
| Repository | GitHub `eduardopfranca/safra-radar` |

## Repository structure

    safra-radar/
    ├── README.md
    ├── CLAUDE.md
    ├── .gitignore
    ├── requirements.txt
    ├── docs/                  # Product spec (Portuguese)
    │   ├── README.md
    │   ├── SPEC_CONSOLIDADA.md
    │   ├── DECISIONS_LOG.md
    │   ├── DATA_SOURCES.md
    │   ├── AGENTS_BOUNDARIES.md
    │   └── ROADMAP.md
    ├── api/
    │   ├── routers/
    │   └── schemas/
    ├── engines/
    ├── tools/
    ├── connections/
    ├── scripts/
    └── tests/

## Documentation (`docs/`)

| File | Contents |
|---|---|
| `docs/SPEC_CONSOLIDADA.md` | Product vision, MVP scope, architecture, invariant rules |
| `docs/DECISIONS_LOG.md` | Architectural decisions, work patterns, lessons learned |
| `docs/DATA_SOURCES.md` | External data sources: URL, method, frequency, quality, risk, fallback |
| `docs/AGENTS_BOUNDARIES.md` | Agent responsibilities: Claude, Claude Code, Lovable, Supabase, Render, Eduardo |
| `docs/ROADMAP.md` | Phases 0–6 with acceptance criteria per phase |

## Dependency hierarchy (invariant)

    scripts/ → connections/ → tools/ → engines/ → utils.py / helpers.py
                                                        ↑
                                        api/ (may import from any layer below)

No layer imports from layers above it. Engines are pure computation — no I/O, no database, no side effects.

## Coding rules

1. All code in English — variables, docstrings, logs, method names.
2. Engines are pure computation — no I/O, no side effects.
3. Atomic helpers always in `utils.py` or `helpers.py`.
4. Dependency hierarchy is invariant — never import upward.
5. Never compute in the frontend — all calculations in the Python API.
6. Persist JSONB objects whole — no cherry-picking fields when storing API responses.
7. Unit conversions only at layer boundaries.
8. Cite source and timestamp on every external-data endpoint.
9. When in doubt: stop and ask Eduardo.

## Git workflow

Eduardo handles all git operations manually. Claude Code prepares commits but **never pushes** without explicit instruction (`git push origin master:main` is Eduardo's responsibility).
