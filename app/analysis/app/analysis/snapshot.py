"""
Snapshots + diff to detect material changes.

Gives the "analyst" memory: it saves the current state, compares it
with the previous one, and reports only the changes that exceed the
thresholds defined in config.
"""

from datetime import datetime, timezone

from app.config import (
    HISTORY_FILE,
    THRESHOLD_PRICE_PCT,
    THRESHOLD_TACTICAL_PCT,
    THRESHOLD_ACCUM_PCT,
    THRESHOLD_RR_DELTA,
    MAX_HISTORY_ITEMS,
)
from app.logger import get_logger

log = get_logger(__name__)


# ============================================================
#  JSON persistence
# ============================================================
def _load_json(path, default=None):
    """Load JSON from disk. Returns default on failure."""
    if default is None:
        default = []
    try:
        if not path.exists():
            return default
        import json
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.warning(f"Could not load {path.name}: {e}")
        return default


def _save_json(path, data):
    """Save JSON atomically (tmp → rename)."""
    try:
        import json, shutil
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        shutil.move(str(tmp), str(path))
    except Exception as e:
        log.warning(f"Could not save {path.name}: {e}")


# ============================================================
#  Snapshot
# ============================================================
def build_snapshot(price, tactical, accumulation, momentum, vol):
    """
    Package the current analysis into a flat dict for comparison.
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "price": price,
        "tactical": {
            "low": tactical["optimal_low"],
            "high": tactical["optimal_high"],
            "mid": tactical["optimal_mid"],
            "sl": tactical["stop_loss"],
            "tp": tactical["take_profit"],
            "rr": tactical["rr_ratio"],
            "members": sorted(tactical["members"]),
        } if tactical else None,
        "accumulation": {
            "low": accumulation["optimal_low"],
            "high": accumulation["optimal_high"],
            "mid": accumulation["optimal_mid"],
            "sl": accumulation["stop_loss"],
            "tp": accumulation["take_profit"],
            "rr": accumulation["rr_ratio"],
            "members": sorted(accumulation["zone_members"]),
        } if accumulation and accumulation.get("confidence_count", 0) > 0 else None,
        "momentum": {
            "pattern": momentum["pattern"],
            "label": momentum["label"],
            "short_avg": momentum["short_avg"],
            "medium_avg": momentum["medium_avg"],
            "long_avg": momentum["long_avg"],
        } if momentum else None,
        "volume": {
            "level": vol["vol_level"] if vol else "—",
            "obv": vol["obv_signal"] if vol else "—",
            "ratio_7d": vol["vol_ratio_7d"] if vol else 1,
        } if vol else None,
    }


# ============================================================
#  Diff with thresholds
# ============================================================
def detect_material_changes(old, new):
    """
    Compare two snapshots and return a list of strings describing
    the changes that exceed the thresholds.
    """
    changes = []

    if old is None:
        return ["First snapshot saved"]

    # ── Price ──
    try:
        delta_price = (new["price"] / old["price"] - 1) * 100
        if abs(delta_price) > THRESHOLD_PRICE_PCT:
            changes.append(
                f"Price {delta_price:+.1f}% "
                f"({old['price']:,.0f} → {new['price']:,.0f})"
            )
    except Exception:
        pass

    # ── Tactical zone ──
    ot, nt = old.get("tactical"), new.get("tactical")
    if ot and nt:
        delta = (nt["mid"] / ot["mid"] - 1) * 100
        if abs(delta) > THRESHOLD_TACTICAL_PCT:
            changes.append(
                f"Tactical zone {delta:+.2f}% ({ot['mid']:,.0f} → {nt['mid']:,.0f})"
            )
        old_m, new_m = set(ot["members"]), set(nt["members"])
        if old_m != new_m:
            added = new_m - old_m
            removed = old_m - new_m
            if added:
                changes.append(f"Tactical + {', '.join(sorted(added))}")
            if removed:
                changes.append(f"Tactical − {', '.join(sorted(removed))}")
        if abs(nt["rr"] - ot["rr"]) > THRESHOLD_RR_DELTA:
            changes.append(f"Tactical R:R 1:{ot['rr']:.1f} → 1:{nt['rr']:.1f}")
    elif ot and not nt:
        changes.append("Tactical zone disappeared")
    elif not ot and nt:
        changes.append("Tactical zone appeared")

    # ── Accumulation zone ──
    oa, na = old.get("accumulation"), new.get("accumulation")
    if oa and na:
        delta = (na["mid"] / oa["mid"] - 1) * 100
        if abs(delta) > THRESHOLD_ACCUM_PCT:
            changes.append(
                f"Accumulation zone {delta:+.2f}% ({oa['mid']:,.0f} → {na['mid']:,.0f})"
            )
        old_m, new_m = set(oa["members"]), set(na["members"])
        if old_m != new_m:
            added = new_m - old_m
            removed = old_m - new_m
            if added:
                changes.append(f"Accumulation + {', '.join(sorted(added))}")
            if removed:
                changes.append(f"Accumulation − {', '.join(sorted(removed))}")
        if abs(na["rr"] - oa["rr"]) > THRESHOLD_RR_DELTA:
            changes.append(f"Accumulation R:R 1:{oa['rr']:.1f} → 1:{na['rr']:.1f}")
    elif oa and not na:
        changes.append("Accumulation zone disappeared")
    elif not oa and na:
        changes.append("Accumulation zone appeared")

    # ── Momentum ──
    om, nm = old.get("momentum"), new.get("momentum")
    if om and nm:
        if om["pattern"] != nm["pattern"]:
            changes.append(f"Momentum {om['pattern']} → {nm['pattern']}: {nm['label']}")

    # ── Volume ──
    ov, nv = old.get("volume"), new.get("volume")
    if ov and nv:
        if ov["obv"] != nv["obv"]:
            changes.append(f"OBV: {ov['obv']} → {nv['obv']}")
        if ov["level"] != nv["level"]:
            changes.append(f"Volume: {ov['level']} → {nv['level']}")

    return changes


# ============================================================
#  History
# ============================================================
def save_snapshot(snapshot):
    """Append the snapshot to the history. Keeps only the last N."""
    history = _load_json(HISTORY_FILE, [])
    history.append(snapshot)
    if len(history) > MAX_HISTORY_ITEMS:
        history = history[-MAX_HISTORY_ITEMS:]
    _save_json(HISTORY_FILE, history)


def get_last_snapshot():
    """Return the last saved snapshot, or None."""
    history = _load_json(HISTORY_FILE, [])
    return history[-1] if history else None


def get_history(limit=None):
    """Return the full history (or the last N items)."""
    history = _load_json(HISTORY_FILE, [])
    if limit:
        return history[-limit:]
    return history


def process_snapshot(snapshot):
    """
    Main entry point.

    Saves the snapshot, computes the diff with the previous one,
    and returns the material changes detected.
    """
    last = get_last_snapshot()
    changes = detect_material_changes(last, snapshot)
    save_snapshot(snapshot)
    return changes
