# ETH Terminal

> Technical analyzer for ETH/USDT that turns raw market data into actionable decisions — buy zones with calculated stop, take profit and R:R, plus automatic Telegram notifications.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastHTML](https://img.shields.io/badge/FastHTML-0.6+-627EEA)](https://fastht.ml/)
[![CoinMarketCap](https://img.shields.io/badge/API-CoinMarketCap-3861FB)](https://coinmarketcap.com/api/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📸 Screenshots

![Dashboard](docs/screenshots/dashboard.png)
*Main dashboard: tactical and accumulation zones with SL/TP marked*

![Telegram notification](docs/screenshots/telegram.png)
*Automatic notification when the price enters a zone*

![Global context](docs/screenshots/global-context.png)
*Macro market context via CoinMarketCap*

---

## 🎯 What does it do?

ETH Terminal solves a specific problem: **knowing when and where to buy ETH**.

Instead of showing charts and expecting the user to interpret them, it computes two **real buy zones** with all the data needed to trade:

| Zone | Horizon | Based on |
|---|---|---|
| ⚡ **Tactical** | Short term (1-3 days) | EMA 20, swing low 10d, Fibonacci 20d, VWAP 7d |
| 🎯 **Accumulation** | Long term (weeks) | 12 methods over 90 days |

Each zone includes:
- **Entry range** exact
- **Stop loss** and **take profit** with calculated R:R
- **Confluence** — which methods coincide in that zone
- **Momentum adjustment** — shifts based on market context

When the price enters a zone you pinned, you get a **Telegram notification**. When it reaches the TP or breaks the SL, you also do.

---

## 🚀 Features

- ✅ **Two buy zones** — short and long term, not a generic one
- ✅ **12 technical methods** — Fibonacci, EMA, Bollinger, Volume Profile, OBV, VWAP, Percentiles
- ✅ **Multi-period momentum** — combines 1h, 24h, 7d, 30d, 60d, 90d into a single diagnostic
- ✅ **Volume analysis** — POC, Value Area, OBV, climax low detection
- ✅ **24/7 scheduler** — watches the price every 10 minutes without the app being open
- ✅ **Telegram notifications** — alerts when the price enters a zone, hits TP or breaks SL
- ✅ **Pinnable decisions** — freeze a zone in time to track its evolution
- ✅ **Change history** — detects when the analysis changed materially
- ✅ **CMC credits counter** — respects the free tier limit
- ✅ **HTMX-driven UI** — partial updates without custom JavaScript
- ✅ **Zero chart libraries** — all SVGs hand-generated

---

## 🧩 CoinMarketCap API usage

This project uses **3 CMC endpoints** to feed the decision engine:

| Endpoint | Purpose | Credits |
|---|---|---|
| `/v1/cryptocurrency/quotes/latest` | Spot price + 24h volume + 6 percentage changes (1h, 24h, 7d, 30d, 60d, 90d) | 1 |
| `/v1/global-metrics/quotes/latest` | Global market cap, BTC/ETH dominance, total volume | 1 |
| `/v3/fear-and-greed/latest` | Fear & Greed index (keyless) | 0 |

**Estimated consumption**: ~4,700 credits/month out of the 10,000 from the Basic free tier (47% margin).

Each call is recorded in a local counter persisted in `data/cmc_usage.json`. The user sees in real time how many calls remain in the topbar badge.

For historical OHLCV candles, **CCXT** is used because CMC's free tier does not include that endpoint.

---

## 🛠 Tech stack

| Component | Technology |
|---|---|
| **Backend** | Python 3.10+ |
| **Web framework** | FastHTML (ASGI + HTMX) |
| **Market data** | CoinMarketCap API + CCXT (candles) |
| **Technical indicators** | `ta` + `pandas` |
| **Charts** | Hand-generated SVG (no libraries) |
| **Persistence** | JSON with atomic writes and locks |
| **Scheduler** | Internal daemon thread |
| **Notifications** | Telegram Bot API |

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- A free [CoinMarketCap](https://pro.coinmarketcap.com/signup) API key (10,000 credits/month)
- (Optional) A Telegram bot for notifications

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/eth-terminal.git
cd eth-terminal

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure credentials
cp .env.example .env
# Edit .env and fill in your CMC_API_KEY (and optionally Telegram)
