"""
Source: CoinMarketCap.

Provides three functions that cover the whole CMC integration:

    fetch_cmc_full()       price + volume + multi-period ratings (1 credit)
    fetch_global_metrics() global market metrics (1 credit)
    fetch_fear_greed()     Fear & Greed index (keyless, 0 credits)

Every successful call to a CMC endpoint is registered in the local
credit counter (app/sources/cmc_usage.py).
"""

from app.config import CMC_BASE, CMC_API_KEY
from app.http_client import http_get_json
from app.logger import get_logger
from app.sources.cmc_usage import register_call

log = get_logger(__name__)


def fetch_cmc_full(symbol="ETH"):
    """
    Fetch price + volume + multi-window ratings from CoinMarketCap.

    A single call to quotes/latest returns everything needed for the
    momentum engine: current price, 24h volume, and percentage changes
    for 1h / 24h / 7d / 30d / 60d / 90d.

    Args:
        symbol: base symbol without pair (e.g. "ETH", "BTC")

    Returns:
        (data, None)     → dict with all fields
        (None, error)    → string describing the failure
    """
    if not CMC_API_KEY:
        return None, "Missing CMC_API_KEY in environment"

    try:
        data = http_get_json(
            f"{CMC_BASE}/v1/cryptocurrency/quotes/latest",
            params={"symbol": symbol, "convert": "USD"},
            headers={
                "X-CMC_PRO_API_KEY": CMC_API_KEY,
                "Accept": "application/json",
            },
            timeout=10,
        )

        if not data:
            return None, "CMC returned no data"

        if "data" not in data or symbol not in data["data"]:
            return None, f"CMC returned unexpected structure: {str(data)[:200]}"

        q = data["data"][symbol]["quote"]["USD"]

        result = {
            "price":  q.get("price"),
            "vol24h": q.get("volume_24h") or 0,
            "chg1h":  q.get("percent_change_1h"),
            "chg24h": q.get("percent_change_24h"),
            "chg7d":  q.get("percent_change_7d"),
            "chg30d": q.get("percent_change_30d"),
            "chg60d": q.get("percent_change_60d"),
            "chg90d": q.get("percent_change_90d"),
        }

        # Register credit consumption in the local counter
        # CMC returns the exact credit count in status.credit_count
        credit_count = 1
        try:
            credit_count = int(data.get("status", {}).get("credit_count", 1))
        except Exception:
            pass
        register_call(credits=credit_count, endpoint="quotes/latest")

        log.info(
            f"CMC OK · {symbol} = ${result['price']:,.2f} · "
            f"vol24h ${result['vol24h']/1e9:.2f}B "
            f"(consumed {credit_count} credit{'s' if credit_count != 1 else ''})"
        )
        return result, None

    except Exception as e:
        log.error(f"CMC failed: {type(e).__name__}: {e}")
        return None, f"{type(e).__name__}: {e}"


def fetch_global_metrics():
    """
    Fetch global crypto market metrics from CMC.

    Cost: 1 credit per call.

    Returns:
        (data, None) → dict with:
            total_market_cap
            total_volume_24h
            market_cap_change_24h
            btc_dominance
            eth_dominance
            active_cryptocurrencies
            active_exchanges
        (None, error)
    """
    if not CMC_API_KEY:
        return None, "Missing CMC_API_KEY in environment"

    try:
        data = http_get_json(
            f"{CMC_BASE}/v1/global-metrics/quotes/latest",
            params={"convert": "USD"},
            headers={
                "X-CMC_PRO_API_KEY": CMC_API_KEY,
                "Accept": "application/json",
            },
            timeout=10,
        )

        if not data or "data" not in data:
            return None, f"Unexpected response: {str(data)[:200]}"

        d = data["data"]
        quote = d.get("quote", {}).get("USD", {})

        result = {
            "total_market_cap": quote.get("total_market_cap") or 0,
            "total_volume_24h": quote.get("total_volume_24h") or 0,
            "market_cap_change_24h": quote.get("total_market_cap_yesterday_percentage_change") or 0,
            "btc_dominance": d.get("btc_dominance") or 0,
            "eth_dominance": d.get("eth_dominance") or 0,
            "active_cryptocurrencies": d.get("active_cryptocurrencies") or 0,
            "active_exchanges": d.get("active_exchanges") or 0,
        }

        # Register credit consumption
        credit_count = 1
        try:
            credit_count = int(data.get("status", {}).get("credit_count", 1))
        except Exception:
            pass
        register_call(credits=credit_count, endpoint="global-metrics/quotes/latest")

        log.info(
            f"CMC Global OK · MCap ${result['total_market_cap']/1e12:.2f}T · "
            f"BTC dom {result['btc_dominance']:.1f}%"
        )
        return result, None

    except Exception as e:
        log.error(f"CMC Global failed: {type(e).__name__}: {e}")
        return None, f"{type(e).__name__}: {e}"


def fetch_fear_greed():
    """
    Fetch the Crypto Fear & Greed index from CMC.

    Cost: 1 credit per call.
    Available even without an API key (keyless endpoint).

    Returns:
        (data, None) → dict with:
            value                 0..100
            value_classification  "Extreme Fear" | "Fear" | "Neutral" | "Greed" | "Extreme Greed"
            update_time           ISO string
        (None, error)
    """
    try:
        # Keyless endpoint (no API key required)
        url = f"{CMC_BASE}/public-api/v3/fear-and-greed/latest"

        data = http_get_json(url, timeout=10)

        if not data or "data" not in data:
            return None, f"Unexpected response: {str(data)[:200]}"

        d = data["data"]
        result = {
            "value": d.get("value", 50),
            "value_classification": d.get("value_classification", "Neutral"),
            "update_time": d.get("update_time"),
        }

        log.info(
            f"CMC F&G OK · {result['value']} "
            f"({result['value_classification']})"
        )
        return result, None

    except Exception as e:
        log.error(f"CMC F&G failed: {type(e).__name__}: {e}")
        return None, f"{type(e).__name__}: {e}"

def fetch_price_only(symbol="ETH"):
    """
    Lightweight version for the scheduler.

    Returns only price + 24h change. Still consumes 1 credit because
    CMC does not offer a cheaper endpoint for a single symbol.

    Returns:
        (data, None)   → {"price": float, "chg24h": float|None}
        (None, error)  → string describing the failure
    """
    full, err = fetch_cmc_full(symbol)
    if err or not full:
        return None, err or "no data"
    return {
        "price": full["price"],
        "chg24h": full.get("chg24h"),
    }, None
