"""
Source: Exchange (CCXT).

Downloads OHLCV candles from the exchange configured in .env
(EXCHANGE_NAME, SYMBOL) using CCXT.
"""

from app.config import EXCHANGE_NAME, SYMBOL
from app.logger import get_logger

log = get_logger(__name__)

# CCXT may not be installed in some environments
try:
    import ccxt
    HAS_CCXT = True
except ImportError:
    HAS_CCXT = False


def _get_exchange():
    """Create a CCXT instance with the standard configuration."""
    ex_class = getattr(ccxt, EXCHANGE_NAME)
    return ex_class({"enableRateLimit": True, "timeout": 15000})


def fetch_ohlcv(symbol=None, timeframe="1d", limit=90):
    """
    Download OHLCV candles from the configured exchange.

    Args:
        symbol:    pair (e.g. "ETH/USDT"). If None, uses SYMBOL from .env
        timeframe: "1d", "1h", etc.
        limit:     maximum number of candles

    Returns:
        (candles, None)   → list of dicts
        (None, error)     → string describing the failure

    Each candle has the shape:
        {"t": ms_epoch, "o": float, "h": float, "l": float, "c": float, "v": float}
    """
    if not HAS_CCXT:
        return None, "CCXT not installed. Run: pip install ccxt"

    if symbol is None:
        symbol = SYMBOL

    try:
        ex = _get_exchange()
        ohlcv = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

        if not ohlcv or len(ohlcv) < 30:
            return None, f"{EXCHANGE_NAME} returned only {len(ohlcv or [])} candles"

        candles = [
            {"t": c[0], "o": c[1], "h": c[2], "l": c[3], "c": c[4], "v": c[5]}
            for c in ohlcv
        ]

        log.info(f"{EXCHANGE_NAME} OK · {symbol} · {len(candles)} candles of {timeframe}")
        return candles, None

    except Exception as e:
        log.error(f"{EXCHANGE_NAME} failed: {type(e).__name__}: {e}")
        return None, f"{type(e).__name__}: {e}"
