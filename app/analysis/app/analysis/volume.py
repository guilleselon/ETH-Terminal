"""
Volume analysis engine.

Computes:
    - Last closed candle vs 7d/30d averages
    - Volume Profile (POC + Value Area 70%)
    - Climax low (possible capitulation)
    - OBV (accumulation vs distribution)
    - Detection of contradictions between daily volume and OBV
"""

from app.logger import get_logger

log = get_logger(__name__)


def compute_volume_analysis(candles):
    """
    Analyze the volume of a series of candles.

    Args:
        candles: list of dicts with t, o, h, l, c, v

    Returns:
        dict with all volume data, or None if there is not enough history.
    """
    if not candles or len(candles) < 31:
        return None

    vols = [c["v"] for c in candles]
    closes = [c["c"] for c in candles]
    highs = [c["h"] for c in candles]
    lows = [c["l"] for c in candles]

    # ── Last closed candle (not the ongoing partial one) ──
    vol_today_partial = vols[-1]
    vol_last_closed = vols[-2]
    vol_7d_avg = sum(vols[-9:-2]) / 7
    vol_30d_avg = sum(vols[-32:-2]) / 30

    vol_ratio_7d = vol_last_closed / vol_7d_avg if vol_7d_avg else 1
    vol_ratio_30d = vol_last_closed / vol_30d_avg if vol_30d_avg else 1

    # ── Volume Profile ──
    min_p = min(lows); max_p = max(highs)
    num_bins = 30
    bin_size = (max_p - min_p) / num_bins if max_p > min_p else 1
    bins = [0.0] * num_bins

    for c in candles:
        low_idx = min(max(int((c["l"] - min_p) / bin_size), 0), num_bins - 1)
        high_idx = min(max(int((c["h"] - min_p) / bin_size), 0), num_bins - 1)
        if high_idx == low_idx:
            bins[low_idx] += c["v"]
        else:
            vol_per_bin = c["v"] / (high_idx - low_idx + 1)
            for i in range(low_idx, high_idx + 1):
                bins[i] += vol_per_bin

    poc_idx = bins.index(max(bins))
    poc_price = min_p + (poc_idx + 0.5) * bin_size

    total_vol = sum(bins)
    sorted_bins = sorted(enumerate(bins), key=lambda x: x[1], reverse=True)
    cumsum = 0
    va_idx = []
    for idx, v in sorted_bins:
        va_idx.append(idx)
        cumsum += v
        if cumsum >= total_vol * 0.7:
            break
    va_low = min_p + min(va_idx) * bin_size
    va_high = min_p + (max(va_idx) + 1) * bin_size

    # ── Climax low (capitulation) ──
    climax_low = None
    climax_vol = 0
    climax_days_ago = None
    for i, c in enumerate(candles[:-1]):
        rng = c["h"] - c["l"]
        if rng <= 0:
            continue
        close_pos = (c["c"] - c["l"]) / rng
        if close_pos < 0.35 and c["v"] > vol_30d_avg * 1.5 and c["v"] > climax_vol:
            climax_vol = c["v"]
            climax_low = c["l"]
            climax_days_ago = len(candles) - 1 - i

    # ── OBV (On-Balance Volume) ──
    obv = [0.0]
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv.append(obv[-1] + vols[i])
        elif closes[i] < closes[i - 1]:
            obv.append(obv[-1] - vols[i])
        else:
            obv.append(obv[-1])

    obv_slope_pct = 0
    obv_signal = "neutral"
    if len(obv) >= 14:
        obv_14 = obv[-14]
        obv_now = obv[-1]
        denom = abs(obv_14) + sum(vols[-14:]) * 0.1
        obv_slope_pct = (obv_now - obv_14) / denom * 100
        if obv_slope_pct > 15:
            obv_signal = "accumulation"
        elif obv_slope_pct < -15:
            obv_signal = "distribution"

    # ── Volume level classification ──
    if vol_ratio_7d > 1.8:
        vol_level = "Very high"
        vol_note = "Last closed candle with volume well above normal — strong conviction"
    elif vol_ratio_7d > 1.2:
        vol_level = "High"
        vol_note = "Last closed candle with volume above average — move has backing"
    elif vol_ratio_7d < 0.6:
        vol_level = "Very low"
        vol_note = "Last closed candle with volume well below average — no short-term conviction"
    elif vol_ratio_7d < 0.85:
        vol_level = "Low"
        vol_note = "Last closed candle with weak volume — caution with the short-term signal"
    else:
        vol_level = "Normal"
        vol_note = "Last closed candle within the recent average"

    # ── Contradiction detection between volume and OBV ──
    vol_contradiction = None
    if vol_ratio_7d < 0.85 and obv_signal == "accumulation":
        vol_contradiction = (
            "The last candle shows low volume, but the OBV (14d) signals accumulation. "
            "Interpretation: large buyers acted on previous days — today the market "
            "is calm, not abandoned."
        )
    elif vol_ratio_7d < 0.85 and obv_signal == "distribution":
        vol_contradiction = (
            "Recent low volume and OBV distributing. Both signals point in the same "
            "weak direction: the market is not interested in going up."
        )
    elif vol_ratio_7d > 1.5 and obv_signal == "distribution":
        vol_contradiction = (
            "Last candle with high volume but OBV distributing over 14d. "
            "Interpretation: there was strong activity, but the overall bias is still to sell."
        )

    return {
        "vol_last": vol_last_closed,
        "vol_last_closed": vol_last_closed,
        "vol_today_partial": vol_today_partial,
        "vol_7d_avg": vol_7d_avg,
        "vol_30d_avg": vol_30d_avg,
        "vol_ratio_7d": vol_ratio_7d,
        "vol_ratio_30d": vol_ratio_30d,
        "vol_level": vol_level,
        "vol_note": vol_note,
        "vol_contradiction": vol_contradiction,
        "poc_price": poc_price,
        "va_low": va_low,
        "va_high": va_high,
        "climax_low": climax_low,
        "climax_vol": climax_vol,
        "climax_days_ago": climax_days_ago,
        "obv_signal": obv_signal,
        "obv_slope_pct": obv_slope_pct,
    }
