"""
HTTP routes + HTMX integration.

    /                       Loading landing page (spinner)
    /warmup                 Preloads data and redirects to /app (HTMX)
    /app                    Full app with data already in cache
    /data                   Fresh data (used by HTMX)
    /data-cached            Cached data
    /data-nocache           Fresh data (full refetch)
    /pin/{zone_type}        Pins a zone as a decision (POST)
    /unpin/{id}             Unpins a decision (GET)
    /refresh                Forces a refetch ignoring the cache
"""

from fasthtml.common import (
    fast_app, Title, Div, Main, Span, Style, Response,
)

from app.logger import get_logger
from app.ui.styles import CSS
from app.ui.views import (
    view_landing,
    view_mercado_shell,
    view_mercado_data,
    render_topbar,
    _CACHE,
)
from app.decisions.manager import pin_decision, unpin_decision

log = get_logger(__name__)


# ════════════════════════════════════════════════════════════
#  Initialize the app
# ════════════════════════════════════════════════════════════
app, rt = fast_app(
    pico=False,
    hdrs=(Style(CSS),),
)


# ════════════════════════════════════════════════════════════
#  Landing — initial loading screen
# ════════════════════════════════════════════════════════════
@rt("/")
def get():
    return (
        Title("ETH Terminal"),
        view_landing(),
    )


# ════════════════════════════════════════════════════════════
#  Warmup — preloads data and redirects to /app
# ════════════════════════════════════════════════════════════
@rt("/warmup")
def get():
    """
    HTMX calls here when the landing page loads.

    Performs the full fetch (fills the cache) and responds with
    HX-Redirect: /app → the browser navigates to the app.
    """
    log.info("Warmup started · loading data...")

    # Force a full fetch (fills _CACHE)
    _CACHE["filled"] = False
    view_mercado_data(use_cache=False)

    log.info("Warmup completed · redirecting to /app")

    return Response(
        "",
        headers={"HX-Redirect": "/app"},
    )


# ════════════════════════════════════════════════════════════
#  App — full view with cached data
# ════════════════════════════════════════════════════════════
@rt("/app")
def get():
    """
    Render the full app with data already in cache.
    If for some reason there is no cache, triggers a fetch via HTMX.
    """
    if _CACHE["filled"]:
        content = view_mercado_data(use_cache=True)
    else:
        # Defensive fallback: if entering /app without going through /
        content = Div(
            hx_get="/data-nocache",
            hx_trigger="load",
            hx_swap="outerHTML",
            id="data-container",
        )

    return (
        Title("ETH Terminal · Market"),
        Div(
            render_topbar(),
            Main(content),
            cls="app",
        ),
    )


# ════════════════════════════════════════════════════════════
#  Data — HTMX calls it for refreshes
# ════════════════════════════════════════════════════════════
@rt("/data")
def get():
    return view_mercado_data(use_cache=False)


@rt("/data-cached")
def get():
    return view_mercado_data(use_cache=True)


@rt("/data-nocache")
def get():
    return view_mercado_data(use_cache=False)


# ════════════════════════════════════════════════════════════
#  Pin — pins a zone as a decision
# ════════════════════════════════════════════════════════════
@rt("/pin/{zone_type}")
def post(zone_type: str):
    if zone_type not in ("tactical", "accumulation"):
        log.warning(f"Pin with invalid zone_type: {zone_type}")
        return view_mercado_data(use_cache=_CACHE["filled"])

    if not _CACHE["filled"]:
        view_mercado_data(use_cache=False)

    price = _CACHE.get("price")
    zone = _CACHE.get(zone_type)

    if not price or not zone:
        log.warning(f"Pin without data")
        return view_mercado_data(use_cache=True)

    ok, result = pin_decision(zone_type, zone, price)
    if ok:
        log.info(f"Pin OK: {zone_type} id={result}")
    else:
        log.warning(f"Pin failed: {result}")

    return view_mercado_data(use_cache=True)


# ════════════════════════════════════════════════════════════
#  Unpin — removes a decision
# ════════════════════════════════════════════════════════════
@rt("/unpin/{decision_id}")
def get(decision_id: str):
    if not _CACHE["filled"]:
        view_mercado_data(use_cache=False)

    ok = unpin_decision(decision_id)
    if ok:
        log.info(f"Unpin OK: id={decision_id}")
    else:
        log.warning(f"Unpin failed: id={decision_id} not found")

    return view_mercado_data(use_cache=True)


# ════════════════════════════════════════════════════════════
#  Refresh — clears cache and refetches
# ════════════════════════════════════════════════════════════
@rt("/refresh")
def get():
    _CACHE["filled"] = False
    log.info("Cache invalidated, full refetch")
    return view_mercado_data(use_cache=False)


# ════════════════════════════════════════════════════════════
#  Start scheduler
# ════════════════════════════════════════════════════════════
from app.scheduler import start as _start_scheduler

_start_scheduler()
