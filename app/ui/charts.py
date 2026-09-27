"""Candlestick and volume SVGs, hand-generated."""

from datetime import datetime
from fasthtml.common import NotStr


# ============================================================
#  Candlestick chart with zones, SL/TP, axes and native tooltips
# ============================================================
def candlestick_svg(candles, tactical=None, accumulation=None, w=1000, h=520):
    """
    Generate an SVG with:
        - Japanese candlesticks (with native browser tooltips via <title>)
        - Y axis on the left (prices)
        - X axis at the bottom (dates)
        - Blue band: tactical zone
        - Green band: accumulation zone
        - SL/TP lines for each zone with labels

    Hovering any candle shows a native tooltip with date, change %,
    volume and full OHLC. Works without JavaScript.
    """
    if not candles:
        return NotStr("")

    ml, mr, mt, mb = 78, 12, 16, 46
    plot_w = w - ml - mr
    plot_h = h - mt - mb

    highs = [c["h"] for c in candles]
    lows = [c["l"] for c in candles]
    mn, mx = min(lows), max(highs)

    # Expand range if there are zones so SL/TP fit
    if tactical:
        mn = min(mn, tactical["stop_loss"] * 0.99)
        mx = max(mx, tactical["take_profit"] * 1.01)
    if accumulation:
        mn = min(mn, accumulation["stop_loss"] * 0.99)
        mx = max(mx, accumulation["take_profit"] * 1.01)

    pad = (mx - mn) * 0.04
    mn -= pad
    mx += pad
    rng = (mx - mn) or 1

    n = len(candles)
    gap = plot_w / n
    cw = max(gap * 0.65, 1.2)

    def y_price(p):
        return mt + plot_h - ((p - mn) / rng) * plot_h

    def fmt_volume(v):
        """Format large volumes: 1.23B, 45.6M, 789K, 123."""
        if v >= 1e9:
            return f"{v/1e9:.2f}B"
        if v >= 1e6:
            return f"{v/1e6:.2f}M"
        if v >= 1e3:
            return f"{v/1e3:.2f}K"
        return f"{v:.0f}"

    def candle_tooltip(c):
        """Build the native tooltip text for a candle."""
        try:
            date_str = datetime.fromtimestamp(c["t"] / 1000).strftime("%Y-%m-%d")
        except Exception:
            date_str = "—"
        change_pct = ((c["c"] / c["o"] - 1) * 100) if c["o"] else 0
        sign = "+" if change_pct >= 0 else ""
        return (
            f"{date_str} · {sign}{change_pct:.2f}% · Vol {fmt_volume(c['v'])}\n"
            f"O ${c['o']:,.2f} · H ${c['h']:,.2f}\n"
            f"L ${c['l']:,.2f} · C ${c['c']:,.2f}"
        )

    parts = []

    # Grid + prices (background)
    for i in range(6):
        frac = i / 5
        p = mx - frac * rng
        y = mt + frac * plot_h
        parts.append(
            f'<line x1="{ml}" y1="{y:.1f}" x2="{ml + plot_w}" y2="{y:.1f}" '
            f'stroke="#1f2937" stroke-width="1" stroke-dasharray="3 4"/>'
        )
        parts.append(
            f'<text x="{ml - 8}" y="{y + 4:.1f}" fill="#9ca3af" '
            f'font-size="12" font-family="monospace" text-anchor="end">'
            f'${p:,.0f}</text>'
        )

    # Zone bands (background)
    if accumulation:
        y_high = y_price(accumulation["optimal_high"])
        y_low = y_price(accumulation["optimal_low"])
        parts.append(
            f'<rect x="{ml}" y="{y_high:.1f}" width="{plot_w}" '
            f'height="{y_low - y_high:.1f}" fill="#22c55e" opacity="0.13"/>'
        )
    if tactical:
        y_high_t = y_price(tactical["optimal_high"])
        y_low_t = y_price(tactical["optimal_low"])
        parts.append(
            f'<rect x="{ml}" y="{y_high_t:.1f}" width="{plot_w}" '
            f'height="{y_low_t - y_high_t:.1f}" fill="#3b82f6" opacity="0.22"/>'
        )

    # Candles (with native browser tooltips via <title>)
    for i, c in enumerate(candles):
        x = ml + i * gap + gap / 2
        y_h, y_l = y_price(c["h"]), y_price(c["l"])
        y_o, y_c = y_price(c["o"]), y_price(c["c"])
        color = "#22c55e" if c["c"] >= c["o"] else "#ef4444"
        top, bot = min(y_o, y_c), max(y_o, y_c)
        bh = max(bot - top, 1.5)

        tooltip = candle_tooltip(c)

        # Wick (with tooltip)
        parts.append(
            f'<line x1="{x:.1f}" y1="{y_h:.1f}" x2="{x:.1f}" y2="{y_l:.1f}" '
            f'stroke="{color}" stroke-width="1.2">'
            f'<title>{tooltip}</title>'
            f'</line>'
        )
        # Body (with tooltip)
        parts.append(
            f'<rect x="{x - cw/2:.1f}" y="{top:.1f}" width="{cw:.1f}" '
            f'height="{bh:.1f}" fill="{color}" opacity="0.9">'
            f'<title>{tooltip}</title>'
            f'</rect>'
        )

    # Zone borders + names
    if accumulation:
        y_high = y_price(accumulation["optimal_high"])
        y_low = y_price(accumulation["optimal_low"])
        parts.append(
            f'<line x1="{ml}" y1="{y_high:.1f}" x2="{ml + plot_w}" y2="{y_high:.1f}" '
            f'stroke="#22c55e" stroke-width="1" stroke-dasharray="4 3" opacity="0.6"/>'
        )
        parts.append(
            f'<line x1="{ml}" y1="{y_low:.1f}" x2="{ml + plot_w}" y2="{y_low:.1f}" '
            f'stroke="#22c55e" stroke-width="1" stroke-dasharray="4 3" opacity="0.6"/>'
        )
        y_mid = (y_high + y_low) / 2
        parts.append(
            f'<text x="{ml + 8}" y="{y_mid + 4:.1f}" fill="#4ade80" '
            f'font-size="10" font-family="monospace" font-weight="700">'
            f'ACCUMULATION</text>'
        )
    if tactical:
        y_high_t = y_price(tactical["optimal_high"])
        y_low_t = y_price(tactical["optimal_low"])
        parts.append(
            f'<line x1="{ml}" y1="{y_high_t:.1f}" x2="{ml + plot_w}" y2="{y_high_t:.1f}" '
            f'stroke="#3b82f6" stroke-width="1.2" stroke-dasharray="4 3" opacity="0.7"/>'
        )
        parts.append(
            f'<line x1="{ml}" y1="{y_low_t:.1f}" x2="{ml + plot_w}" y2="{y_low_t:.1f}" '
            f'stroke="#3b82f6" stroke-width="1.2" stroke-dasharray="4 3" opacity="0.7"/>'
        )
        y_mid_t = (y_high_t + y_low_t) / 2
        parts.append(
            f'<text x="{ml + 8}" y="{y_mid_t + 4:.1f}" fill="#93c5fd" '
            f'font-size="10" font-family="monospace" font-weight="700">'
            f'TACTICAL ENTRY</text>'
        )

    # SL/TP lines with labels
    def draw_sl_tp(price_val, color, label, label_x_offset):
        y = y_price(price_val)
        if not (mt <= y <= mt + plot_h):
            return ""
        line = (
            f'<line x1="{ml}" y1="{y:.1f}" x2="{ml + plot_w}" y2="{y:.1f}" '
            f'stroke="{color}" stroke-width="1.4" stroke-dasharray="6 3" '
            f'opacity="0.9"/>'
        )
        label_w = len(label) * 6.2 + 10
        label_h = 14
        label_x = ml + 4 + label_x_offset
        label_y = y - label_h / 2
        rect = (
            f'<rect x="{label_x:.1f}" y="{label_y:.1f}" '
            f'width="{label_w:.1f}" height="{label_h}" '
            f'rx="3" ry="3" fill="{color}"/>'
        )
        text = (
            f'<text x="{label_x + label_w/2:.1f}" y="{y + 4:.1f}" '
            f'fill="#0b0f17" font-size="10" font-family="monospace" '
            f'font-weight="700" text-anchor="middle">{label}</text>'
        )
        return rect + text + line

    if tactical:
        parts.append(draw_sl_tp(tactical["stop_loss"], "#f87171", "SL TAC.", 0))
        parts.append(draw_sl_tp(tactical["take_profit"], "#60a5fa", "TP TAC.", 0))
    if accumulation:
        parts.append(draw_sl_tp(accumulation["stop_loss"], "#dc2626", "SL ACC.", 68))
        parts.append(draw_sl_tp(accumulation["take_profit"], "#3b82f6", "TP ACC.", 68))

    # X axis (dates)
    lc = 6
    for i in range(lc):
        idx = min(max(round(i * (n - 1) / (lc - 1)), 0), n - 1)
        x = ml + idx * gap + gap / 2
        try:
            label = datetime.fromtimestamp(candles[idx]["t"] / 1000).strftime("%d/%m")
        except Exception:
            label = "—"
        parts.append(
            f'<text x="{x:.1f}" y="{h - 16}" fill="#9ca3af" '
            f'font-size="12" font-family="monospace" text-anchor="middle">'
            f'{label}</text>'
        )

    # Base lines (axes)
    y_base = mt + plot_h
    parts.append(
        f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{y_base}" '
        f'stroke="#374151" stroke-width="1.2"/>'
    )
    parts.append(
        f'<line x1="{ml}" y1="{y_base}" x2="{ml + plot_w}" y2="{y_base}" '
        f'stroke="#374151" stroke-width="1.2"/>'
    )

    return NotStr(
        f'<svg width="100%" height="{h}" viewBox="0 0 {w} {h}" '
        f'style="display:block">{"".join(parts)}</svg>'
    )


# ============================================================
#  Volume chart
# ============================================================
def volume_svg(candles, vol_analysis=None, w=1000, h=160):
    """
    Volume bars with:
        - Yellow line: 7d average
        - Yellow circle: climax low
        - Dotted border: current ongoing candle
    """
    if not candles:
        return NotStr("")

    ml, mr, mt, mb = 78, 12, 10, 30
    plot_w = w - ml - mr
    plot_h = h - mt - mb
    vols = [c["v"] for c in candles]
    mx = max(vols) or 1
    n = len(candles)
    gap = plot_w / n

    def y_vol(v):
        return mt + plot_h - (v / mx) * plot_h

    parts = []

    # Grid
    for i in range(3):
        frac = i / 2
        vol = mx - frac * mx
        y = mt + frac * plot_h
        parts.append(
            f'<line x1="{ml}" y1="{y:.1f}" x2="{ml + plot_w}" y2="{y:.1f}" '
            f'stroke="#1f2937" stroke-width="1" stroke-dasharray="3 4"/>'
        )
        label = f"{vol/1e6:.0f}M" if vol >= 1e6 else f"{vol/1e3:.0f}K"
        parts.append(
            f'<text x="{ml - 8}" y="{y + 4:.1f}" fill="#9ca3af" '
            f'font-size="12" font-family="monospace" text-anchor="end">{label}</text>'
        )

    vol_30d_avg = sum(vols[-31:-1]) / 30 if len(vols) >= 31 else sum(vols) / len(vols)

    # Bars
    for i, c in enumerate(candles):
        x = ml + i * gap + gap / 2
        y = y_vol(c["v"])
        bh = (mt + plot_h) - y
        base_color = "#22c55e" if c["c"] >= c["o"] else "#ef4444"
        opacity = "0.85" if c["v"] > vol_30d_avg * 1.5 else "0.4"
        if i == len(candles) - 1:
            parts.append(
                f'<rect x="{x - gap*0.32:.1f}" y="{y:.1f}" '
                f'width="{gap*0.64:.1f}" height="{bh:.1f}" '
                f'fill="{base_color}" opacity="{opacity}" '
                f'stroke="#facc15" stroke-width="1" stroke-dasharray="2 2"/>'
            )
        else:
            parts.append(
                f'<rect x="{x - gap*0.32:.1f}" y="{y:.1f}" '
                f'width="{gap*0.64:.1f}" height="{bh:.1f}" '
                f'fill="{base_color}" opacity="{opacity}"/>'
            )

    # 7-day moving average
    if len(vols) >= 7:
        ma_pts = []
        for i in range(6, len(vols)):
            avg = sum(vols[i-6:i+1]) / 7
            x = ml + i * gap + gap / 2
            y = y_vol(avg)
            ma_pts.append((x, y))
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in ma_pts)
        parts.append(
            f'<polyline points="{poly}" fill="none" stroke="#eab308" '
            f'stroke-width="1.5" opacity="0.85"/>'
        )

    # Climax low
    if vol_analysis and vol_analysis.get("climax_days_ago") is not None:
        idx = len(candles) - 1 - vol_analysis["climax_days_ago"]
        if 0 <= idx < n:
            x = ml + idx * gap + gap / 2
            y = y_vol(vols[idx])
            parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" '
                f'fill="none" stroke="#facc15" stroke-width="2"/>'
            )

    # X axis
    lc = 6
    for i in range(lc):
        idx = min(max(round(i * (n - 1) / (lc - 1)), 0), n - 1)
        x = ml + idx * gap + gap / 2
        try:
            label = datetime.fromtimestamp(candles[idx]["t"] / 1000).strftime("%d/%m")
        except Exception:
            label = "—"
        parts.append(
            f'<text x="{x:.1f}" y="{h - 8}" fill="#9ca3af" '
            f'font-size="12" font-family="monospace" text-anchor="middle">'
            f'{label}</text>'
        )

    y_base = mt + plot_h
    parts.append(
        f'<line x1="{ml}" y1="{y_base}" x2="{ml + plot_w}" y2="{y_base}" '
        f'stroke="#374151" stroke-width="1.2"/>'
    )

    return NotStr(
        f'<svg width="100%" height="{h}" viewBox="0 0 {w} {h}" '
        f'style="display:block">{"".join(parts)}</svg>'
    )
