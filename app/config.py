"""
Central configuration.

Loads environment variables from .env (if python-dotenv is available)
and exposes all constants used by the rest of the application.
"""

import os
from pathlib import Path


# ============================================================
#  Base paths
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    # Without dotenv, only system environment variables are read
    pass

# State directories
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Persistent files
HISTORY_FILE = DATA_DIR / "analysis_history.json"
DECISIONS_FILE = DATA_DIR / "decisions.json"
LOG_FILE = LOGS_DIR / "eth_terminal.log"


# ============================================================
#  External APIs
# ============================================================
CMC_BASE = "https://pro-api.coinmarketcap.com"
CMC_API_KEY = os.getenv("CMC_API_KEY", "")

# Monthly credits available on the CMC Basic free tier
CMC_CREDITS_MONTHLY = 10000

# File where the local credit counter is persisted
CMC_USAGE_FILE = DATA_DIR / "cmc_usage.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


# ============================================================
#  Exchange
# ============================================================
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "coinex")
SYMBOL = os.getenv("SYMBOL", "ETH/USDT")


# ============================================================
#  Scheduler
# ============================================================
# Enable/disable the background decision check
SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "true").lower() in ("true", "1", "yes")

# Seconds between checks
# 600s = 10 min → 4,320 CMC credits/month
SCHEDULER_INTERVAL_SECONDS = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "600"))


# ============================================================
#  Analysis thresholds
# ============================================================
# If the optimal zone is more than this % away from the current price,
# it is flagged as "far" (blue style, no urgency)
ZONE_FAR_THRESHOLD_PCT = 8.0

# If the take profit is within this % of the current price, warn
# that the R:R is theoretical (requires a full up-and-down cycle)
TP_NEAR_PRICE_PCT = 5.0


# ============================================================
#  Material change thresholds (for snapshot diffs)
# ============================================================
THRESHOLD_PRICE_PCT = 2.0       # minimum price change to report
THRESHOLD_TACTICAL_PCT = 1.0    # minimum tactical zone shift to report
THRESHOLD_ACCUM_PCT = 2.0       # minimum accumulation zone shift to report
THRESHOLD_RR_DELTA = 0.5        # minimum R:R change to report

# Maximum number of snapshots kept in analysis_history.json
MAX_HISTORY_ITEMS = 100


# ============================================================
#  Logging
# ============================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
