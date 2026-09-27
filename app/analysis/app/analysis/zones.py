"""
Buy zone engine.

Computes:
    - Tactical zone      (short term, 7-20 day supports)
    - Accumulation zone  (long term, 90 day supports)
    - Momentum adjustment (shifts zones up/down)
"""

from app.config import TP_NEAR_PRICE_PCT
from app.logger import get_logger

log = get_logger(__name__)

# TA is optional (falls back to manual calculation)
try:
    import pandas as pd
    import ta as ta_lib
    HAS_TA = True
except ImportError:
    HAS_TA = False


# ============================================================
#  Internal helpers
# ============================================================
def _ema_manual(values, period):
    """EMA computed by hand (fallback if `ta` is not installed)."""
    if not values:
        return []
    k = 2 / (period + 1)
    out, e = [], values[0]
    for v in values:
        e = v * k + e * (1 - k)
        out.append(e)
    return out


def _ema(values, period):
    """EMA using `ta` if available, otherwise manual calculation."""
    if HAS_TA and len(values) >= period:
        s = pd.Series(values)
        return float(ta_lib.trend.EMAIndicator(s, window=period).ema_indicator().iloc[-1])
    return _ema_manual(values, period)[-1]


def _bollinger_low(closes, window=20, dev=2):
    """Lower Bollinger band."""
    if HAS_TA and len(closes) >= window:
        s = pd.Series(closes)
        bb = ta_lib.volatility.BollingerBands(s, window=window, window_dev=dev)
        return float(bb.bollinger_lband().iloc[-1])
    # Manual fallback
    sma = sum(closes[-window:]) / window
    var = sum((c - sma) ** 2 for c in closes[-window:]) / window
    return sma - dev * (var ** 0.5)


def _cluster_prices(items, threshold_pct=0.02):
    """
    Group (name, price) tuples by proximity.

    Args:
        items:          list of (name, price)
        threshold_pct:  max distance between levels of the same cluster

    Returns:
        list of clusters, each one being a list of (name, price)
    """
    if not items:
        return []
    items_sorted = sorted(items, key=lambda x: x[1])
    clusters = [[items_sorted[0]]]
    for name, p in items_sorted[1:]:
        base = clusters[-1][-1][1]
        if abs(p - base) / base < threshold_pct:
            clusters[-1].append((name, p))
        else:
            clusters.append([(name, p)])
    return clusters


# ============================================================
#  Tactical zone (short term, 7-20 days)
# ============================================================
def compute_tactical_zone(candles):
    """
    Tactical entry zone based on short-term supports.

    Candidates:
        - EMA 20
        - Swing low 10d
        - Fib 0.382 / 0.500 / 0.618 over the 20d range
        - VWAP 7d

    Returns:
        dict with optimal_low/high/mid, sl, tp, rr, distance_pct, members
        None if there are not enough candidates
    """
    if not candles or len(candles) < 20:
        return None

    price = candles[-1]["c"]
    highs = [c["h"] for c in candles]
    lows = [c["l"] for c in candles]
    closes = [c["c"] for c in candles]
    vols = [c["v"] for c in candles]

    ema20 = _ema(closes, 20)
    swing_low_10 = min(lows[-10:])

    recent_high = max(highs[-20:])
    recent_low = min(lows[-20:])
    diff_recent = recent_high - recent_low
    fib_382_recent = recent_high - 0.382 * diff_recent
    fib_500_recent = recent_high - 0.500 * diff_recent
    fib_618_recent = recent_high - 0.618 * diff_recent

    window_7 = list(range(max(0, len(closes) - 7), len(closes)))
    tv = sum(vols[i] for i in window_7)
    vwap_7 = (sum(closes[i] * vols[i] for i in window_7) / tv) if tv > 0 else price

    candidates = [
        ("EMA 20", ema20),
        ("Swing low 10d", swing_low_10),
        ("Fib 0.382 (20d)", fib_382_recent),
        ("Fib 0.500 (20d)", fib_500_recent),
        ("Fib 0.618 (20d)", fib_618_recent),
        ("VWAP 7d", vwap_7),
    ]

    below = [(name, p) for name, p in candidates if p < price * 0.995]
    if not below:
        return None

    clusters = _cluster_prices(below, threshold_pct=0.02)
    # The cluster closest to the price = the one with the highest price
    clusters.sort(key=lambda c: max(p for _, p in c), reverse=True)
    best = clusters[0]

    prices = [p for _, p in best]
    zone_mid = sum(prices) / len(prices)
    buffer = 0.006
    zone_low = min(prices) * (1 - buffer)
    zone_high = max(prices) * (1 + buffer)

    stop_loss = zone_low * 0.975

    swing_high_10 = max(highs[-10:])
    if swing_high_10 > price * 1.02:
        take_profit = swing_high_10
    else:
        take_profit = price * 1.06

    entry = zone_mid
    risk = entry - stop_loss
    reward = take_profit - entry
    rr = reward / risk if risk > 0 else 0

    distance_pct = (zone_mid / price - 1) * 100
    net_return_from_current = (take_profit / price - 1) * 100 if price > 0 else 0
    tp_near_current = abs(net_return_from_current) < TP_NEAR_PRICE_PCT

    return {
        "optimal_low": zone_low,
        "optimal_high": zone_high,
        "optimal_mid": zone_mid,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "rr_ratio": rr,
        "rr_viable": rr >= 1.5,
        "distance_pct": distance_pct,
        "tp_distance_pct": (take_profit - entry) / entry * 100 if entry > 0 else 0,
        "net_return_from_current_pct": net_return_from_current,
        "tp_near_current": tp_near_current,
        "members": [name for name, _ in best],
    }


# ============================================================
#  Accumulation zone (long term, 90 days)
# ============================================================
def compute_buy_zones(candles, vol_analysis=None):
    """
    Accumulation zone based on long-term supports.

    Candidates:
        - Swing low 30d
        - Fibonacci 0.382 / 0.500 / 0.618 over the 90d range
        - Lower Bollinger
        - EMA 50
        - Percentile 25 over 90d
        - VWAP 30d
        - Mean 90d
        - Volume POC (if volume analysis is provided)
        - Value Area Low (if volume analysis is provided)
        - Climax low (if volume analysis is provided)

    Returns:
        dict with optimal_low/high/mid, sl, tp, rr, zone_members, etc.
    """
    if not candles or len(candles) < 30:
        return None

    price = candles[-1]["c"]
    highs = [c["h"] for c in candles]
    lows = [c["l"] for c in candles]
    closes = [c["c"] for c in candles]
    vols = [c["v"] for c in candles]

    min_90 = min(lows); max_90 = max(highs)
    swing_low_30 = min(lows[-30:])
    diff = max_90 - min_90
    fib_382 = max_90 - 0.382 * diff
    fib_500 = max_90 - 0.500 * diff
    fib_618 = max_90 - 0.618 * diff

    bb_low = _bollinger_low(closes, window=20, dev=2)
    ema50 = _ema(closes, 50)

    sorted_lows = sorted(lows)
    p25 = sorted_lows[max(0, len(sorted_lows) // 4)]

    window_30 = list(range(max(0, len(closes) - 30), len(closes)))
    tv = sum(vols[i] for i in window_30)
    vwap_30 = (sum(closes[i] * vols[i] for i in window_30) / tv) if tv > 0 else price

    swing_high_30 = max(highs[-30:])
    mean_90 = sum(closes) / len(closes)

    candidates = [
        ("Swing low 30d", swing_low_30),
        ("Fibonacci 0.382", fib_382),
        ("Fibonacci 0.500", fib_500),
        ("Fibonacci 0.618", fib_618),
        ("Bollinger Lower", bb_low),
        ("EMA 50", ema50),
        ("Percentile 25 (90d)", p25),
        ("VWAP 30d", vwap_30),
        ("Mean 90d", mean_90),
    ]

    if vol_analysis:
        candidates.append(("Volume POC (90d)", vol_analysis["poc_price"]))
        candidates.append(("Value Area Low (70%)", vol_analysis["va_low"]))
        if vol_analysis["climax_low"] and vol_analysis["climax_low"] < price * 0.995:
            days = vol_analysis["climax_days_ago"]
            label = f"Climax low ({days}d ago)" if days is not None else "Climax low"
            candidates.append((label, vol_analysis["climax_low"]))

    below = [(name, p) for name, p in candidates if p < price * 0.995]
    methods_detail = [
        {"name": name, "price": p, "distance": (p / price - 1) * 100, "below": p < price}
        for name, p in candidates
    ]

    if not below:
        return {
            "price": price,
            "optimal_low": price * 0.97, "optimal_high": price * 0.99,
            "optimal_mid": price * 0.98,
            "aggressive": price * 0.98, "aggressive_name": "Current price",
            "conservative": price * 0.94,
            "stop_loss": price * 0.93, "take_profit": price * 1.08,
            "rr_ratio": 2.0, "rr_viable": True,
            "tp_distance_pct": 10.0, "net_return_from_current_pct": 8.0,
            "tp_near_current": False,
            "confidence_count": 0,
            "methods": methods_detail, "zone_members": [],
        }

    clusters = _cluster_prices(below, threshold_pct=0.025)
    clusters.sort(key=len, reverse=True)
    optimal_cluster = clusters[0]

    prices_opt = [p for _, p in optimal_cluster]
    opt_mid = sum(prices_opt) / len(prices_opt)
    buffer_pct = 0.008
    opt_low = min(prices_opt) * (1 - buffer_pct)
    opt_high = max(prices_opt) * (1 + buffer_pct)

    closest_name, closest_price = min(below, key=lambda x: abs(x[1] - price))
    aggressive = closest_price

    lowest_cluster = sorted(clusters, key=lambda c: min(p for _, p in c))[0]
    conservative = min(p for _, p in lowest_cluster)

    stop_loss = opt_low * 0.97

    entry = opt_mid
    risk = entry - stop_loss
    TARGET_RR = 2.0
    tp_by_rr = entry + TARGET_RR * risk

    resistances = [swing_high_30, max_90]
    above = [r for r in resistances if r > price * 1.02]
    tp_resistance = min(above) if above else None

    if tp_resistance and tp_resistance <= tp_by_rr * 1.4:
        take_profit = tp_resistance
    else:
        take_profit = tp_by_rr

    reward = take_profit - entry
    rr = reward / risk if risk > 0 else 0
    rr_viable = rr >= 1.5

    tp_distance_pct = (take_profit - entry) / entry * 100 if entry > 0 else 0
    net_return_from_current_pct = (take_profit / price - 1) * 100 if price > 0 else 0
    tp_near_current = abs(net_return_from_current_pct) < TP_NEAR_PRICE_PCT

    return {
        "price": price,
        "optimal_low": opt_low, "optimal_high": opt_high, "optimal_mid": opt_mid,
        "aggressive": aggressive, "aggressive_name": closest_name,
        "conservative": conservative,
        "stop_loss": stop_loss,
        "take_profit": take_profit, "rr_ratio": rr,
        "rr_viable": rr_viable,
        "tp_distance_pct": tp_distance_pct,
        "net_return_from_current_pct": net_return_from_current_pct,
        "tp_near_current": tp_near_current,
        "confidence_count": len(optimal_cluster),
        "methods": methods_detail,
        "zone_members": [name for name, _ in optimal_cluster],
    }


# ============================================================
#  Momentum adjustment
# ============================================================
def apply_momentum_shift(zones, momentum):
    """
    Adjust a zone (tactical or accumulation) according to momentum.

    Returns:
        (updated_zones, shift_pct_applied)
    """
    if not momentum or not zones:
        return zones, 0.0

    shift = momentum.get("zone_shift", 0.0)
    if shift == 0.0:
        return zones, 0.0

    zones["optimal_low"]  *= (1 + shift)
    zones["optimal_high"] *= (1 + shift)
    zones["optimal_mid"]  *= (1 + shift)
    zones["stop_loss"] = zones["optimal_low"] * 0.97

    entry = zones["optimal_mid"]
    risk = entry - zones["stop_loss"]

    TARGET_RR = 2.0
    tp_by_rr = entry + TARGET_RR * risk

    old_tp = zones["take_profit"]
    if old_tp and old_tp <= tp_by_rr * 1.4:
        zones["take_profit"] = old_tp
    else:
        zones["take_profit"] = tp_by_rr

    reward = zones["take_profit"] - entry
    zones["rr_ratio"] = reward / risk if risk > 0 else 0
    zones["rr_viable"] = zones["rr_ratio"] >= 1.5
    zones["tp_distance_pct"] = (zones["take_profit"] - entry) / entry * 100 if entry > 0 else 0

    price = zones.get("price")
    if price and price > 0:
        zones["net_return_from_current_pct"] = (zones["take_profit"] / price - 1) * 100
        zones["tp_near_current"] = abs(zones["net_return_from_current_pct"]) < TP_NEAR_PRICE_PCT

    return zones, shift * 100
