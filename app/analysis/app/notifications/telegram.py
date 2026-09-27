"""
Notifications via Telegram Bot API.

Configuration (in .env):
    TELEGRAM_BOT_TOKEN  → bot token (from @BotFather)
    TELEGRAM_CHAT_ID    → your personal or group chat_id

If both variables are empty, functions don't send anything but
they also don't fail.
"""

from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from app.http_client import http_post_json
from app.logger import get_logger

log = get_logger(__name__)

TELEGRAM_API = "https://api.telegram.org"


# ============================================================
#  Basic send
# ============================================================
def send_telegram(message, timeout=5):
    """
    Send a message via Telegram.

    Returns:
        (True, None)   → sent OK
        (False, error) → string describing the failure
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False, "Telegram not configured (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID)"

    url = f"{TELEGRAM_API}/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    response = http_post_json(url, payload, timeout=timeout)

    if response and response.get("ok"):
        log.info(f"Telegram sent OK ({len(message)} chars)")
        return True, None

    err = "invalid response"
    if response:
        err = f"HTTP {response.get('error_code', '?')}: {response.get('description', '')[:200]}"
    log.warning(f"Telegram failed: {err}")
    return False, err


# ============================================================
#  Predefined events
# ============================================================
def notify_event(decision, event, current_price):
    """
    Send a notification for a decision event.

    Args:
        decision:      dict with type, entry_low/high/mid, stop_loss, take_profit, rr, result_pct
        event:         "in_zone" | "tp_hit" | "sl_hit"
        current_price: price at the moment of the event
    """
    zone_label = "Tactical" if decision.get("type") == "tactical" else "Accumulation"
    entry_range = (f"${decision['entry_low']:,.0f}–"
                   f"${decision['entry_high']:,.0f}")

    if event == "in_zone":
        title = "🎯 Price entered the zone"
        body = (
            f"<b>{zone_label} zone</b> reached\n"
            f"Current price: <b>${current_price:,.2f}</b>\n"
            f"Entry range: {entry_range}\n"
            f"SL: ${decision['stop_loss']:,.0f} · "
            f"TP: ${decision['take_profit']:,.0f}\n"
            f"R:R 1:{decision.get('rr', 0):.1f}"
        )
    elif event == "tp_hit":
        title = "✅ Take Profit reached"
        result = decision.get("result_pct") or 0
        body = (
            f"<b>{zone_label} zone</b> reached TP\n"
            f"Current price: <b>${current_price:,.2f}</b>\n"
            f"Entry average: ${decision['entry_mid']:,.0f}\n"
            f"TP: ${decision['take_profit']:,.0f}\n"
            f"Result: <b>{result:+.1f}%</b>"
        )
    elif event == "sl_hit":
        title = "❌ Stop Loss hit"
        result = decision.get("result_pct") or 0
        body = (
            f"<b>{zone_label} zone</b> broke SL\n"
            f"Current price: <b>${current_price:,.2f}</b>\n"
            f"Entry average: ${decision['entry_mid']:,.0f}\n"
            f"SL: ${decision['stop_loss']:,.0f}\n"
            f"Result: <b>{result:+.1f}%</b>"
        )
    else:
        log.warning(f"Unknown event: {event}")
        return False, f"Unknown event: {event}"

    message = f"{title}\n\n{body}"
    return send_telegram(message)


# ============================================================
#  Manual test
# ============================================================
def send_test_message():
    """Send a test message to verify the configuration."""
    return send_telegram(
        "🧪 <b>ETH Terminal test</b>\n\n"
        "If you see this message, Telegram is properly configured.\n"
        "You will receive notifications when:\n"
        "• Price enters a zone (🎯)\n"
        "• TP is reached (✅)\n"
        "• SL is breached (❌)"
    )
