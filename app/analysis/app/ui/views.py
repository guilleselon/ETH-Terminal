"""
Main views.

    view_landing         → initial loading screen (logo + spinner)
    render_topbar        → topbar with logo + CMC badge + Refresh button
    view_mercado_shell   → shell with skeletons (kept for compatibility)
    view_mercado_data    → final HTML with data (served via HTMX)
"""

from fasthtml.common import (
    Div, Span, A, P, H2, Table, Thead, Tbody, Tr, Th, Td, Ul, Li, B, Button, NotStr,
)

from app.config import (
    EXCHANGE_NAME,
    ZONE_FAR_THRESHOLD_PCT,
)
from app.logger import get_logger
from app.sources.cmc import (
    fetch_cmc_full,
    fetch_global_metrics,
    fetch_fear_greed,
)
from app.sources.exchange import fetch_ohlcv
from app.analysis.momentum import analyze_momentum
from app.analysis.volume import compute_volume_analysis
from app.analysis.zones import (
    compute_tactical_zone, compute_buy_zones, apply_momentum_shift,
)
from app.analysis.snapshot import (
    build_snapshot, process_snapshot, get_history, detect_material_changes,
)
from app.decisions.storage import load_decisions
from app.decisions.manager import refresh_decisions
from app.notifications.telegram import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from app.ui.components import (
    money, money_compact, time_ago, kpi, build_rr_meta, wrap_data_container,
    render_global_context,
)
from app.ui.charts import candlestick_svg, volume_svg

log = get_logger(__name__)


# ════════════════════════════════════════════════════════════
#  In-memory cache (avoids refetch on /pin and /unpin)
# ════════════════════════════════════════════════════════════
_CACHE = {
    "filled": False,
    "candles": None,
    "cmc": None,
    "cmc_err": None,
    "global_metrics": None,
    "fear_greed": None,
    "price": None,
    "vol24h": None,
    "chg24h": None,
    "vol": None,
    "tactical": None,
    "accumulation": None,
    "momentum": None,
    "shift_pct": 0.0,
}


def _cache_clear():
    _CACHE["filled"] = False


# ════════════════════════════════════════════════════════════
#  LANDING — initial loading screen
# ════════════════════════════════════════════════════════════
def view_landing():
    """
    Loading screen shown before the app.

    - Occupies the full viewport
    - Large logo + spinner + text
    - Triggers /warmup in the background (HTMX)
    - When /warmup responds, HTMX redirects to /app
    """
    return Div(
        Div(
            Div(
                Div("ETH", Span("Terminal"), cls="landing-logo"),
                Div("Technical analyzer · ETH/USDT", cls="landing-subtitle"),
                cls="landing-header",
            ),
            Div(
                Div(cls="landing-spinner"),
                Div("Loading market data...", cls="landing-text"),
                Div("Candles · Momentum · Zones · Volume", cls="landing-hint"),
                cls="landing-status",
            ),
            # HTMX trigger: fires /warmup when the page loads
            Div(
                hx_get="/warmup",
                hx_trigger="load",
                hx_swap="none",
                style="display:none",
            ),
            cls="landing-inner",
        ),
        cls="landing",
    )


# ════════════════════════════════════════════════════════════
#  Topbar
# ════════════════════════════════════════════════════════════
def render_topbar():
    """
    Top bar of the app:
        - Left:  logo "ETH Terminal · Market"
        - Right: CMC credits badge + Refresh button
    """
    from app.ui.components import credits_badge, refresh_button

    return Div(
        Div(
            Div("ETH", Span("Terminal"), cls="brand"),
            Span("· Market", cls="tag"),
        ),
        Div(
            credits_badge(),
            refresh_button(),
            cls="topbar-actions",
            id="topbar-actions",
        ),
        cls="topbar",
    )


# ════════════════════════════════════════════════════════════
#  Shell (kept for compatibility)
# ════════════════════════════════════════════════════════════
def view_mercado_shell():
    """Skeleton shell. No longer used in the main flow."""
    return Div(
        H2("Market ETH/USDT"),
        Div(
            Div(
                Div(cls="loading-spinner"),
                Span("Loading market data — prices, candles, momentum and analysis…"),
                cls="loading-banner",
            ),
            Div(
                Div(Div(cls="skeleton-line w30"),
                    Div(cls="skeleton-line w70"),
                    Div(cls="skeleton-line w50"),
                    cls="skeleton-card"),
                Div(Div(cls="skeleton-line w30"),
                    Div(cls="skeleton-line h60"),
                    cls="skeleton-card"),
                Div(Div(cls="skeleton-line w30"),
                    Div(cls="skeleton-line h120"),
                    cls="skeleton-card"),
            ),
            id="data-container",
            hx_get="/data",
            hx_trigger="load",
            hx_swap="outerHTML",
        ),
    )


# ════════════════════════════════════════════════════════════
#  Render by section
# ════════════════════════════════════════════════════════════
def _render_changes_banner(changes):
    real_changes = [c for c in changes if c != "First snapshot saved"]
    if not real_changes:
        return ""
    return Div(
        Div("📢 Changes since last session", cls="changes-banner-title"),
        Ul(*[Li(c) for c in real_changes], cls="changes-list"),
        cls="changes-banner",
    )


def _render_momentum_card(momentum, cmc, shift_pct, acc_is_far):
    if not momentum:
        return "", ""

    def mom_item(label, val):
        if val is None:
            return Div(Div(label, cls="mom-period"),
                       Div("—", cls="mom-val neu"), cls="mom-item")
        cls = "pos" if val > 0 else "neg" if val < 0 else "neu"
        sign = "+" if val > 0 else ""
        return Div(Div(label, cls="mom-period"),
                   Div(f"{sign}{val:.2f}%", cls=f"mom-val {cls}"), cls="mom-item")

    horizons = (
        f"Short: {'+' if momentum['short_avg'] > 0 else '−'}"
        f"{abs(momentum['short_avg']):.1f}%  ·  "
        f"Medium: {'+' if momentum['medium_avg'] > 0 else '−'}"
        f"{abs(momentum['medium_avg']):.1f}%  ·  "
        f"Long: {'+' if momentum['long_avg'] > 0 else '−'}"
        f"{abs(momentum['long_avg']):.1f}%"
    )

    zone_adj_note = ""
    if shift_pct != 0:
        direction = "down" if shift_pct < 0 else "up"
        zone_adj_note = f"Zone adjusted {shift_pct:+.2f}% ({direction}) by momentum"

    advice_text = momentum["advice_far"] if acc_is_far else momentum["advice"]

    grid_items = []
    if cmc:
        grid_items = [
            mom_item("1h", cmc.get("chg1h")),
            mom_item("24h", cmc.get("chg24h")),
            mom_item("7d", cmc.get("chg7d")),
            mom_item("30d", cmc.get("chg30d")),
            mom_item("60d", cmc.get("chg60d")),
            mom_item("90d", cmc.get("chg90d")),
        ]

    card = Div(
        Div("Momentum multi-period · CoinMarketCap", cls="card-title"),
        Div(*grid_items, cls="mom-grid") if grid_items else "",
        Div(
            Div(momentum["label"], cls=f"mom-verdict mom-{momentum['class']}"),
            Div(advice_text, cls="mom-advice"),
            Div(horizons, cls="mom-horizons"),
            style="margin-top:16px;padding-top:16px;border-top:1px solid #1f2937",
        ),
        cls="card",
        style="margin-bottom:20px",
    )
    return card, zone_adj_note


def _render_volume_card(vol):
    if not vol:
        return ""

    obv_color = ("vol-high" if vol["obv_signal"] == "accumulation"
                 else "vol-low" if vol["obv_signal"] == "distribution"
                 else "vol-normal")
    vol_level_cls = {"Very high": "vol-high", "High": "vol-high",
                     "Normal": "vol-normal", "Low": "vol-low",
                     "Very low": "vol-low"}.get(vol["vol_level"], "vol-normal")

    climax_info = "—"
    climax_sub = ""
    if vol.get("climax_low"):
        climax_info = money(vol["climax_low"], 0)
        days = vol.get("climax_days_ago")
        climax_sub = f"{days}d ago · {vol['climax_vol']/vol['vol_30d_avg']:.1f}x average"

    contradiction_block = ""
    if vol.get("vol_contradiction"):
        contradiction_block = Div(vol["vol_contradiction"], cls="vol-contradiction")

    return Div(
        Div("Volume analysis", cls="card-title"),
        Div(
            Div(Div("Last closed candle", cls="vol-item-lbl"),
                Div(money_compact(vol["vol_last_closed"]),
                    cls=f"vol-item-val {vol_level_cls}"),
                Div(f"{vol['vol_ratio_7d']:.2f}x 7d average", cls="vol-item-sub"),
                cls="vol-item"),
            Div(Div("7d average (closed)", cls="vol-item-lbl"),
                Div(money_compact(vol["vol_7d_avg"]), cls="vol-item-val"),
                Div("short reference", cls="vol-item-sub"),
                cls="vol-item"),
            Div(Div("30d average (closed)", cls="vol-item-lbl"),
                Div(money_compact(vol["vol_30d_avg"]), cls="vol-item-val"),
                Div("medium reference", cls="vol-item-sub"),
                cls="vol-item"),
            Div(Div("Level", cls="vol-item-lbl"),
                Div(vol["vol_level"], cls=f"vol-item-val {vol_level_cls}"),
                Div("vs 7d average", cls="vol-item-sub"),
                cls="vol-item"),
            cls="vol-grid",
        ),
        Div(vol["vol_note"], cls="vol-advice", style="margin-top:16px"),
        contradiction_block,
        Div(
            Div(Div("OBV (14d)", cls="vol-signal-lbl"),
                Div(vol["obv_signal"].capitalize(), cls=f"vol-signal-val {obv_color}"),
                Div(f"slope {vol['obv_slope_pct']:+.1f}%", cls="vol-signal-note")),
            Div(Div("Volume POC (90d)", cls="vol-signal-lbl"),
                Div(money(vol["poc_price"], 0), cls="vol-signal-val"),
                Div("price with most volume", cls="vol-signal-note")),
            Div(Div("Value Area (70%)", cls="vol-signal-lbl"),
                Div(f"{money(vol['va_low'], 0)} – {money(vol['va_high'], 0)}",
                    cls="vol-signal-val", style="font-size:13px"),
                Div("zone of highest activity", cls="vol-signal-note")),
            Div(Div("Climax low", cls="vol-signal-lbl"),
                Div(climax_info, cls="vol-signal-val"),
                Div(climax_sub or "no recent capitulation", cls="vol-signal-note")),
            cls="vol-signals",
        ),
        cls="card",
        style="margin-bottom:20px",
    )


def _render_decisions_card(decisions, price):
    active = [d for d in decisions if d.get("status") in ("waiting", "in_zone")]
    closed = sorted(
        [d for d in decisions if d.get("status") in ("tp_hit", "sl_hit")],
        key=lambda d: d.get("last_checked", ""), reverse=True,
    )[:3]

    if not active and not closed:
        return ""

    items = []

    for d in active:
        zone_label = "Tactical" if d["type"] == "tactical" else "Accumulation"
        status_labels = {"waiting": "Waiting for price", "in_zone": "IN ZONE"}
        status_label = status_labels.get(d["status"], d["status"])
        dist = (d["entry_mid"] / price - 1) * 100

        items.append(Div(
            Div(
                Div(f"📌 {zone_label}", cls="decision-title"),
                Div(
                    Div(status_label, cls=f"decision-status {d['status']}"),
                    A("✕ Unpin",
                      href=f"/unpin/{d['id']}",
                      cls="unpin-btn",
                      hx_get=f"/unpin/{d['id']}",
                      hx_target="#data-container",
                      hx_swap="outerHTML"),
                    cls="decision-header-right",
                ),
                cls="decision-header",
            ),
            Div(
                Div(Div("Entry", cls="decision-item-lbl"),
                    Div(f"{money(d['entry_low'], 0)}–{money(d['entry_high'], 0)}",
                        cls="decision-item-val")),
                Div(Div("SL / TP", cls="decision-item-lbl"),
                    Div(f"{money(d['stop_loss'], 0)} / {money(d['take_profit'], 0)}",
                        cls="decision-item-val")),
                Div(Div("R:R", cls="decision-item-lbl"),
                    Div(f"1:{d['rr']:.1f}", cls="decision-item-val")),
                Div(Div("Dist. to entry", cls="decision-item-lbl"),
                    Div(f"{dist:+.2f}%", cls="decision-item-val")),
                cls="decision-grid",
            ),
            Div(f"Pinned {time_ago(d['pinned_at'])} · "
                f"price at pin {money(d['price_at_pin'], 0)}",
                cls="decision-pin-info"),
            cls="decision-card",
        ))

    for d in closed:
        zone_label = "Tactical" if d["type"] == "tactical" else "Accumulation"
        status_labels = {"tp_hit": "TP reached", "sl_hit": "SL hit"}
        status_label = status_labels.get(d["status"], d["status"])
        result = d.get("result_pct")
        result_str = f"{result:+.1f}%" if result is not None else "—"

        items.append(Div(
            Div(
                Div(f"✓ {zone_label}", cls="decision-title"),
                Div(Div(status_label, cls=f"decision-status {d['status']}"),
                    cls="decision-header-right"),
                cls="decision-header",
            ),
            Div(
                Div(Div("Entry average", cls="decision-item-lbl"),
                    Div(money(d['entry_mid'], 0), cls="decision-item-val")),
                Div(Div("Result", cls="decision-item-lbl"),
                    Div(result_str, cls="decision-item-val")),
                cls="decision-grid",
                style="grid-template-columns: repeat(2, 1fr);",
            ),
            Div(f"Resolved {time_ago(d['last_checked'])}", cls="decision-pin-info"),
            cls="decision-card",
            style="opacity: 0.75;",
        ))

    return Div(
        Div("Pinned decisions", cls="card-title"),
        *items,
        cls="card",
        style="margin-bottom:20px",
    )


def _render_zone_card(zone_type, zone, price, decisions, zone_adj_note, acc_is_far):
    """Render a zone (tactical or accumulation) with its card and pin button."""
    is_tactical = (zone_type == "tactical")

    if is_tactical:
        dist = zone["distance_pct"]
        members = zone["members"]
        title = "⚡ Tactical entry · short term"
        card_cls = "zone-card tactical"
        distance_hint = ""
    else:
        dist = (zone["optimal_mid"] / price - 1) * 100
        members = zone["zone_members"]
        card_cls = f"zone-card accumulation" + (" distant" if acc_is_far else "")
        title = ("🏦 Accumulation if a deep pullback occurs"
                 if acc_is_far else "🎯 Optimal accumulation zone")
        distance_hint = ""
        if acc_is_far:
            distance_hint = Div(
                f"Zone {abs(dist):.1f}% away from the current price. "
                f"Reference for long-term accumulation — not an immediate buy signal.",
                cls="distance-hint",
            )

    members_badges = Div(
        Span("Confluence:", cls="zone-members-lbl"),
        *[Span(m, cls="zone-member-badge") for m in members],
        cls="zone-members",
    )

    already_pinned = any(
        d["type"] == zone_type and d.get("status") in ("waiting", "in_zone")
        for d in decisions
    )

    if already_pinned:
        label = "tactical" if is_tactical else "accumulation"
        pin_block = Div(f"✓ You already have an active {label} decision", cls="pinned-note")
    else:
        pin_block = A("🔒 Pin this zone as a decision",
                      href="#", cls="pin-btn",
                      hx_post=f"/pin/{zone_type}",
                      hx_target="#data-container",
                      hx_swap="outerHTML")

    return Div(
        Div(title, cls="zone-label"),
        Div(f"{money(zone['optimal_low'], 0)} – {money(zone['optimal_high'], 0)}",
            cls="zone-prices"),
        Div(f"{dist:+.2f}% from the current price ({money(price, 0)})",
            cls=f"zone-distance {'neg' if dist < 0 else 'pos'}"),
        Div(zone_adj_note, cls="zone-adj-note") if zone_adj_note else "",
        distance_hint,
        members_badges,
        build_rr_meta(zone),
        pin_block,
        cls=card_cls,
    )


def _render_scenarios_card(tactical, accumulation, dist_acc):
    scenarios = []
    if tactical:
        scenarios.append(("Tactical", tactical["optimal_mid"], tactical["distance_pct"],
                          "Short-term entry if the price pulls back a bit"))
    if accumulation:
        scenarios.append(("Accumulation", accumulation["optimal_mid"], dist_acc,
                          "Long-term zone with the most confluence"))

    rows = [Tr(
        Td(B(s[0])), Td(money(s[1], 0)),
        Td(Span(f"{s[2]:+.2f}%", cls="pos" if s[2] < 0 else "neg")),
        Td(Span(s[3], style="color:#9ca3af;font-size:12px")),
    ) for s in scenarios]

    return Div(
        Div("Entry scenarios", cls="card-title"),
        Table(Thead(Tr(Th("Type"), Th("Price"), Th("Δ% vs current"), Th("When to use"))),
              Tbody(*rows)),
        cls="card",
        style="margin-bottom:20px",
    )


def _render_chart_card(candles, tactical, accumulation, vol):
    return Div(
        Div(Div(f"Candles 90d · ETH/USDT ({EXCHANGE_NAME.capitalize()})",
                cls="card-title", style="margin:0"),
            Span("yellow border = ongoing candle", cls="chart-hint"),
            cls="chart-title-row"),
        Div(candlestick_svg(candles, tactical=tactical, accumulation=accumulation),
            style="margin-bottom:4px"),
        Div(
            Div(Div(style="background:#3b82f6;width:18px;height:3px;border-radius:2px"),
                Span("Tactical zone"), cls="chart-legend-item"),
            Div(Div(style="background:#60a5fa;width:18px;height:3px;border-radius:2px"),
                Span("Tactical TP"), cls="chart-legend-item"),
            Div(Div(style="background:#f87171;width:18px;height:3px;border-radius:2px"),
                Span("Tactical SL"), cls="chart-legend-item"),
            Div(Div(style="background:#22c55e;width:18px;height:3px;border-radius:2px"),
                Span("Accumulation zone"), cls="chart-legend-item"),
            Div(Div(style="background:#3b82f6;width:18px;height:3px;border-radius:2px;opacity:0.7"),
                Span("Accumulation TP"), cls="chart-legend-item"),
            Div(Div(style="background:#dc2626;width:18px;height:3px;border-radius:2px"),
                Span("Accumulation SL"), cls="chart-legend-item"),
            cls="chart-legend",
        ),
        Div(
            Div(Div("Volume", cls="card-title", style="margin:0"),
                Span("yellow line = 7d average · circle = climax low", cls="chart-hint"),
                cls="chart-title-row", style="margin-top:16px"),
            volume_svg(candles, vol_analysis=vol),
        ),
        cls="card",
    )


def _render_history_card():
    history_data = get_history()
    items = []
    if len(history_data) >= 2:
        for i in range(len(history_data) - 1, max(0, len(history_data) - 6), -1):
            older = history_data[i - 1]
            newer = history_data[i]
            changes = detect_material_changes(older, newer)
            real = [c for c in changes if c != "First snapshot saved"]
            if real:
                items.append((newer["timestamp"], real))

    if not items:
        return ""

    rows = [
        Div(
            Div(time_ago(ts), cls="history-time"),
            Div(*[Div(c, cls="change-item") for c in chs], cls="history-changes"),
            cls="history-row",
        )
        for ts, chs in items
    ]

    return Div(
        Div("Change history", cls="card-title"),
        *rows,
        cls="card",
        style="margin-bottom:20px",
    )


def _render_topbar_oob():
    """Right topbar with hx-swap-oob to update out-of-band."""
    from app.ui.components import credits_badge, refresh_button

    return Div(
        credits_badge(),
        refresh_button(),
        cls="topbar-actions",
        id="topbar-actions",
        hx_swap_oob="true",
    )


# ════════════════════════════════════════════════════════════
#  DATA — main render
# ════════════════════════════════════════════════════════════
def view_mercado_data(use_cache=False):
    """
    Return the full HTML with all data.

    Args:
        use_cache: if True, reuse the analysis in _CACHE without refetching
    """
    if use_cache and _CACHE["filled"]:
        cmc = _CACHE["cmc"]
        cmc_err = _CACHE["cmc_err"]
        global_metrics = _CACHE["global_metrics"]
        fear_greed = _CACHE["fear_greed"]
        candles = _CACHE["candles"]
        price = _CACHE["price"]
        vol24h = _CACHE["vol24h"]
        chg24h = _CACHE["chg24h"]
        vol = _CACHE["vol"]
        tactical = _CACHE["tactical"]
        accumulation = _CACHE["accumulation"]
        momentum = _CACHE["momentum"]
        shift_pct = _CACHE["shift_pct"]
        changes = []
    else:
        # ── Fetch from external sources ──
        cmc, cmc_err = fetch_cmc_full("ETH")
        global_metrics, _ = fetch_global_metrics()
        fear_greed, _ = fetch_fear_greed()
        candles, ccxt_err = fetch_ohlcv()

        if candles is None:
            return wrap_data_container(
                Div(f"⚠️ Could not load candles: {ccxt_err}", cls="error-banner"),
                P(f"Configured exchange: {EXCHANGE_NAME}", cls="sub"),
                P("Check your connection and that CCXT is installed: pip install ccxt",
                  cls="sub"),
            )

        closes = [c["c"] for c in candles]

        if cmc and cmc.get("price"):
            price = cmc["price"]
            vol24h = cmc.get("vol24h") or 0
        else:
            price = closes[-1]
            vol24h = 0

        # ── Analysis ──
        vol = compute_volume_analysis(candles)
        tactical = compute_tactical_zone(candles)
        accumulation = compute_buy_zones(candles, vol_analysis=vol)

        if accumulation is None:
            return wrap_data_container(
                Div("⚠️ Not enough data to compute buy zones.",
                    cls="error-banner"),
            )

        momentum = analyze_momentum(cmc)
        accumulation, shift_pct = apply_momentum_shift(accumulation, momentum)

        chg24h = cmc.get("chg24h") if cmc else None
        if chg24h is None and len(closes) >= 2:
            chg24h = (closes[-1] / closes[-2] - 1) * 100

        # ── Snapshot + diff ──
        snapshot = build_snapshot(
            price,
            tactical,
            accumulation if accumulation.get("confidence_count", 0) > 0 else None,
            momentum,
            vol,
        )
        changes = process_snapshot(snapshot)

        # ── Update cache ──
        _CACHE.update({
            "filled": True,
            "candles": candles,
            "cmc": cmc,
            "cmc_err": cmc_err,
            "global_metrics": global_metrics,
            "fear_greed": fear_greed,
            "price": price,
            "vol24h": vol24h,
            "chg24h": chg24h,
            "vol": vol,
            "tactical": tactical,
            "accumulation": accumulation,
            "momentum": momentum,
            "shift_pct": shift_pct,
        })

    # ── Refresh decisions ──
    decisions = refresh_decisions(price)

    has_tactical = tactical is not None and len(tactical.get("members", [])) >= 2
    has_accumulation = accumulation.get("confidence_count", 0) > 0

    dist_acc = (accumulation["optimal_mid"] / price - 1) * 100 if has_accumulation else 0
    acc_is_far = abs(dist_acc) > ZONE_FAR_THRESHOLD_PCT

    # ── Render by section ──
    changes_card = _render_changes_banner(changes)

    momentum_card, zone_adj_note = _render_momentum_card(
        momentum, cmc, shift_pct, acc_is_far
    )

    volume_card = _render_volume_card(vol)

    decisions_card = _render_decisions_card(decisions, price)

    global_context_card = render_global_context(global_metrics, fear_greed)

    tactical_card = ""
    if has_tactical:
        tactical_card = _render_zone_card(
            "tactical", tactical, price, decisions, zone_adj_note, False
        )

    if has_accumulation:
        accumulation_card = _render_zone_card(
            "accumulation", accumulation, price, decisions, zone_adj_note, acc_is_far
        )
    else:
        accumulation_card = Div(
            Div("⚠️ No clear accumulation zone", cls="zone-label"),
            Div("Market at highs — no long-term supports below",
                cls="zone-prices", style="font-size:20px"),
            cls="zone-card no-zone",
        )

    zones_explainer = Div(
        NotStr("<strong>Two zones depending on your horizon:</strong> "
               "the <span style='color:#93c5fd'>tactical zone</span> (blue) is for "
               "short-term entries (1-3 days) — 7-20 day supports. "
               "The <span style='color:#86efac'>accumulation zone</span> (green) "
               "is for long positions — 90-day supports."),
        cls="zones-explainer",
    )

    scenarios_card = _render_scenarios_card(
        tactical if has_tactical else None,
        accumulation if has_accumulation else None,
        dist_acc,
    )

    chart_card = _render_chart_card(
        candles,
        tactical if has_tactical else None,
        accumulation if has_accumulation else None,
        vol,
    )

    history_card = _render_history_card()

    cmc_banner = ""
    if cmc_err:
        cmc_banner = Div(f"ℹ️ CMC unavailable: {cmc_err}", cls="info-banner")

    # ── Main content of #data-container ──
    main_content = wrap_data_container(
        cmc_banner,
        changes_card,
        Div(
            kpi("ETH Price", money(price, 2),
                f"{chg24h:+.2f}% 24h" if chg24h is not None else "— 24h",
                "pos" if (chg24h or 0) > 0 else "neg" if (chg24h or 0) < 0 else "neu"),
            kpi("24h Volume (CMC)", money_compact(vol24h),
                "CoinMarketCap", "neu"),
            cls="grid kpis",
        ),
        global_context_card,
        decisions_card,
        momentum_card,
        volume_card,
        zones_explainer,
        tactical_card,
        accumulation_card,
        scenarios_card,
        Div(chart_card, style="margin-bottom:20px"),
        history_card,
    )

    # ── OOB: updated topbar (credits badge + refresh button) ──
    return main_content, _render_topbar_oob()
