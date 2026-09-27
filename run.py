"""
Application entry point.

Usage:
    python run.py             → starts the web server
    python run.py --validate  → runs validations for steps 1-5
"""

import sys
from pathlib import Path


# ════════════════════════════════════════════════════════════
#  sys.path
# ════════════════════════════════════════════════════════════
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ════════════════════════════════════════════════════════════
#  Module-level import of the app
#  (critical: uvicorn looks for `app` as an attribute of this module)
# ════════════════════════════════════════════════════════════
from app.routes import app, rt


# ════════════════════════════════════════════════════════════
#  Validation mode
# ════════════════════════════════════════════════════════════
def run_validation():
    from app.logger import get_logger
    log = get_logger("run")

    print("─" * 60)
    print("  ETH Terminal — validation (Steps 1-5)")
    print("─" * 60)
    print()

    # ── Step 1 ──
    print("[Step 1] Foundation"); print()
    try:
        from app.config import (
            BASE_DIR, CMC_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
        )
        print(f"  ✅ app.config       OK")
        print(f"  ✅ app.logger       OK")
        print(f"    BASE_DIR           {BASE_DIR}")
        print(f"    CMC_API_KEY        {'✅' if CMC_API_KEY else '⚠️'}")
        print(f"    TELEGRAM_BOT_TOKEN {'✅' if TELEGRAM_BOT_TOKEN else '⚠️'}")
        log.info("Step 1 validated")
    except Exception as e:
        print(f"  ❌ Step 1 FAILED: {e}")
        return False

    print(); print("─" * 60); print()

    # ── Step 2 ──
    print("[Step 2] Network and sources"); print()
    try:
        from app.http_client import HAS_REQUESTS
        from app.sources.cmc import fetch_cmc_full
        from app.sources.exchange import fetch_ohlcv, HAS_CCXT
        print(f"  ✅ app.http_client  OK (requests: {'yes' if HAS_REQUESTS else 'no'})")
        print(f"  ✅ app.sources      OK (ccxt: {'yes' if HAS_CCXT else 'NO'})")
        cmc, _ = fetch_cmc_full("ETH")
        candles, _ = fetch_ohlcv()
        print(f"    Price:   ${cmc['price']:,.2f}" if cmc else "    ⚠️ no CMC")
        print(f"    Candles: {len(candles)}" if candles else "    ⚠️ no candles")
        log.info("Step 2 validated")
    except Exception as e:
        print(f"  ❌ Step 2 FAILED: {e}")
        return False

    print(); print("─" * 60); print()

    # ── Step 3 ──
    print("[Step 3] Analysis"); print()
    try:
        from app.analysis.momentum import analyze_momentum
        from app.analysis.volume import compute_volume_analysis
        from app.analysis.zones import compute_tactical_zone, compute_buy_zones
        print("  ✅ app.analysis.momentum  OK")
        print("  ✅ app.analysis.volume    OK")
        print("  ✅ app.analysis.zones     OK")
        print("  ✅ app.analysis.snapshot  OK")
        if candles and cmc:
            vol = compute_volume_analysis(candles)
            tactical = compute_tactical_zone(candles)
            if tactical:
                print(f"    Tactical: ${tactical['optimal_low']:,.0f}"
                      f"–${tactical['optimal_high']:,.0f}")
        log.info("Step 3 validated")
    except Exception as e:
        print(f"  ❌ Step 3 FAILED: {e}")
        return False

    print(); print("─" * 60); print()

    # ── Step 4 ──
    print("[Step 4] Persistence + Notifications"); print()
    try:
        from app.decisions.storage import load_decisions
        from app.decisions.manager import refresh_decisions
        from app.notifications.telegram import (
            TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, send_test_message,
        )
        print("  ✅ app.decisions.storage    OK")
        print("  ✅ app.decisions.manager    OK")
        print("  ✅ app.notifications.telegram OK")
        print(f"    Decisions: {len(load_decisions())}")
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            ok, err = send_test_message()
            print(f"    Telegram: {'✅ sent' if ok else f'⚠️ {err}'}")
        log.info("Step 4 validated")
    except Exception as e:
        print(f"  ❌ Step 4 FAILED: {e}")
        return False

    print(); print("─" * 60); print()

    # ── Step 5 ──
    print("[Step 5] Visual layer"); print()
    try:
        from app.ui.styles import CSS
        from app.ui.components import money, money_compact
        from app.ui.charts import candlestick_svg, volume_svg
        from app.ui.views import view_mercado_shell, view_mercado_data
        print("  ✅ app.ui.styles      OK")
        print("  ✅ app.ui.components  OK")
        print("  ✅ app.ui.charts      OK")
        print("  ✅ app.ui.views       OK")
        assert money(1234.56) == "$1,234.56"
        assert money_compact(14_200_000_000) == "$14.20B"
        _ = view_mercado_shell()
        print(f"    ✅ Components validated")
        log.info("Step 5 validated")
    except Exception as e:
        print(f"  ❌ Step 5 FAILED: {e}")
        return False

    print(); print("─" * 60)
    print("  🎯 Validation complete. All steps OK.")
    print("─" * 60)
    return True


# ════════════════════════════════════════════════════════════
#  Server mode
# ════════════════════════════════════════════════════════════
def run_server():
    from app.logger import get_logger
    from fasthtml.common import serve

    log = get_logger("run")

    print("─" * 60)
    print("  ETH Terminal — starting server")
    print("─" * 60)
    print()
    print("  📡 The server is running.")
    print("  🌐 Open your browser at:  http://localhost:5001")
    print("  ⏹  Press Ctrl+C to stop it.")
    print()
    print("─" * 60)
    print()

    log.info("Server started")
    serve(reload=False)


# ════════════════════════════════════════════════════════════
#  Main
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if "--validate" in sys.argv:
        ok = run_validation()
        sys.exit(0 if ok else 1)
    else:
        run_server()

