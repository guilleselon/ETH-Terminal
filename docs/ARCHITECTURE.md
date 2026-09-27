# Architecture

## Layer overview

ETH Terminal is structured in 5 layers:

1. **Sources** — External data fetchers (CMC, CCXT)
2. **Analysis** — Technical analysis engines
3. **Decisions** — User decision lifecycle management
4. **UI** — Presentation layer (styles, components, views)
5. **Scheduler** — Background daemon thread

## Data flow

[Describe the flow with a diagram]

User opens `/`
    ↓
HTMX triggers `/warmup`
    ↓
Sources fetch data from CMC + CCXT
    ↓
Analysis engines process the data
    ↓
Decisions state is refreshed
    ↓
UI renders the final HTML
    ↓
Scheduler continues in background

## Design decisions

### Why JSON and not SQLite?

The MVP uses JSON with atomic writes (`tmp` → `rename`) plus a
`threading.RLock` to serialize concurrent access between the web
thread and the scheduler thread. This keeps the project dependency-free
and portable.

Migration to SQLite is planned for when multi-pair support lands, as
the JSON approach would suffer from race conditions with multiple
symbols being watched simultaneously.

### Why a daemon thread and not a separate service?

The scheduler runs as a `daemon=True` thread inside the web process.
This means a single systemd service is enough, and the app works
in local mode without extra setup.

Downside: if the web crashes, the scheduler stops too. In production,
systemd auto-restarts the service, which brings the scheduler back up.

### Why hand-generated SVG and not Chart.js?

- Zero JavaScript dependencies
- Works offline
- Full control over the visual style
- No external CDN calls

The trade-off is more Python code, but the chart is simple enough
(candlesticks, zones, SL/TP lines) that manual generation is
maintainable.

### Why FastHTML + HTMX?

- Single-language stack (Python only)
- Progressive enhancement: works even without JavaScript
- Partial updates without a SPA framework
- Built-in ASGI/uvicorn integration

## Module responsibilities

| Module | Responsibility |
|---|---|
| `app/config.py` | Central configuration, environment loading |
| `app/logger.py` | Shared logger setup |
| `app/http_client.py` | Unified HTTP with requests/urllib fallback |
| `app/sources/cmc.py` | CoinMarketCap endpoints |
| `app/sources/cmc_usage.py` | Local credit counter |
| `app/sources/exchange.py` | CCXT OHLCV fetcher |
| `app/analysis/momentum.py` | Multi-period momentum interpreter |
| `app/analysis/volume.py` | Volume Profile, OBV, climax low |
| `app/analysis/zones.py` | Tactical + accumulation zone engines |
| `app/analysis/snapshot.py` | Snapshot storage and diff |
| `app/decisions/storage.py` | Decision JSON persistence |
| `app/decisions/manager.py` | Decision lifecycle (pin/unpin/status) |
| `app/notifications/telegram.py` | Telegram Bot API integration |
| `app/ui/styles.py` | Full CSS |
| `app/ui/components.py` | Reusable UI helpers |
| `app/ui/charts.py` | SVG chart generators |
| `app/ui/views.py` | Landing, topbar, main view |
| `app/scheduler.py` | Background price watcher |
| `app/routes.py` | HTTP routes and HTMX integration |
