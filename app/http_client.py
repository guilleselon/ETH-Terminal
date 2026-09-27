"""
Unified HTTP client.

Uses `requests` if available; otherwise falls back to `urllib` from the
standard library. Never raises exceptions to the caller: returns None
and logs the error, letting the upper layer decide what to do.
"""

from app.logger import get_logger

log = get_logger(__name__)

# Check if requests is available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Fallback using urllib
import urllib.request
import urllib.parse
import json as _json


def http_get_json(url, params=None, headers=None, timeout=10):
    """
    Perform a GET request and return the parsed JSON, or None on failure.

    Args:
        url:     Base URL (without query string)
        params:  Dict of query parameters (optional)
        headers: Dict of extra headers (optional)
        timeout: Seconds before aborting the request

    Returns:
        dict/list  → parsed JSON
        None       → on any error
    """
    h = {"User-Agent": "Mozilla/5.0"}
    if headers:
        h.update(headers)

    # ── Attempt 1: requests ──
    if HAS_REQUESTS:
        try:
            r = requests.get(url, params=params, headers=h, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            log.debug(f"requests failed at {url}: {type(e).__name__}: {e}")
            # Fall through to urllib

    # ── Attempt 2: urllib ──
    try:
        full_url = url
        if params:
            full_url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(full_url, headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return _json.loads(r.read().decode("utf-8"))
    except Exception as e:
        log.warning(f"HTTP GET failed at {url}: {type(e).__name__}: {e}")
        return None


def http_post_json(url, payload, headers=None, timeout=5):
    """
    Perform a POST request with a JSON body.

    Returns:
        dict  → parsed response
        None  → on failure
    """
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)

    # ── Attempt 1: requests ──
    if HAS_REQUESTS:
        try:
            r = requests.post(url, json=payload, headers=h, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            log.debug(f"POST {url} returned HTTP {r.status_code}: {r.text[:200]}")
            return None
        except Exception as e:
            log.debug(f"requests POST failed at {url}: {type(e).__name__}: {e}")
            # Fall through to urllib

    # ── Attempt 2: urllib ──
    try:
        data = _json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return _json.loads(r.read().decode("utf-8"))
    except Exception as e:
        log.warning(f"HTTP POST failed at {url}: {type(e).__name__}: {e}")
        return None
