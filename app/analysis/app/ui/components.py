"""Reusable UI helpers."""

from datetime import datetime, timezone
from fasthtml.common import Div, Span, Button


# ============================================================
#  Formatting
# ============================================================
def money(v, digits=2):
    """Format a number as $X,XXX.XX"""
    try:
        return f"${v:,.{digits}f}"
    except (TypeError, ValueError):
        return "$0.00"


def money_compact(v):
    """Format large numbers: $14.2B, $850M, $75K"""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    if v >= 1e9:
        return f"${v/1e9:.2f}B"
    if v >= 1e6:
        return f"${v/1e6:.1f}M"
    if v >= 1e3:
        return f"${v/1e3:.1f}K"
    return f"${v:.0f}"


def time_ago(iso_str):
    """Convert an ISO timestamp into 'Xm/h/d ago'."""
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        secs = delta.total_seconds()
        if secs < 60:
            return "seconds ago"
        if secs < 3600:
            return f"{int(secs/60)}m ago"
        if secs < 86400:
            return f"{int(secs/3600)}h ago"
        return f"{int(secs/86400)}d ago"
    except Exception:
        return "—"


# ============================================================
#  Composite components
# ============================================================
def kpi(label, value, delta, cls):
    """KPI card: label + value + colored delta."""
    return Div(
        Div(label, cls="kpi-label"),
        Div(value, cls="kpi-value"),
        Div(delta, cls=f"kpi-delta {cls}"),
        cls="card",
    )


def build_rr_meta(zone):
    """
    STOP/TP/R:R block for a zone.
    If R:R is not viable (< 1.5), shows "no realistic target".
    If TP is near the current price, adds a context note.
    """
    if not zone.get("rr_viable", True):
        return Div(
            Div(Div("STOP LOSS", cls="zone-meta-lbl"),
                Div(money(zone["stop_loss"], 0), cls="zone-meta-val sl"),
                cls="zone-meta-item"),
            Div(Div("TAKE PROFIT", cls="zone-meta-lbl"),
                Div("—", cls="zone-meta-val", style="color:#6b7280"),
                Div("no realistic target", cls="rr-tag"),
                cls="zone-meta-item"),
            Div(Div("R:R RATIO", cls="zone-meta-lbl"),
                Div("—", cls="zone-meta-val", style="color:#6b7280"),
                Div("below 1:1.5", cls="rr-tag"),
                cls="zone-meta-item"),
            cls="zone-meta",
        )

    context_note = ""
    if zone.get("tp_near_current", False):
        net = zone.get("net_return_from_current_pct", 0)
        sign = "+" if net > 0 else ""
        context_note = Div(
            f"⚠️ The R:R 1:{zone['rr_ratio']:.1f} requires a full cycle: "
            f"drop down to the zone and then rise up to the TP. Net return from "
            f"the current price: {sign}{net:.1f}%.",
            cls="rr-context-note",
        )

    return Div(
        Div(Div("STOP LOSS", cls="zone-meta-lbl"),
            Div(money(zone["stop_loss"], 0), cls="zone-meta-val sl"),
            cls="zone-meta-item"),
        Div(Div("TAKE PROFIT", cls="zone-meta-lbl"),
            Div(money(zone["take_profit"], 0), cls="zone-meta-val tp"),
            cls="zone-meta-item"),
        Div(Div("R:R RATIO", cls="zone-meta-lbl"),
            Div(f"1 : {zone['rr_ratio']:.1f}", cls="zone-meta-val rr"),
            cls="zone-meta-item"),
        context_note,
        cls="zone-meta",
    )


def wrap_data_container(*content):
    """Wrap content in the div that HTMX replaces."""
    return Div(*content, id="data-container")


# ============================================================
#  CMC credits counter
# ============================================================
def credits_badge():
    """
    Compact badge showing the number of remaining CMC API calls.

    Format: 📊 API: {remaining}/{total} · {today} today

    Color based on the percentage used this month (inverted):
        < 50% used   → green  (plenty of credits left)
        < 80% used   → yellow (getting low)
        >= 80% used  → red    (almost exhausted)
    """
    from app.config import CMC_CREDITS_MONTHLY
    from app.sources.cmc_usage import get_usage

    usage = get_usage()
    used = usage["used_this_month"]
    remaining = usage["remaining"]
    today = usage["used_today"]
    pct = usage["percent_used"]

    if pct < 50:
        color_cls = "credits-ok"
    elif pct < 80:
        color_cls = "credits-warn"
    else:
        color_cls = "credits-danger"

    tooltip = (
        f"CoinMarketCap API calls\n"
        f"─────────────────────────────────\n"
        f"Plan:      Basic (free)\n"
        f"Remaining: {remaining:,} / {CMC_CREDITS_MONTHLY:,} ({100 - pct:.2f}%)\n"
        f"Used:      {used:,} this month\n"
        f"Today:     {today}\n"
        f"\n"
        f"Each /data call consumes 1."
    )

    return Div(
        Span("📊", cls="credits-icon"),
        Span("API:", cls="credits-label"),
        Span(f"{remaining:,}/{CMC_CREDITS_MONTHLY:,}", cls=f"credits-count {color_cls}"),
        Span(f"· {today} today", cls="credits-today"),
        cls="credits-badge",
        title=tooltip,
    )


# ============================================================
#  Refresh button
# ============================================================
def refresh_button():
    """
    Manual refresh button via HTMX.

    Triggers /refresh, which invalidates the cache and does a full fetch.
    While loading, shows a spinner and disables clicking.
    """
    return Button(
        Span(cls="refresh-spinner"),
        Span("🔄", cls="refresh-icon"),
        Span("Refresh", cls="refresh-text"),
        cls="refresh-btn",
        hx_get="/refresh",
        hx_target="#data-container",
        hx_swap="outerHTML",
        hx_indicator="this",
        title="Force a full refresh (consumes 1 CMC credit)",
    )


# ============================================================
#  Global market context
# ============================================================
def render_global_context(global_metrics, fear_greed):
    """
    Block with macro market context.

    Args:
        global_metrics: dict or None
        fear_greed:     dict or None

    Returns:
        Div component or "" if there is no data
    """
    if not global_metrics and not fear_greed:
        return ""

    items = []

    # ── Global metrics ──
    if global_metrics:
        mcap = global_metrics.get("total_market_cap", 0)
        vol = global_metrics.get("total_volume_24h", 0)
        chg = global_metrics.get("market_cap_change_24h", 0)
        btc_dom = global_metrics.get("btc_dominance", 0)
        eth_dom = global_metrics.get("eth_dominance", 0)

        chg_cls = "pos" if chg > 0 else "neg" if chg < 0 else "neu"
        chg_sign = "+" if chg > 0 else ""

        items.append(
            Div(
                Div("Global Market Cap", cls="global-item-lbl"),
                Div(f"${mcap/1e12:.2f}T", cls="global-item-val"),
                Div(f"{chg_sign}{chg:.2f}% 24h", cls=f"global-item-sub {chg_cls}"),
                cls="global-item",
            )
        )

        items.append(
            Div(
                Div("Volume 24h", cls="global-item-lbl"),
                Div(f"${vol/1e9:.1f}B", cls="global-item-val"),
                Div("total market", cls="global-item-sub"),
                cls="global-item",
            )
        )

        items.append(
            Div(
                Div("BTC / ETH Dominance", cls="global-item-lbl"),
                Div(f"{btc_dom:.1f}% / {eth_dom:.1f}%", cls="global-item-val"),
                Div("market share", cls="global-item-sub"),
                cls="global-item",
            )
        )

    # ── Fear & Greed ──
    if fear_greed:
        fg_value = fear_greed.get("value", 50)
        fg_class = fear_greed.get("value_classification", "Neutral")

        # Color based on value
        if fg_value <= 25:
            fg_color_cls = "fg-extreme-fear"
        elif fg_value <= 45:
            fg_color_cls = "fg-fear"
        elif fg_value <= 55:
            fg_color_cls = "fg-neutral"
        elif fg_value <= 75:
            fg_color_cls = "fg-greed"
        else:
            fg_color_cls = "fg-extreme-greed"

        items.append(
            Div(
                Div("Fear & Greed", cls="global-item-lbl"),
                Div(
                    Span(str(fg_value), cls=f"fg-value {fg_color_cls}"),
                    Span("/100", cls="fg-max"),
                ),
                Div(fg_class, cls=f"global-item-sub {fg_color_cls}"),
                cls="global-item",
            )
        )

    return Div(
        Div(
            Span("🌍", cls="global-icon"),
            Span("Market context", cls="global-title"),
            Span("CoinMarketCap", cls="global-source"),
            cls="global-header",
        ),
        Div(*items, cls="global-grid"),
        cls="global-context",
    )
