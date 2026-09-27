"""
Lightweight scheduler.

A daemon thread that every N seconds:
    1. Fetches the current price via CMC (1 credit)
    2. Updates the status of active decisions
    3. Sends Telegram notifications if there are relevant changes

Does not perform technical analysis — it only checks whether the price
touched a zone, SL or TP.

Lives inside the same web process (daemon thread).
Starts automatically when the app starts if SCHEDULER_ENABLED=true.
"""

import threading
import time
from datetime import datetime, timezone

from app.config import (
    SYMBOL,
    SCHEDULER_ENABLED,
    SCHEDULER_INTERVAL_SECONDS,
)
from app.logger import get_logger
from app.decisions.manager import refresh_decisions
from app.decisions.storage import get_active_decisions
from app.sources.cmc import fetch_price_only

log = get_logger(__name__)

# Internal thread state
_thread = None
_stop_event = threading.Event()

# Last execution metrics (for UI and debugging)
_last_run = {
    "at": None,
    "checked": 0,
    "notified": 0,
    "error": None,
}


# ============================================================
#  Single cycle execution
# ============================================================
def run_once():
    """
    Execute one full check cycle.
    Returns a dict with the metrics of this execution.

    Can be called manually from /check-now if desired.
    """
    now = datetime.now(timezone.utc).isoformat()
    result = {"at": now, "checked": 0, "notified": 0, "error": None}

    try:
        # Base symbol (ETH, not ETH/USDT)
        symbol_base = SYMBOL.split("/")[0]

        # 1. Get price (consumes 1 CMC credit)
        cmc, err = fetch_price_only(symbol_base)
        if not cmc or not cmc.get("price"):
            result["error"] = err or "no price"
            log.warning(f"[scheduler] No price: {result['error']}")
            _last_run.update(result)
            return result

        price = cmc["price"]

        # 2. Count active decisions BEFORE checking
        active_before = get_active_decisions()
        result["checked"] = len(active_before)

        # 3. Update statuses (fires notifications if something changes)
        # refresh_decisions persists the changes and notifies
        refresh_decisions(price)

        log.info(
            f"[scheduler] OK · ${price:,.2f} · "
            f"{len(active_before)} active decisions"
        )

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
        log.error(f"[scheduler] Error: {result['error']}")

    _last_run.update(result)
    return result


# ============================================================
#  Thread loop
# ============================================================
def _loop():
    """Infinite loop until _stop_event is set."""
    log.info(
        f"[scheduler] Starting · interval {SCHEDULER_INTERVAL_SECONDS}s "
        f"({SCHEDULER_INTERVAL_SECONDS//60} min)"
    )

    # Wait 15s initially so the web finishes starting up
    if _stop_event.wait(15):
        log.info("[scheduler] Stopped during startup")
        return

    while not _stop_event.is_set():
        run_once()

        # Wait for the interval or exit earlier if _stop_event is set
        if _stop_event.wait(SCHEDULER_INTERVAL_SECONDS):
            break

    log.info("[scheduler] Stopped")


# ============================================================
#  Public API
# ============================================================
def start():
    """Start the scheduler as a daemon thread. Idempotent."""
    global _thread

    if not SCHEDULER_ENABLED:
        log.info("[scheduler] Disabled (SCHEDULER_ENABLED=false)")
        return False

    if _thread is not None and _thread.is_alive():
        log.warning("[scheduler] Was already running")
        return False

    _stop_event.clear()
    _thread = threading.Thread(target=_loop, name="eth-scheduler", daemon=True)
    _thread.start()
    log.info("[scheduler] Thread launched")
    return True


def stop(timeout=5):
    """Stop the scheduler (clean shutdown)."""
    global _thread
    if _thread is None:
        return
    _stop_event.set()
    _thread.join(timeout=timeout)
    _thread = None
    log.info("[scheduler] Stopped by stop()")


def get_status():
    """Scheduler status for UI or logs."""
    alive = _thread is not None and _thread.is_alive()
    return {
        "enabled": SCHEDULER_ENABLED,
        "alive": alive,
        "interval_seconds": SCHEDULER_INTERVAL_SECONDS,
        "interval_minutes": SCHEDULER_INTERVAL_SECONDS // 60,
        "last_run_at": _last_run.get("at"),
        "last_checked": _last_run.get("checked", 0),
        "last_error": _last_run.get("error"),
    }
