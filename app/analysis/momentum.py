"""
Momentum engine.

Interprets the 6 percentage changes from CoinMarketCap
(1h, 24h, 7d, 30d, 60d, 90d) by grouping them into 3 horizons:
    Short  → 1h + 24h
    Medium → 7d + 30d
    Long   → 60d + 90d

Then classifies the sign pattern into 7 possible scenarios.
"""


# ============================================================
#  Scenario table
# ============================================================
_SCENARIOS = {
    "+++": {
        "label": "Confirmed bullish trend",
        "advice": "All three horizons are up. Pullbacks tend to be short.",
        "advice_far": "All three horizons are up, but the entry zone is far. "
                      "The market hasn't pulled back yet — wait without rush.",
        "class": "buy-strong", "zone_shift": 0.010,
    },
    "-++": {
        "label": "Healthy pullback in a bullish trend",
        "advice": "Short term is correcting but medium and long are up. Classic buy setup.",
        "advice_far": "Correction underway but the zone is still far. "
                      "No rush — wait for the price to come closer.",
        "class": "buy-strong", "zone_shift": 0.000,
    },
    "--+": {
        "label": "Deep pullback in a bullish trend",
        "advice": "Short and medium are down, long holds. Opportunity if it reaches the conservative zone.",
        "advice_far": "Deep correction in progress. The conservative zone is the reference "
                      "— patience.",
        "class": "buy-caution", "zone_shift": -0.015,
    },
    "+--": {
        "label": "Bounce in a bearish trend",
        "advice": "Short timeframes are up but long ones are down. Possible bull trap.",
        "advice_far": "Bounce inside a bearish trend. Zone is far — "
                      "better not to chase the price.",
        "class": "wait", "zone_shift": -0.010,
    },
    "+-+": {
        "label": "Early recovery",
        "advice": "Short and long are up, medium is correcting. Watch for medium confirmation.",
        "advice_far": "Early recovery but the zone is far. "
                      "Confirm before acting.",
        "class": "wait", "zone_shift": 0.000,
    },
    "-+-": {
        "label": "Potential top",
        "advice": "Medium is up while long is down. Momentum is fading.",
        "advice_far": "Potential top, zone is far. If price doesn't correct, "
                      "better stay out.",
        "class": "wait", "zone_shift": -0.010,
    },
    "---": {
        "label": "Confirmed bearish trend",
        "advice": "All three horizons are down. Wait for capitulation.",
        "advice_far": "Confirmed bearish trend. The conservative zone is the reference "
                      "— don't buy before it.",
        "class": "sell", "zone_shift": -0.030,
    },
}

_FALLBACK = {
    "label": "Mixed momentum",
    "advice": "No clear pattern across horizons — wait for confirmation.",
    "advice_far": "No clear pattern. The zone is far — wait without rush.",
    "class": "wait", "zone_shift": 0.0,
}


# ============================================================
#  Main function
# ============================================================
def analyze_momentum(cmc):
    """
    Analyze momentum from the CMC dict.

    Args:
        cmc: dict with chg1h, chg24h, chg7d, chg30d, chg60d, chg90d

    Returns:
        dict with:
            pattern       "+++" / "-++" / etc.
            short_avg     average of 1h + 24h
            medium_avg    average of 7d + 30d
            long_avg      average of 60d + 90d
            label         diagnostic text
            advice        advice when the zone is close
            advice_far    advice when the zone is far
            class         used for UI coloring
            zone_shift    adjustment to apply to the zone
        None if there is not enough data
    """
    if not cmc:
        return None

    short  = [v for v in [cmc.get("chg1h"),  cmc.get("chg24h")] if v is not None]
    medium = [v for v in [cmc.get("chg7d"),  cmc.get("chg30d")] if v is not None]
    long_t = [v for v in [cmc.get("chg60d"), cmc.get("chg90d")] if v is not None]

    if not short or not medium or not long_t:
        return None

    s_avg = sum(short)  / len(short)
    m_avg = sum(medium) / len(medium)
    l_avg = sum(long_t) / len(long_t)

    s_sign = "+" if s_avg > 0 else "-"
    m_sign = "+" if m_avg > 0 else "-"
    l_sign = "+" if l_avg > 0 else "-"
    pattern = f"{s_sign}{m_sign}{l_sign}"

    base = _SCENARIOS.get(pattern, _FALLBACK)

    return {
        "pattern": pattern,
        "short_avg": s_avg,
        "medium_avg": m_avg,
        "long_avg": l_avg,
        "signs": (s_sign, m_sign, l_sign),
        **base,
    }
