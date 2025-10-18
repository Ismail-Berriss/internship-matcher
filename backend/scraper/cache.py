# backend/scraper/cache.py
import time
from typing import List, Dict, Optional

_CACHE = {}
_CACHE_TIMEOUT = 7200  # 2 hours (seconds)


def _make_cache_key(field: str, location: str = "") -> str:
    """Create a consistent, hashable cache key from a single field and an optional location."""
    # Construct the key string, e.g., "Data Engineering|Paris" or "Machine Learning"
    key_parts = [field]
    if location:
        key_parts.append(location)
    return "|".join(key_parts)


def get_cached_jobs(field: str, location: str = "") -> Optional[List[Dict]]:
    key = _make_cache_key(field, location)  # Use the updated key function
    if key in _CACHE:
        data, timestamp = _CACHE[key]
        if time.time() - timestamp < _CACHE_TIMEOUT:
            return data
    return None


def set_cached_jobs(field: str, jobs: List[Dict], location: str = ""):
    key = _make_cache_key(field, location)  # Use the updated key function
    _CACHE[key] = (jobs, time.time())
