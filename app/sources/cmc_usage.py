"""
Local counter for CoinMarketCap API credits.

CMC does not expose the total credits consumed per month through the
public API, so we keep a local counter persisted in data/cmc_usage.json.

File structure:
    {
      "count_by_month": {"2026-09": 42, ...},
      "count_by_day":   {"2026-09-23": 12, ...},
      "last_call_at":   "2026-09-23T15:30:00+00:00"
    }

Keys are reset automatically when the month or day changes, but the
historical data is preserved for later queries.
"""

import json
import shutil
from datetime import datetime, timezone

from app.config import CMC_CREDITS_MONTHLY, CMC_USAGE_FILE
from app.logger import get_logger

log = get_logger(__name__)


# ============================================================
#  Internal helpers
# ============================================================
def _now():
    return datetime.now(timezone.utc)


def _load():
    """Load the usage file. Returns an empty structure on failure."""
    default = {
        "count_by_month": {},
        "count_by_day": {},
        "last_call_at": None,
    }
    try:
        if not CMC_USAGE_FILE.exists():
            return default
        with open(CMC_USAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in default.items():
            data.setdefault(k, v)
        return data
    except Exception as e:
        log.warning(f"Could not load CMC usage: {e}")
        return default


def _save(data):
    """Atomic write."""
    try:
        tmp = CMC_USAGE_FILE.with_suffix(CMC_USAGE_FILE.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        shutil.move(str(tmp), str(CMC_USAGE_FILE))
    except Exception as e:
        log.warning(f"Could not save CMC usage: {e}")


# ============================================================
#  Public API
# ============================================================
def register_call(credits=1, endpoint="quotes/latest"):
    """
    Register N credits consumed. Call this after every successful
    request to CMC.

    Args:
        credits:  how many credits the call consumed (usually 1)
        endpoint: endpoint name (for future breakdown by type)
    """
    data = _load()
    now = _now()
    month_key = now.strftime("%Y-%m")
    day_key = now.strftime("%Y-%m-%d")

    data["count_by_month"][month_key] = (
        data["count_by_month"].get(month_key, 0) + credits
    )
    data["count_by_day"][day_key] = (
        data["count_by_day"].get(day_key, 0) + credits
    )
    data["last_call_at"] = now.isoformat()

    _save(data)
    return data


def get_usage():
    """
    Return the usage summary for the current month/day.

    Returns:
        dict with:
            month_key         "2026-09"
            used_this_month   N
            remaining         N (limit - used)
            percent_used      float 0..100
            day_key           "2026-09-23"
            used_today        N
            last_call_at      ISO string or None
    """
    data = _load()
    now = _now()
    month_key = now.strftime("%Y-%m")
    day_key = now.strftime("%Y-%m-%d")

    used_month = data["count_by_month"].get(month_key, 0)
    used_day = data["count_by_day"].get(day_key, 0)
    remaining = max(0, CMC_CREDITS_MONTHLY - used_month)
    percent = (used_month / CMC_CREDITS_MONTHLY * 100) if CMC_CREDITS_MONTHLY else 0

    return {
        "month_key": month_key,
        "used_this_month": used_month,
        "remaining": remaining,
        "percent_used": percent,
        "day_key": day_key,
        "used_today": used_day,
        "last_call_at": data.get("last_call_at"),
    }


def get_history(days=30):
    """History of the last N days (useful for future charts)."""
    data = _load()
    return sorted(data["count_by_day"].items(), reverse=True)[:days]


def reset(confirm=False):
    """
    Clear the counter. Only useful during development.

    Usage: reset(confirm=True)
    """
    if not confirm:
        log.warning("reset() requires confirm=True")
        return False
    _save({"count_by_month": {}, "count_by_day": {}, "last_call_at": None})
    log.info("CMC usage counter reset")
    return True
