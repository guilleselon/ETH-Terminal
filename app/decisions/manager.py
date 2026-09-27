"""
Decision lifecycle management.

State flow:
    waiting  →  in_zone  →  tp_hit / sl_hit
                waiting  →  tp_hit / sl_hit  (if price jumps over the zone)

Every relevant state change triggers a notification (only once).
"""

import uuid
from datetime import datetime, timezone

from app.decisions.storage import (
    load_decisions, save_decisions,
)
from app.logger import get_logger

log = get_logger(__name__)


# ============================================================
#  Pin / Unpin
# ============================================================
def pin_decision(zone_type, zone, price):
    """
    Pin a zone as a user decision.

    Args:
        zone_type: "tactical" or "accumulation"
        zone:      dict with optimal_low/high/mid, stop_loss, take_profit, rr_ratio
        price:     current price

    Returns:
        (True, id)     → decision created
        (False, error) → already an active one of the same type
    """
    decisions = load_decisions()

    # Do not allow 2 active decisions of the same type
    for d in decisions:
        if d.get("type") == zone_type and d.get("status") in ("waiting", "in_zone"):
            return False, "Already an active decision of this type"

    now = datetime.now(timezone.utc).isoformat()
    decision = {
        "id": str(uuid.uuid4())[:8],
        "type": zone_type,
        "pinned_at": now,
        "last_checked": now,
        "price_at_pin": price,
        "entry_low": zone["optimal_low"],
        "entry_high": zone["optimal_high"],
        "entry_mid": zone["optimal_mid"],
        "stop_loss": zone["stop_loss"],
        "take_profit": zone["take_profit"],
        "rr": zone["rr_ratio"],
        "status": "waiting",
        "result_pct": None,
        "notified": [],
    }
    decisions.append(decision)
    save_decisions(decisions)

    log.info(f"Decision pinned: {zone_type} id={decision['id']} "
             f"entry ${zone['optimal_mid']:,.0f}")
    return True, decision["id"]


def unpin_decision(decision_id):
    """Remove a decision by id."""
    decisions = load_decisions()
    before = len(decisions)
    decisions = [d for d in decisions if d.get("id") != decision_id]
    save_decisions(decisions)

    if len(decisions) < before:
        log.info(f"Decision removed: id={decision_id}")
        return True
    return False


# ============================================================
#  Status updates
# ============================================================
def _compute_new_status(decision, current_price):
    """Determine the new status from the current price."""
    if current_price <= decision["stop_loss"]:
        return "sl_hit"
    if current_price >= decision["take_profit"]:
        return "tp_hit"
    if decision["entry_low"] <= current_price <= decision["entry_high"]:
        return "in_zone"
    return "waiting"


def update_decision_status(decision, current_price):
    """
    Update a decision in-place according to the current price.
    Fires a notification if it changes to in_zone / tp_hit / sl_hit.
    """
    if decision.get("status") in ("tp_hit", "sl_hit", "expired"):
        return decision

    old_status = decision["status"]
    new_status = _compute_new_status(decision, current_price)

    if new_status != old_status:
        decision["status"] = new_status

        # Compute the result when closing
        if new_status in ("tp_hit", "sl_hit"):
            if new_status == "tp_hit":
                decision["result_pct"] = (decision["take_profit"] / decision["price_at_pin"] - 1) * 100
            else:
                decision["result_pct"] = (decision["stop_loss"] / decision["price_at_pin"] - 1) * 100

        # Notify only the first time for each event
        notified = decision.get("notified", [])
        if new_status in ("in_zone", "tp_hit", "sl_hit") and new_status not in notified:
            _safe_notify(decision, new_status, current_price)
            notified.append(new_status)
            decision["notified"] = notified

    decision["last_checked"] = datetime.now(timezone.utc).isoformat()
    return decision


def _safe_notify(decision, event, current_price):
    """Send notification without breaking if Telegram is not available."""
    try:
        from app.notifications.telegram import notify_event
        notify_event(decision, event, current_price)
    except Exception as e:
        log.warning(f"Notification failed ({event}): {type(e).__name__}: {e}")


def refresh_decisions(current_price):
    """
    Recompute the status of all decisions with the current price
    and persist the changes.

    Returns:
        full list of decisions (active + closed)
    """
    decisions = load_decisions()
    for d in decisions:
        update_decision_status(d, current_price)
    save_decisions(decisions)
    return decisions
