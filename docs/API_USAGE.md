# CoinMarketCap API Usage

This document details how ETH Terminal uses the CoinMarketCap API
to build its decision engine.

## Endpoints used

### 1. `/v1/cryptocurrency/quotes/latest`

**Purpose**: Fetch spot price, 24h volume, and 6 percentage changes.

**Credits per call**: 1

**Response fields used**:
- `price` — current spot price in USD
- `volume_24h` — total 24h volume in USD
- `percent_change_1h`, `percent_change_24h`, `percent_change_7d`, `percent_change_30d`, `percent_change_60d`, `percent_change_90d`

**Used by**: `app/sources/cmc.py → fetch_cmc_full()`

**Why this endpoint**: A single call provides everything needed for
the momentum engine. The 6 percentage windows map directly to our
3 horizons (short: 1h + 24h, medium: 7d + 30d, long: 60d + 90d).

### 2. `/v1/global-metrics/quotes/latest`

**Purpose**: Fetch macro market context.

**Credits per call**: 1

**Response fields used**:
- `total_market_cap` — global crypto market cap
- `total_volume_24h` — global 24h volume
- `btc_dominance`, `eth_dominance`
- `total_market_cap_yesterday_percentage_change`

**Used by**: `app/sources/cmc.py → fetch_global_metrics()`

**Why this endpoint**: Gives the user macro context — a buy zone in
ETH is more meaningful if you know the overall market is trending up
or down.

### 3. `/v3/fear-and-greed/latest`

**Purpose**: Fetch the Crypto Fear & Greed Index.

**Credits per call**: 0 (keyless endpoint)

**Response fields used**:
- `value` — 0 to 100
- `value_classification` — "Extreme Fear" | "Fear" | "Neutral" | "Greed" | "Extreme Greed"

**Used by**: `app/sources/cmc.py → fetch_fear_greed()`

**Why this endpoint**: Classic contrarian indicator. Extreme fear
often marks local bottoms; extreme greed often marks local tops. We
display it in the "Market context" block as additional signal context.

## Credit consumption strategy

| Source | Credits/month |
|---|---|
| Scheduler (every 10 min) | ~4,320 |
| Manual `/data` and `/refresh` calls | ~300 |
| **Total estimated** | **~4,700** |
| **Basic plan limit** | **10,000** |
| **Remaining margin** | **~53%** |

### Local credit counter

Because CMC does not expose monthly consumed credits via the public
API, we maintain a local counter persisted in `data/cmc_usage.json`.

Every successful call to `fetch_cmc_full()` and `fetch_global_metrics()`
registers the exact credit count returned by CMC in the response body
(`status.credit_count`).

The user can see at any time how many credits remain in the topbar
badge: `API: 9,988/10,000 · 12 today`.

## Why we do not use CMC for OHLCV

The endpoint `/v1/cryptocurrency/ohlcv/historical` requires the
**Hobbyist plan** ($29/month) or higher. The Basic free tier does
not include it.

Since our technical analysis needs 90 daily candles, we use **CCXT**
with the configured exchange (default: CoinEx) to fetch OHLCV data
for free and without rate limit issues.

**Roadmap**: if the project scales, we plan to upgrade to the Hobbyist
plan to have a single data source for both quotes and OHLCV.

## Rate limits

The Basic plan allows **10,000 credits/month**. Endpoints consume:

| Endpoint | Credits |
|---|---|
| `quotes/latest` (1 symbol) | 1 |
| `quotes/latest` (N symbols) | N |
| `global-metrics/quotes/latest` | 1 |
| `fear-and-greed/latest` | 0 |

The scheduler is designed to use **1 credit per cycle** by only
calling `fetch_cmc_full()` for the analyzed symbol. Global metrics
and Fear & Greed are only fetched on-demand when the user opens the
dashboard, not by the scheduler.
