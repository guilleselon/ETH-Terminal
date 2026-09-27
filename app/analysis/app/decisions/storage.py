"""
Decision persistence to disk (JSON).

Atomic write (tmp → rename) + threading.Lock to prevent the web
thread and the scheduler thread from writing at the same time.
"""

import json
import shutil
import threading

from app.config import DECISIONS_FILE
from app.logger import get_logger

log = get_logger(__name__)

# Reentrant lock: can be acquired multiple times by the same thread
_lock = threading.RLock()


def load_decisions():
    """Load the list of decisions from decisions.json."""
    with _lock:
        try:
            if not DECISIONS_FILE.exists():
                return []
            with open(DECISIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception as e:
            log.warning(f"Could not load {DECISIONS_FILE.name}: {e}")
            return []


def save_decisions(decisions):
    """Save the list of decisions (atomic write)."""
    with _lock:
        try:
            tmp = DECISIONS_FILE.with_suffix(DECISIONS_FILE.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(decisions, f, indent=2, ensure_ascii=False)
            shutil.move(str(tmp), str(DECISIONS_FILE))
        except Exception as e:
            log.warning(f"Could not save {DECISIONS_FILE.name}: {e}")


def get_active_decisions():
    """Return only decisions in waiting or in_zone status."""
    return [d for d in load_decisions()
            if d.get("status") in ("waiting", "in_zone")]


def get_closed_decisions(limit=None):
    """Return closed decisions (tp_hit/sl_hit), most recent first."""
    closed = [d for d in load_decisions()
              if d.get("status") in ("tp_hit", "sl_hit", "expired")]
    closed.sort(key=lambda d: d.get("last_checked", ""), reverse=True)
    return closed[:limit] if limit else closed
